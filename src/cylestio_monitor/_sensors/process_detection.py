"""
Process execution detection rules for RCE attacks.

This module provides real-time detection rules for identifying potential
Remote Code Execution (RCE) attacks based on process execution patterns.
"""

import os
import re
from typing import Dict, List, Optional, Tuple

from cylestio_monitor.utils.security_patterns import (
    get_suspicious_shell_patterns,
    get_dangerous_commands,
    get_suspicious_directories,
    get_privilege_escalation_commands,
    get_context_switching_patterns,
    get_sql_injection_patterns
)

# Track process execution patterns for context-aware detection
_recent_processes = []
_MAX_RECENT_PROCESSES = 50
_process_callers = {}  # Maps process paths to their callers


def track_process(process_data: Dict) -> None:
    """
    Track process execution for pattern detection.

    Args:
        process_data: Process execution data
    """
    global _recent_processes

    # Add to recent processes list
    _recent_processes.append(process_data)

    # Trim list if needed
    if len(_recent_processes) > _MAX_RECENT_PROCESSES:
        _recent_processes = _recent_processes[-_MAX_RECENT_PROCESSES:]

    # Track process callers for caller transition detection
    proc_path = process_data.get("proc.path", "")
    caller_context = process_data.get("proc.calling_context", "")

    if proc_path and caller_context:
        if proc_path not in _process_callers:
            _process_callers[proc_path] = set()
        _process_callers[proc_path].add(caller_context)


def check_suspicious_shell_usage(process_data: Dict) -> Optional[Dict]:
    """
    Detect suspicious shell usage patterns like command injection.

    Args:
        process_data: Process execution data

    Returns:
        Dict with alert information if suspicious, None otherwise
    """
    # Check if this is a shell execution
    proc_path = process_data.get("proc.path", "")
    proc_args = process_data.get("proc.args", "")
    is_shell = process_data.get("proc.shell", False) or "shell_used" in process_data

    shell_paths = ["/bin/sh", "/bin/bash", "/bin/zsh", "cmd.exe", "powershell.exe", "pwsh.exe"]
    is_shell_binary = any(shell in proc_path.lower() for shell in shell_paths)

    if not (is_shell or is_shell_binary):
        return None

    # Check for command injection patterns
    suspicious_patterns = get_suspicious_shell_patterns()

    matches = []
    for pattern in suspicious_patterns:
        if re.search(pattern, proc_args, re.IGNORECASE):
            matches.append(pattern)

    if matches:
        return {
            "alert": "Suspicious Shell Command Pattern Detected",
            "severity": "critical",
            "evidence": f"Command contains suspicious patterns: {', '.join(matches)}",
            "risk": "command_injection",
            "proc.path": proc_path,
            "proc.args": proc_args
        }

    # Check for dangerous commands
    dangerous_commands = get_dangerous_commands()
    dangerous_matches = []

    for cmd in dangerous_commands:
        if cmd in proc_args.lower():
            dangerous_matches.append(cmd)

    if dangerous_matches:
        return {
            "alert": "Dangerous Command Execution Detected",
            "severity": "high",
            "evidence": f"Command contains dangerous operations: {', '.join(dangerous_matches)}",
            "risk": "dangerous_command",
            "proc.path": proc_path,
            "proc.args": proc_args
        }

    return None


def check_context_transition(process_data: Dict) -> Optional[Dict]:
    """
    Detect suspicious transitions between code contexts that could indicate RCE.

    Args:
        process_data: Process execution data

    Returns:
        Dict with alert information if suspicious, None otherwise
    """
    proc_path = process_data.get("proc.path", "")
    caller_context = process_data.get("proc.calling_context", "")

    # Not enough context to make determination
    if not proc_path or not caller_context:
        return None

    # Check if this process was previously called from a different context
    if proc_path in _process_callers and caller_context not in _process_callers[proc_path]:
        # Known shell executables are suspicious when called from new contexts
        shell_bins = ["/bin/sh", "/bin/bash", "/bin/zsh", "cmd.exe", "powershell.exe"]
        if any(shell in proc_path.lower() for shell in shell_bins):
            db_indicators = ["sql", "sqlite", "database", "query", "db"]

            # Check if any previous context was database-related
            caller_contexts = list(_process_callers[proc_path])
            db_related_contexts = [ctx for ctx in caller_contexts if any(db in ctx.lower() for db in db_indicators)]

            # If we've seen this shell executed from DB context, this could be MCP → shell transition
            if db_related_contexts:
                return {
                    "alert": "Database-to-Shell Execution Context Transition",
                    "severity": "critical",
                    "evidence": f"Shell previously executed from {db_related_contexts[0]}, now from {caller_context}",
                    "risk": "mcp_shell_transition",
                    "proc.path": proc_path
                }

    # Always track new callers
    track_process(process_data)
    return None


