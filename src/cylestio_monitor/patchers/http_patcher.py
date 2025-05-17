"""
HTTP client monitoring patcher for Cylestio Monitor.

This module patches popular HTTP client libraries (httpx, requests) to detect
shell access patterns and potential RCE attacks in HTTP request/response payloads.
"""

import logging
import json
import re
import os
import time
from typing import Dict, List, Any, Callable, Optional, Union, Tuple, Set
import functools
import threading
import subprocess

from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.event_context import get_session_id
from cylestio_monitor.utils.security_patterns import get_shell_access_network_patterns

logger = logging.getLogger(__name__)

# Keep track of patching status
_http_patched = False

# Thread-local storage for tracking HTTP requests in progress
_HTTP_CONTEXT = threading.local()

# Keep a global registry of detected shell processes
_SHELL_PROCESSES = {}
_shell_processes_lock = threading.RLock()

# Common shell executable paths
SHELL_EXECUTABLES = {
    "/bin/sh", "/bin/bash", "/bin/zsh", "/bin/dash",
    "cmd.exe", "powershell.exe", "pwsh.exe"
}

# Dangerous commands that are strong indicators of RCE when seen in HTTP traffic
DANGEROUS_HTTP_PATTERNS = [
    # Reverse shell patterns
    r"bash -i >& /dev/tcp/",
    r"python -c ['\"](import socket|import pty.*pty\.spawn)",
    r"perl -e 'use Socket;",
    r"rm -f /tmp/f;mkfifo /tmp/f",
    r"nc -e /bin/sh",
    # Encoded command execution
    r"base64 -d.*\|.*sh",
    r"eval\(atob\(",
    r"echo.*\|.*base64 -d.*\|.*sh",
    # Process execution with evasion
    r"IFS=.;.*\$\{IFS\}",
    r"\$\{IEX\}",
    r"String\.fromCharCode\(.*\).+eval",
    # System command execution
    r"system\(['\"]/bin/",
    r"exec\(['\"]/",
    r"subprocess\.(?:Popen|call|run)\s*\(['\"]"
]

# Suspicious SQL patterns that might be attempting to trigger RCE
# Note: Avoiding hardcoding specific patterns from the example attack, keeping it generic
SUSPICIOUS_SQL_PATTERNS = [
    # SQL injection attempts - only severe ones that might enable RCE
    r";\s*EXEC\s*", 
    r";\s*EXECUTE\s*",
    r";\s*SYSTEM\s*",
    r";\s*SHELL\s*",
    r"--\s*.*SELECT.*INTO\s*OUTFILE",
    r"UNION\s*SELECT.*INTO\s*OUTFILE",
    
    # Command extraction patterns - specifically look for command injection syntax
    r"WHERE\s+\w+\s*=\s*['\"].*[|;&`].*['\"]",  # Typical command injection with special chars
    
    # Mode switching attempts (explicit RCE enablement)
    r"ENABLE.*SHELL",
    r"SWITCH.*MODE.*SHELL",
    r"SET.*MODE.*UNSAFE",
    
    # Direct shell execution patterns in SQL - high confidence indicators
    r"WHERE\s+\w+\s*=\s*['\"].*(\/bin\/sh|\/bin\/bash|cmd\.exe|powershell\.exe).*['\"]"
]

# MCP-specific patterns for extracting commands from SQL queries
# More selective to reduce false positives 
MCP_COMMAND_EXTRACTION_PATTERNS = [
    # Only match WHERE clauses with potential command patterns
    r"WHERE\s+\w+\s*=\s*['\"](\/bin\/.*?|cmd\.exe.*?|powershell\.exe.*?)['\"]",  # Path-based commands
    r"WHERE\s+\w+\s*=\s*['\"](enable\-shell|unsafe\-exec|system\-access)['\"]",   # Context switching keywords
    r"WHERE\s+mode\s*=\s*['\"](shell|exec|command|unsafe)['\"]"                   # Mode change to shell
]