def check_unusual_directory(process_data: Dict) -> Optional[Dict]:
    """
    Detect process execution from unusual directories.

    Args:
        process_data: Process execution data

    Returns:
        Dict with alert information if suspicious, None otherwise
    """
    # Check working directory
    cwd = process_data.get("proc.cwd", "")
    if not cwd:
        return None

    suspicious_dirs = get_suspicious_directories()

    is_suspicious = any(d in cwd.lower() for d in suspicious_dirs)

    if is_suspicious:
        return {
            "alert": "Process Executed From Suspicious Directory",
            "severity": "high",
            "evidence": f"Process working directory {cwd} is commonly used in attacks",
            "risk": "unusual_execution_directory",
            "proc.cwd": cwd
        }

    return None


def check_privilege_escalation(process_data: Dict) -> Optional[Dict]:
    """
    Detect potential privilege escalation attempts.

    Args:
        process_data: Process execution data

    Returns:
        Dict with alert information if suspicious, None otherwise
    """
    proc_args = process_data.get("proc.args", "").lower()
    is_privileged = process_data.get("proc.is_privileged", False)
    euid = process_data.get("proc.euid", None)

    # Check for commands used in privilege escalation
    priv_escalation_cmds = get_privilege_escalation_commands()
    has_priv_cmd = any(cmd in proc_args for cmd in priv_escalation_cmds)

    # Check for direct privilege gain (uid 0 = root)
    privilege_gained = is_privileged or (euid is not None and euid == 0)

    if has_priv_cmd or privilege_gained:
        return {
            "alert": "Potential Privilege Escalation Detected",
            "severity": "critical",
            "evidence": f"Process contains privilege escalation commands or is running as privileged user",
            "risk": "privilege_escalation",
            "proc.args": proc_args,
            "proc.is_privileged": is_privileged
        }

    return None