def _register_shell_process(pid: int, parent_pid: int, executable: str, timestamp: float) -> None:
    """
    Register a detected shell process.

    Args:
        pid: Process ID of the shell
        parent_pid: Parent process ID
        executable: Path to the shell executable
        timestamp: Time when the process was detected
    """
    logger.debug(f"Registering shell process PID={pid}, parent={parent_pid}, executable={executable}")

    with _shell_processes_lock:
        _SHELL_PROCESSES[pid] = {
            "parent_pid": parent_pid,
            "executable": executable,
            "timestamp": timestamp,
            "http_correlated": False,
            "http_requests": []
        }
    logger.debug(f"Shell processes registry now contains {len(_SHELL_PROCESSES)} entries")


def _get_recent_shell_processes(time_window: float = 5.0) -> List[Dict[str, Any]]:
    """
    Get shell processes detected within the specified time window.

    Args:
        time_window: Time window in seconds to look for shell processes

    Returns:
        List of shell process information dictionaries
    """
    current_time = time.time()
    recent_shells = []

    with _shell_processes_lock:
        for pid, info in _SHELL_PROCESSES.items():
            if current_time - info["timestamp"] <= time_window:
                recent_shells.append({"pid": pid, **info})

    return recent_shells


def _analyze_content_for_dangerous_commands(content: Union[str, bytes]) -> List[str]:
    """
    Analyze HTTP content for high-confidence dangerous commands.

    Args:
        content: The content to analyze (string or bytes)

    Returns:
        List of matched dangerous patterns
    """
    # Skip if content is empty
    if not content:
        return []

    # Convert content to string if it's bytes
    if isinstance(content, bytes):
        try:
            text_content = content.decode('utf-8', errors='replace')
        except Exception:
            # If we can't decode, use string representation
            text_content = str(content)
    else:
        text_content = str(content)

    # Match against dangerous patterns
    matches = []
    for pattern in DANGEROUS_HTTP_PATTERNS:
        if re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE):
            matches.append(pattern)

    return matches


def _analyze_content_for_suspicious_sql(content: Union[str, bytes]) -> List[str]:
    """
    Analyze HTTP content for suspicious SQL patterns that might indicate SQL-to-shell transitions.
    Enhanced with better context awareness to reduce false positives for legitimate MCP operations.
    
    Args:
        content: The content to analyze (string or bytes)
        
    Returns:
        List of matched suspicious SQL patterns
    """
    # Skip if content is empty
    if not content:
        return []
    
    # Convert content to string if it's bytes
    if isinstance(content, bytes):
        try:
            text_content = content.decode('utf-8', errors='replace')
        except Exception:
            # If we can't decode, use string representation
            text_content = str(content)
    else:
        text_content = str(content)
    
    # Extract SQL queries from JSON if possible
    sql_queries = []
    
    # Try to find SQL queries in JSON
    try:
        data = json.loads(text_content)
        # Common patterns for SQL queries in JSON
        if isinstance(data, dict):
            # Check for query parameter
            if "query" in data and isinstance(data["query"], str):
                sql_queries.append(data["query"])
            
            # Check for messages array with content
            if "messages" in data and isinstance(data["messages"], list):
                for msg in data["messages"]:
                    if isinstance(msg, dict) and "content" in msg and isinstance(msg["content"], str):
                        content = msg["content"]
                        # Only add if it looks like SQL
                        if ("SELECT" in content and "FROM" in content) or "WHERE" in content:
                            sql_queries.append(content)
            
            # Check for nested parameters
            if "params" in data and isinstance(data["params"], dict):
                if "arguments" in data["params"] and isinstance(data["params"]["arguments"], dict):
                    if "query" in data["params"]["arguments"] and isinstance(data["params"]["arguments"]["query"], str):
                        sql_queries.append(data["params"]["arguments"]["query"])
    except:
        # If not JSON, just use the text as is
        if ("SELECT" in text_content and "FROM" in text_content) or "WHERE" in text_content:
            sql_queries.append(text_content)
    
    # If we couldn't extract any SQL queries, just use the original text
    if not sql_queries:
        sql_queries.append(text_content)
    
    # Match against suspicious SQL patterns
    matches = []
    for sql in sql_queries:
        for pattern in SUSPICIOUS_SQL_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE | re.MULTILINE):
                # Double-check for false positives on common legitimate patterns
                if "WHERE" in pattern and "=" in pattern:
                    # Skip common legitimate WHERE clause patterns
                    if re.search(r"WHERE\s+(id|name|type|value|key)\s*=\s*['\"][^;|&`]+['\"]", sql, re.IGNORECASE):
                        continue
                
                matches.append(pattern)
    
    return matches


def _extract_commands_from_sql(sql: str) -> List[str]:
    """
    Extract potential shell commands from SQL queries based on MCP patterns.
    More selective to reduce false positives for legitimate SQLite MCP operations.
    
    Args:
        sql: SQL query string
        
    Returns:
        List of potential shell commands
    """
    commands = []
    
    # Log the SQL being analyzed for debugging purposes
    logger.debug(f"Analyzing SQL for command extraction: {sql[:100]}...")
    
    # First check if this is likely an attack attempt before detailed analysis
    # This helps reduce false positives for legitimate SQLite queries
    is_suspicious = False
    
    # High confidence attack indicators
    high_risk_indicators = [
        "enable-shell", "shell mode", "exec(", "system(", "unsafe", 
        "/bin/sh", "/bin/bash", "cmd.exe", "powershell.exe", 
        "|", ";", "`", "$("
    ]
    
    # Check for high-risk indicators first
    for indicator in high_risk_indicators:
        if indicator in sql.lower():
            is_suspicious = True
            logger.debug(f"High-risk SQL indicator found: {indicator}")
            break
    
    # Skip command extraction for non-suspicious SQL
    if not is_suspicious:
        return []
    
    # If suspicious, proceed with command extraction
    for pattern in MCP_COMMAND_EXTRACTION_PATTERNS:
        matches = re.finditer(pattern, sql, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) > 0:
                command = match.group(1).strip()
                
                # Enhanced shell command detection - be more selective
                shell_commands = [
                    "ls", "cd", "pwd", "cat", "echo", "whoami", "id", "ps", "netstat", 
                    "curl", "wget", "chmod", "mkdir", "rm", "cp", "mv"
                ]
                
                # Skip this command if it's a common identifier in legitimate SQL
                common_legitimate_values = ["id", "name", "type", "path", "value", "data", "key", "state"]
                if command.lower() in common_legitimate_values and len(command) < 10:
                    continue
                
                # Check if the command starts with any known shell command
                is_shell_command = False
                
                # Only match commands with multiple components (args) or path-like structures
                if any(cmd == command.split()[0] for cmd in shell_commands) and (
                    " -" in command or  # Has command-line arguments
                    "/" in command or   # Has path separator (Unix)
                    "\\" in command or  # Has path separator (Windows)
                    len(command.split()) > 1  # Has multiple parts
                ):
                    is_shell_command = True
                
                # Also check for explicit paths or command options
                elif ('/' in command or '\\' in command) and any(
                    cmd in command for cmd in ["bin", "usr", "etc", "sbin", "cmd.exe", "powershell"]
                ):
                    is_shell_command = True
                
                if is_shell_command:
                    logger.debug(f"Extracted potential shell command from SQL: {command}")
                    commands.append(command)
    
    return commands