def check_sql_command_injection(query: str) -> Optional[Dict]:
    """
    Detect potential command injection in SQL queries or context switching attempts.
    Distinguishes between remote code execution and traditional SQL injection.

    Args:
        query: SQL query string

    Returns:
        Dict with alert information if suspicious, None otherwise
    """
    if not query:
        return None

    # First, check for traditional SQL injection patterns
    sql_injection_patterns = get_sql_injection_patterns()

    # Check for regular SQL injection patterns (DROP, DELETE, UNION SELECT, etc.)
    for pattern in sql_injection_patterns:
        if re.search(pattern, query):
            # Skip shell execution patterns here - they're handled separately
            if "EXEC" in pattern or "SYSTEM" in pattern or "SHELL" in pattern.upper():
                continue

            # This is regular SQL injection
            if "DROP" in pattern or "DELETE" in pattern or "UNION" in pattern:
                return {
                    "alert": "SQL Injection Attempt",
                    "severity": "high",
                    "evidence": f"SQL query contains injection pattern",
                    "risk": "sql_command_injection",
                    "description": "Detected attempt to manipulate database structure or data through SQL injection",
                    "query": query
                }

    # Check for context switching patterns in extracted parameters
    context_switch_patterns = get_context_switching_patterns()

    # Extract potential command from WHERE name = '...' or similar patterns
    name_pattern = re.search(r"WHERE\s+\w+\s*=\s*['\"](.*?)['\"]", query, re.IGNORECASE)
    if name_pattern:
        cmd = name_pattern.group(1).strip()

        # Check for context switching patterns in the extracted value
        for pattern in context_switch_patterns:
            if re.search(pattern, cmd):
                return {
                    "alert": "Context Switching Attempt Detected in SQL Query",
                    "severity": "critical",
                    "evidence": f"Query contains pattern that may enable command execution or context switching",
                    "risk": "mcp_shell_transition",
                    "description": "Detected attempt to transition from database query to shell execution",
                    "query": query,
                    "category": "remote_code_execution"
                }

    # Check for direct SQL to shell transition patterns in the whole query
    for pattern in sql_injection_patterns:
        if re.search(pattern, query):
            if "EXEC" in pattern or "SYSTEM" in pattern or "SHELL" in pattern.upper():
                return {
                    "alert": "SQL to Shell Execution Attempt",
                    "severity": "critical",
                    "evidence": f"SQL query contains direct command execution syntax",
                    "risk": "remote_code_execution",
                    "description": "Detected attempt to execute system commands through SQL",
                    "query": query,
                    "category": "remote_code_execution"
                }

    # Check for shell commands in the extracted name
    if name_pattern:
        cmd = name_pattern.group(1).strip()
        dangerous_commands = get_dangerous_commands()

        command_matches = []

        for dangerous_cmd in dangerous_commands:
            if dangerous_cmd == cmd or dangerous_cmd == cmd.split()[0]:
                command_matches.append(dangerous_cmd)

        if command_matches:
            return {
                "alert": "Shell Command in SQL Query",
                "severity": "high",
                "evidence": f"SQL query contains shell command: {cmd}",
                "risk": "remote_code_execution",
                "description": "SQL query parameter contains a known dangerous system command",
                "query": query,
                "command": cmd,
                "category": "remote_code_execution"
            }

        # Check for common Unix commands
        common_commands = ["ls", "pwd", "cat", "cd", "rm", "echo", "find", "grep", "ps", "netstat", "whoami"]
        if cmd in common_commands:
            return {
                "alert": "Potential Command Injection in SQL Query",
                "severity": "medium",
                "evidence": f"SQL query contains Unix command: {cmd}",
                "risk": "remote_code_execution",
                "description": "SQL query parameter contains a common system command",
                "query": query,
                "command": cmd,
                "category": "remote_code_execution"
            }

    return None


def is_system_utility_process(process_data: Dict) -> bool:
    """
    Determine if a process is a common system utility that may be less suspicious.

    Args:
        process_data: Process execution data

    Returns:
        True if process is a common system utility, False otherwise
    """
    proc_path = process_data.get("proc.path", "")
    proc_args = process_data.get("proc.args", "")

    # System utilities often used by Python and other applications
    system_utilities = [
        "uname", "file", "which", "whereis", "hostname",
        "stat", "readlink", "wc", "date", "arch", "lsb_release"
    ]

    # Check if the process is a system utility
    if proc_path and any(util == os.path.basename(proc_path) for util in system_utilities):
        return True

    return False


def is_known_python_subprocess(process_data: Dict) -> bool:
    """
    Determine if a process is a known Python module-related subprocess.

    Args:
        process_data: Process execution data

    Returns:
        True if process is a known Python-related subprocess, False otherwise
    """
    calling_context = process_data.get("proc.calling_context", "")

    # Known Python module contexts that commonly spawn processes
    python_modules = [
        "platform.py", "subprocess.py", "multiprocessing",
        "distutils", "shutil.py", "pip", "venv",
        "os.py", "site.py", "importlib"
    ]

    # Check if the calling context matches any known Python modules
    if any(module in calling_context for module in python_modules):
        return True

    return False


def analyze_process(process_data: Dict) -> List[Dict]:
    """
    Analyze process execution data for signs of RCE.

    Args:
        process_data: Process execution data

    Returns:
        List of alerts if suspicious patterns detected
    """
    alerts = []

    # First, adjust severity based on context
    if is_system_utility_process(process_data) and is_known_python_subprocess(process_data):
        # Lower severity for known Python-related system utility processes
        process_data["security.severity"] = "info"

    # Run all detection rules
    shell_alert = check_suspicious_shell_usage(process_data)
    if shell_alert:
        alerts.append(shell_alert)

    context_alert = check_context_transition(process_data)
    if context_alert:
        alerts.append(context_alert)

    directory_alert = check_unusual_directory(process_data)
    if directory_alert:
        alerts.append(directory_alert)

    privilege_alert = check_privilege_escalation(process_data)
    if privilege_alert:
        alerts.append(privilege_alert)

    return alerts