def _register_virtual_shell_execution(command: str, url: str, method: str) -> None:
    """
    Register a 'virtual' shell execution for commands detected in SQL queries.
    This simulates a shell process execution for MCP-based RCE where we don't directly
    observe the shell process being spawned.
    
    Args:
        command: Shell command detected
        url: URL associated with the request
        method: HTTP method used
    """
    # Skip common legitimate values that might be mistaken for commands
    command_lower = command.lower()
    common_legitimate_values = ["id", "name", "type", "path", "value", "data", "key", "state", 
                               "file", "user", "status", "mode", "size", "date"]
    
    # Skip registration for common legitimate values
    if command_lower in common_legitimate_values and len(command) < 15:
        logger.debug(f"Skipping virtual shell registration for likely legitimate value: {command}")
        return
    
    # Determine severity based on command content
    severity = "medium"
    
    # Upgrade severity for clear attack indicators
    high_risk_indicators = [
        "enable-shell", "bash", "/bin/", "cmd.exe", "powershell", "wget", "curl",
        "nc ", "netcat", "|", ";", "`", "unsafe", "&", "system(", "exec("
    ]
    
    for indicator in high_risk_indicators:
        if indicator in command_lower:
            severity = "critical"
            break
    
    # Create a pseudo-PID for this virtual shell process
    # Use negative numbers to distinguish from real processes
    pseudo_pid = -int(time.time() * 1000) % 100000
    shell_path = "/bin/sh" if os.name == "posix" else "cmd.exe"
    
    _register_shell_process(pseudo_pid, os.getpid(), shell_path, time.time())
    
    # Generate an alert with appropriate severity
    alert_attributes = {
        "alert.type": "MCP Shell Command Execution in SQL Query",
        "alert.severity": severity,
        "alert.evidence": f"SQL query containing shell command '{command}' was executed via HTTP {method} to {url}",
        "security.risk": "remote_code_execution",
        "security.category": "remote_code_execution",
        "security.severity": severity, 
        "security.description": f"Shell command executed via SQL query in HTTP request - SQL-to-shell transition detected",
        "proc.command": command,
        "proc.virtual_shell": "true",
        "net.protocol": "http",
        "http.url": url,
        "http.method": method,
        "session.id": get_session_id()
    }
    
    log_event(
        name="security.alert",
        attributes=alert_attributes,
        level="CRITICAL" if severity == "critical" else "WARNING"
    )


def _log_shell_process_alert(shell_info: Dict[str, Any], http_context: Dict[str, Any]):
    """
    Log a security alert for shell process execution correlated with HTTP traffic.

    Args:
        shell_info: Information about the detected shell process
        http_context: Information about the related HTTP request
    """
    # Mark this shell as correlated with HTTP
    with _shell_processes_lock:
        if shell_info["pid"] in _SHELL_PROCESSES:
            _SHELL_PROCESSES[shell_info["pid"]]["http_correlated"] = True
            _SHELL_PROCESSES[shell_info["pid"]]["http_requests"].append(http_context)

    # Generate alert
    alert_attributes = {
        "alert.type": "Shell Process Execution via HTTP",
        "alert.severity": "critical",
        "alert.evidence": f"Shell process {shell_info['executable']} (PID: {shell_info['pid']}) executed after HTTP request to {http_context.get('url')}",
        "security.risk": "remote_code_execution",
        "security.category": "remote_code_execution",
        "security.severity": "critical",
        "security.description": f"Shell execution detected shortly after HTTP request - potential RCE attack",
        "proc.pid": shell_info["pid"],
        "proc.parent_pid": shell_info["parent_pid"],
        "proc.path": shell_info["executable"],
        "net.protocol": "http",
        "http.url": http_context.get("url", "unknown"),
        "http.method": http_context.get("method", "unknown"),
        "session.id": get_session_id()
    }

    log_event(
        name="security.alert",
        attributes=alert_attributes,
        level="CRITICAL"
    )


def _log_dangerous_command_alert(matches: List[str], url: str, method: str, direction: str):
    """
    Log a security alert for dangerous command patterns detected in HTTP traffic.

    Args:
        matches: List of matched dangerous patterns
        url: The URL associated with this content
        method: The HTTP method used
        direction: Either 'request' or 'response'
    """
    if not matches:
        return

    alert_attributes = {
        "alert.type": "Dangerous Command Pattern in HTTP Traffic",
        "alert.severity": "high",
        "alert.evidence": f"HTTP {direction} to {url} contains dangerous command patterns: {', '.join(matches)}",
        "security.risk": "remote_code_execution",
        "security.category": "remote_code_execution",
        "security.severity": "high",
        "security.description": f"HTTP {direction} contains dangerous command patterns indicating potential RCE attempt",
        "net.protocol": "http",
        "http.url": url,
        "http.method": method,
        "http.direction": direction,
        "session.id": get_session_id()
    }

    log_event(
        name="security.alert",
        attributes=alert_attributes,
        level="WARNING"
    )


def _log_suspicious_sql_alert(matches: List[str], url: str, method: str, direction: str):
    """
    Log a security alert for suspicious SQL patterns that might indicate SQL-to-shell transitions.

    Args:
        matches: List of matched suspicious SQL patterns
        url: The URL associated with this content
        method: The HTTP method used
        direction: Either 'request' or 'response'
    """
    if not matches:
        return

    alert_attributes = {
        "alert.type": "Suspicious SQL Pattern in HTTP Traffic",
        "alert.severity": "medium",
        "alert.evidence": f"HTTP {direction} to {url} contains suspicious SQL patterns: {', '.join(matches)}",
        "security.risk": "potential_rce",
        "security.category": "remote_code_execution",
        "security.severity": "medium",
        "security.description": f"HTTP {direction} contains suspicious SQL patterns that might indicate SQL-to-shell transition",
        "net.protocol": "http",
        "http.url": url,
        "http.method": method,
        "http.direction": direction,
        "session.id": get_session_id()
    }

    log_event(
        name="security.alert",
        attributes=alert_attributes,
        level="WARNING"
    )


def _register_http_request(url: str, method: str) -> Dict[str, Any]:
    """
    Register a new HTTP request and set up for shell process correlation.

    Args:
        url: The request URL
        method: The HTTP method

    Returns:
        HTTP context information
    """
    context = {
        "url": url,
        "method": method,
        "timestamp": time.time()
    }

    # Store in thread-local for reference
    if not hasattr(_HTTP_CONTEXT, 'requests'):
        _HTTP_CONTEXT.requests = []

    _HTTP_CONTEXT.requests.append(context)

    # Keep only the last 20 requests to avoid memory issues
    if len(_HTTP_CONTEXT.requests) > 20:
        _HTTP_CONTEXT.requests = _HTTP_CONTEXT.requests[-20:]

    return context


def _check_for_shell_process_correlation(http_context: Dict[str, Any]) -> None:
    """
    Check if any recently spawned shell processes might be connected to this HTTP request.

    Args:
        http_context: Information about the HTTP request
    """
    # Get recent shell processes (last 15 seconds - increased from 5 seconds)
    recent_shells = _get_recent_shell_processes(time_window=15.0)

    # Debug logging to help diagnose HTTP-to-shell correlation issues
    logger.debug(f"HTTP correlation check for {http_context.get('url')}: found {len(recent_shells)} recent shell processes")

    for shell in recent_shells:
        # If the shell was spawned after the HTTP request (within 15 seconds)
        if (shell["timestamp"] >= http_context["timestamp"] and
            shell["timestamp"] <= http_context["timestamp"] + 15.0):

            # Log additional debug information
            logger.debug(f"HTTP-to-shell correlation found: HTTP request at {http_context.get('timestamp')} to {http_context.get('url')} correlated with shell PID {shell.get('pid')} at {shell.get('timestamp')}")

            # Log alert for potential RCE
            _log_shell_process_alert(shell, http_context)


def _analyze_sql_for_mcp_rce(content: Union[str, bytes], url: str, method: str) -> None:
    """
    Analyze HTTP content for SQL queries that might be used for MCP-based RCE.

    Args:
        content: The content to analyze
        url: The URL associated with this content
        method: The HTTP method used
    """
    # Skip if content is empty
    if not content:
        return

    # Convert content to string if it's bytes
    if isinstance(content, bytes):
        try:
            text_content = content.decode('utf-8', errors='replace')
        except Exception:
            # If we can't decode, use string representation
            text_content = str(content)
    else:
        text_content = str(content)

    # Try to extract SQL queries from JSON
    sql_queries = []

    try:
        # Parse JSON content
        data = json.loads(text_content)

        # Look for MCP-style query parameter
        if isinstance(data, dict):
            if 'query' in data and isinstance(data['query'], str):
                sql_queries.append(data['query'])

            # Check for nested parameters (common MCP format)
            if 'params' in data and isinstance(data['params'], dict):
                params = data['params']
                if 'arguments' in params and isinstance(params['arguments'], dict):
                    arguments = params['arguments']
                    if 'query' in arguments and isinstance(arguments['query'], str):
                        sql_queries.append(arguments['query'])

            # Check LLM message format
            if 'messages' in data and isinstance(data['messages'], list):
                for msg in data['messages']:
                    if isinstance(msg, dict) and 'content' in msg:
                        content = msg['content']
                        if isinstance(content, str) and ('SELECT' in content and 'FROM' in content):
                            sql_queries.append(content)
    except:
        # If not valid JSON, check if the content itself looks like a SQL query
        if isinstance(text_content, str) and ('SELECT' in text_content and 'FROM' in text_content):
            sql_queries.append(text_content)

    # For each SQL query, check for potential shell commands
    for sql in sql_queries:
        commands = _extract_commands_from_sql(sql)
        for command in commands:
            if command:
                # Register this as a virtual shell execution
                _register_virtual_shell_execution(command, url, method)


def _patch_httpx():
    """Patch the httpx library for monitoring."""
    try:
        import httpx
        original_send = httpx.Client.send

        @functools.wraps(original_send)
        def wrapped_send(self, request, *args, **kwargs):
            # Get request details
            url = str(request.url)
            method = request.method

            # Register this HTTP request for shell correlation
            http_context = _register_http_request(url, method)

            # Check for dangerous command patterns in request content
            if request.content:
                command_matches = _analyze_content_for_dangerous_commands(request.content)
                if command_matches:
                    _log_dangerous_command_alert(command_matches, url, method, "request")

                # Also check for suspicious SQL patterns
                sql_matches = _analyze_content_for_suspicious_sql(request.content)
                if sql_matches:
                    _log_suspicious_sql_alert(sql_matches, url, method, "request")

                # Check for MCP-based RCE in SQL queries
                _analyze_sql_for_mcp_rce(request.content, url, method)

            # Call original method
            response = original_send(self, request, *args, **kwargs)

            # Check for dangerous command patterns in response
            if response.content:
                command_matches = _analyze_content_for_dangerous_commands(response.content)
                if command_matches:
                    _log_dangerous_command_alert(command_matches, url, method, "response")

                # Also check for suspicious SQL patterns in response
                sql_matches = _analyze_content_for_suspicious_sql(response.content)
                if sql_matches:
                    _log_suspicious_sql_alert(sql_matches, url, method, "response")

                # Check for MCP-based RCE in SQL query responses
                _analyze_sql_for_mcp_rce(response.content, url, method)

            # After response received, check for shell processes that might have been spawned
            _check_for_shell_process_correlation(http_context)

            return response

        # Apply the patch
        httpx.Client.send = wrapped_send
        logger.info("Patched httpx library for HTTP monitoring")

        # Also patch AsyncClient if available
        if hasattr(httpx, 'AsyncClient'):
            original_async_send = httpx.AsyncClient.send

            async def wrapped_async_send(self, request, *args, **kwargs):
                # Get request details
                url = str(request.url)
                method = request.method

                # Register this HTTP request for shell correlation
                http_context = _register_http_request(url, method)

                # Check for dangerous command patterns in request content
                if request.content:
                    command_matches = _analyze_content_for_dangerous_commands(request.content)
                    if command_matches:
                        _log_dangerous_command_alert(command_matches, url, method, "request")

                    # Also check for suspicious SQL patterns
                    sql_matches = _analyze_content_for_suspicious_sql(request.content)
                    if sql_matches:
                        _log_suspicious_sql_alert(sql_matches, url, method, "request")

                    # Check for MCP-based RCE in SQL queries
                    _analyze_sql_for_mcp_rce(request.content, url, method)

                # Call original method
                response = await original_async_send(self, request, *args, **kwargs)

                # Check for dangerous command patterns in response
                if hasattr(response, 'content'):
                    try:
                        response_content = await response.aread()
                        command_matches = _analyze_content_for_dangerous_commands(response_content)
                        if command_matches:
                            _log_dangerous_command_alert(command_matches, url, method, "response")

                        # Also check for suspicious SQL patterns in response
                        sql_matches = _analyze_content_for_suspicious_sql(response_content)
                        if sql_matches:
                            _log_suspicious_sql_alert(sql_matches, url, method, "response")

                        # Check for MCP-based RCE in SQL query responses
                        _analyze_sql_for_mcp_rce(response_content, url, method)
                    except Exception as e:
                        logger.debug(f"Error analyzing async response: {e}")

                # After response received, check for shell processes that might have been spawned
                _check_for_shell_process_correlation(http_context)

                return response

            httpx.AsyncClient.send = wrapped_async_send
            logger.info("Patched httpx AsyncClient for HTTP monitoring")

        return True
    except ImportError:
        logger.info("httpx library not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"Error patching httpx: {e}")
        return False


def _patch_requests():
    """Patch the requests library for monitoring."""
    try:
        import requests
        from requests.models import Response

        # Patch the send method of Session
        original_send = requests.Session.send

        @functools.wraps(original_send)
        def wrapped_send(self, request, **kwargs):
            # Get request details
            url = request.url
            method = request.method

            # Register this HTTP request for shell correlation
            http_context = _register_http_request(url, method)

            # Check for dangerous command patterns in request body
            if request.body:
                command_matches = _analyze_content_for_dangerous_commands(request.body)
                if command_matches:
                    _log_dangerous_command_alert(command_matches, url, method, "request")

                # Also check for suspicious SQL patterns
                sql_matches = _analyze_content_for_suspicious_sql(request.body)
                if sql_matches:
                    _log_suspicious_sql_alert(sql_matches, url, method, "request")

                # Check for MCP-based RCE in SQL queries
                _analyze_sql_for_mcp_rce(request.body, url, method)

            # Call original method
            response = original_send(self, request, **kwargs)

            # Check for dangerous command patterns in response
            if response.content:
                command_matches = _analyze_content_for_dangerous_commands(response.content)
                if command_matches:
                    _log_dangerous_command_alert(command_matches, url, method, "response")

                # Also check for suspicious SQL patterns in response
                sql_matches = _analyze_content_for_suspicious_sql(response.content)
                if sql_matches:
                    _log_suspicious_sql_alert(sql_matches, url, method, "response")

                # Check for MCP-based RCE in SQL query responses
                _analyze_sql_for_mcp_rce(response.content, url, method)

            # After response received, check for shell processes that might have been spawned
            _check_for_shell_process_correlation(http_context)

            return response

        # Apply the patch
        requests.Session.send = wrapped_send
        logger.info("Patched requests library for HTTP monitoring")

        return True
    except ImportError:
        logger.info("requests library not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"Error patching requests: {e}")
        return False


def register_shell_process_execution(pid: int, parent_pid: int, executable: str) -> None:
    """
    Register a shell process execution for HTTP correlation.
    This function is called from the process_patcher when a shell process is detected.

    Args:
        pid: Process ID of the shell
        parent_pid: Parent process ID
        executable: Path to the shell executable
    """
    if any(shell in executable.lower() for shell in ["sh", "bash", "zsh", "cmd", "powershell"]):
        _register_shell_process(pid, parent_pid, executable, time.time())
        logger.debug(f"Registered shell process: {executable} (PID: {pid})")


def patch_http_monitoring() -> bool:
    """
    Apply HTTP client library monitoring patches.

    Returns:
        bool: True if at least one client was patched successfully
    """
    global _http_patched

    if _http_patched:
        logger.info("HTTP monitoring already enabled")
        return True

    success = False

    # Patch httpx library
    httpx_success = _patch_httpx()
    success = success or httpx_success

    # Patch requests library
    requests_success = _patch_requests()
    success = success or requests_success

    if success:
        _http_patched = True
        logger.info("HTTP monitoring enabled")
    else:
        logger.warning("Failed to patch any HTTP client libraries")

    return success


def unpatch_http_monitoring() -> bool:
    """
    Remove HTTP client monitoring patches.

    Returns:
        bool: True if successful, False otherwise
    """
    global _http_patched

    if not _http_patched:
        return True

    try:
        # Restore original methods for httpx
        try:
            import httpx
            import importlib
            importlib.reload(httpx)
            logger.info("Unpatched httpx library")
        except ImportError:
            pass

        # Restore original methods for requests
        try:
            import requests
            import importlib
            importlib.reload(requests)
            logger.info("Unpatched requests library")
        except ImportError:
            pass

        _http_patched = False
        logger.info("HTTP monitoring unpatched")
        return True
    except Exception as e:
        logger.error(f"Failed to unpatch HTTP monitoring: {e}")
        return False
