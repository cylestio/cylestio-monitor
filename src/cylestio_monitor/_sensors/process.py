"""
Process execution monitoring sensor.

This module provides monitoring of subprocess and os.system calls to detect
potential remote code execution (RCE) attempts.
"""

import os
import pwd
import shlex
import subprocess
import sys
import traceback
import time
from typing import Any, Dict, List, Optional, Union, Callable

from cylestio_monitor.utils.event_context import get_session_id
from cylestio_monitor.utils.event_logging import log_event, log_error

# Import our detection rules
try:
    from cylestio_monitor._sensors.process_detection import analyze_process, check_sql_command_injection
except ImportError:
    # Define a fallback if the detection module isn't available
    def analyze_process(process_data: Dict) -> List[Dict]:
        return []
    def check_sql_command_injection(query: str) -> Optional[Dict]:
        return None

# Store original functions before monkey patching
_orig_popen = subprocess.Popen
_orig_system = os.system

# Toggle for enabling/disabling RCE detection
ENABLE_RCE_DETECTION = True

# Shell process callback function (used to integrate with HTTP monitoring)
_shell_process_callback = None

def register_shell_callback(callback: Callable[[int, int, str], None]) -> None:
    """
    Register a callback function to be called when a shell process is executed.
    Used to integrate with HTTP-based RCE detection.

    Args:
        callback: Function to call with shell process information (pid, parent_pid, executable)
    """
    global _shell_process_callback
    _shell_process_callback = callback


def unregister_shell_callback() -> None:
    """
    Unregister the shell process callback.
    """
    global _shell_process_callback
    _shell_process_callback = None


def _get_process_metadata():
    """
    Get detailed process metadata to help identify potential RCE attacks.

    Returns:
        dict: Process metadata including user, privileges, and execution context
    """
    metadata = {}

    # Add user and privilege information (defensive coding for all platforms)
    try:
        metadata["proc.user"] = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        if hasattr(os, "getuid"):
            metadata["proc.uid"] = os.getuid()
            metadata["proc.euid"] = os.geteuid()
            metadata["proc.gid"] = os.getgid()
            metadata["proc.egid"] = os.getegid()
            metadata["proc.is_privileged"] = (metadata["proc.euid"] == 0)

            # On Unix-like systems, try to get the username associated with the UID
            try:
                metadata["proc.username"] = pwd.getpwuid(metadata["proc.uid"]).pw_name
            except (KeyError, ImportError):
                # Fall back to environment variable if pwd lookup fails
                metadata["proc.username"] = metadata["proc.user"]
    except (AttributeError, OSError):
        # Non-Unix platforms may not have these functions
        pass

    # Process context (should work cross-platform)
    try:
        metadata["proc.cwd"] = os.getcwd()
        metadata["proc.parent_pid"] = os.getppid() if hasattr(os, "getppid") else None
    except (AttributeError, OSError):
        pass

    # Execution context
    metadata["proc.command_path"] = sys.argv[0] if len(sys.argv) > 0 else "unknown"
    metadata["proc.platform"] = sys.platform

    # Process tree context - capture stack trace to get calling context
    try:
        stack = traceback.extract_stack()
        # Skip the last few frames which are just our monitoring code
        stack = stack[:-3] if len(stack) > 3 else stack
        if stack:
            # Include the last 3 frames from the calling code as calling context
            context_frames = stack[-3:] if len(stack) >= 3 else stack
            caller_info = []
            for frame in context_frames:
                # Frame format: (filename, line number, function name, text)
                caller_info.append(f"{os.path.basename(frame[0])}:{frame[1]}:{frame[2]}")
            metadata["proc.calling_context"] = "|".join(caller_info)
    except Exception:
        # Don't let stack capturing issues break monitoring
        pass

    return metadata


def _check_if_shell_process(exec_path: str, args: List[str]) -> bool:
    """
    Check if a process is a shell process that should be reported to HTTP monitoring.

    Args:
        exec_path: Path to the executable
        args: Process arguments

    Returns:
        bool: True if this is a shell process
    """
    # Common shell executable paths
    shell_executables = [
        "/bin/sh", "/bin/bash", "/bin/zsh", "/bin/dash",
        "cmd.exe", "powershell.exe", "pwsh.exe"
    ]

    # Check if this is a shell executable
    if any(shell in exec_path.lower() for shell in ["sh", "bash", "zsh", "cmd", "powershell", "pwsh"]):
        return True

    # Check if the path ends with any of the shell executables
    for shell in shell_executables:
        if exec_path.lower().endswith(shell):
            return True

    return False


def _process_alerts(alerts: List[Dict], process_data: Dict) -> None:
    """
    Process and log any security alerts generated by detection rules.

    Args:
        alerts: List of alert dictionaries from detection rules
        process_data: Original process execution data
    """
    for alert in alerts:
        # Get the severity for this alert
        severity = alert.get("severity", "high")

        # Create a new security alert event with combined information
        alert_data = {
            "alert.type": alert.get("alert", "Suspicious Process Execution"),
            "alert.severity": severity,
            "alert.evidence": alert.get("evidence", "See process details"),
            "security.risk": alert.get("risk", "potential_rce"),
            "security.category": "process_execution",
            "security.severity": severity,
            "security.description": alert.get("description", "Suspicious process execution detected"),

            # Include minimal process context for the alert
            "proc.path": process_data.get("proc.path", ""),
            "proc.args": process_data.get("proc.args", ""),
            "proc.cwd": process_data.get("proc.cwd", ""),
            "proc.calling_context": process_data.get("proc.calling_context", ""),
            "session.id": process_data.get("session.id", "")
        }

        # Map severity to appropriate log level
        # Only use CRITICAL for critical severity, all others use WARNING
        log_level = "WARNING"
        if severity.lower() == "critical":
            log_level = "CRITICAL"

        # Log an explicit security alert
        log_event(
            name="security.alert",
            level=log_level,
            attributes=alert_data
        )


def _span_popen(args, **kwargs):
    """
    Monkey-patched version of subprocess.Popen that records process execution spans.

    Records a span for every process execution while preserving all original functionality.
    """
    # Extract command information
    cmd_str = ""
    cmd_args: List[str] = []
    shell = kwargs.get("shell", False)

    if isinstance(args, str):
        cmd_str = args
        if not shell:
            # If not using shell but passed string, it's a single command
            cmd_args = [args]
        else:
            # With shell=True, attempt to parse arguments for telemetry
            try:
                cmd_args = shlex.split(args)
            except:
                cmd_args = [args]
    else:
        # Handle list/tuple of arguments
        cmd_args = list(args)
        cmd_str = " ".join(str(arg) for arg in cmd_args)

    # Determine the executable path
    exec_path = cmd_args[0] if cmd_args else ""

    # Get process metadata
    proc_metadata = _get_process_metadata()

    # Capture environment variables (safely)
    env_vars = kwargs.get("env", os.environ)
    if env_vars:
        # Only include specific environment variables that might indicate unusual behavior
        # but avoid capturing potentially sensitive values
        env_keys = set(env_vars.keys())
        interesting_prefixes = ('PATH', 'PYTHON', 'LD_', 'DYLD_', 'HOME', 'TEMP', 'TMP')
        interesting_env = {
            f"proc.env.{k}": "PRESENT"
            for k in env_keys
            if any(k.startswith(prefix) for prefix in interesting_prefixes)
        }
        proc_metadata.update(interesting_env)

    # Add indicators for shell usage
    proc_metadata["proc.shell_used"] = shell
    if shell:
        proc_metadata["proc.shell_args"] = cmd_str

    # Capture stdin/stdout/stderr redirections as these are common in attacks
    for stream_name, stream_option in [('stdin', 'stdin'), ('stdout', 'stdout'), ('stderr', 'stderr')]:
        if stream_name in kwargs:
            stream_value = kwargs[stream_name]
            if stream_value == subprocess.PIPE:
                proc_metadata[f"proc.{stream_option}"] = "PIPE"
            elif stream_value == subprocess.DEVNULL:
                proc_metadata[f"proc.{stream_option}"] = "DEVNULL"

    # Determine security risk severity based on the command
    severity = "medium"

    # Shell execution is higher risk
    if shell:
        severity = "high"

    # Build complete process data
    process_data = {
        "proc.path": exec_path,
        "proc.args": cmd_str,
        "proc.shell": shell,
        "proc.parent_id": os.getpid(),
        "session.id": get_session_id(),

        # Add process user and privilege information
        **proc_metadata,

        # Add security assessment with severity based on the process
        "security.category": "process_execution",
        "security.severity": severity,
    }

    # Log the process execution event
    log_event(
        "process.exec",
        level="WARNING",
        attributes=process_data
    )

    # Run detection rules if enabled
    if ENABLE_RCE_DETECTION:
        try:
            alerts = analyze_process(process_data)
            if alerts:
                _process_alerts(alerts, process_data)
        except Exception as e:
            # Don't let detection errors affect process execution
            log_error(f"Error in RCE detection: {str(e)}")

    # Execute the process with original functionality
    try:
        result = _orig_popen(args, **kwargs)
        # Add additional telemetry if process was created successfully
        if result.pid:
            # Check if this is a shell process, and if so, report it to HTTP monitoring
            if _check_if_shell_process(exec_path, cmd_args) and _shell_process_callback:
                try:
                    _shell_process_callback(result.pid, os.getpid(), exec_path)
                except Exception as e:
                    # Don't let callback errors affect process execution
                    log_error(f"Error in shell process callback: {str(e)}")

            log_event(
                "process.started",
                level="INFO",
                attributes={
                    "proc.child_id": result.pid,
                    "proc.path": exec_path,
                    "proc.args": cmd_str,
                    "session.id": get_session_id(),
                    "proc.cwd": kwargs.get("cwd", proc_metadata.get("proc.cwd", "")),
                    "proc.user": proc_metadata.get("proc.user", "unknown"),
                    "proc.calling_context": proc_metadata.get("proc.calling_context", ""),
                }
            )
        return result
    except Exception as e:
        # Log the exception but let it propagate
        log_event(
            "process.exec.error",
            level="ERROR",
            attributes={
                "error.type": type(e).__name__,
                "error.message": str(e),
                "proc.path": exec_path,
                "proc.args": cmd_str,
                "session.id": get_session_id(),
                "proc.cwd": kwargs.get("cwd", proc_metadata.get("proc.cwd", "")),
                "proc.user": proc_metadata.get("proc.user", "unknown"),
                "proc.calling_context": proc_metadata.get("proc.calling_context", ""),
            }
        )
        raise


def _span_system(cmd):
    """
    Monkey-patched version of os.system that records process execution.
    """
    shell = "/bin/sh" if os.name == "posix" else "cmd.exe"

    # Get process metadata
    proc_metadata = _get_process_metadata()

    # Build complete process data
    process_data = {
        "proc.path": shell,
        "proc.args": cmd,
        "proc.shell": True,
        "proc.parent_id": os.getpid(),
        "session.id": get_session_id(),

        # Add process user and privilege information
        **proc_metadata,

        # Add security assessment - os.system is always shell use
        "security.category": "process_execution",
        "security.severity": "high",
        "security.direct_shell": True,
    }

    # Log the system call event
    log_event(
        "process.exec",
        level="WARNING",
        attributes=process_data
    )

    # Run detection rules if enabled
    if ENABLE_RCE_DETECTION:
        try:
            alerts = analyze_process(process_data)
            if alerts:
                _process_alerts(alerts, process_data)
        except Exception as e:
            # Don't let detection errors affect process execution
            log_error(f"Error in RCE detection: {str(e)}")

    # Execute the command with original functionality
    try:
        # Register this as a shell process for HTTP correlation
        # We don't have the actual PID, but we can use a timestamp-based approximation
        if _shell_process_callback:
            try:
                # Use negative PID to indicate it's an estimated shell process from os.system
                pseudo_pid = -int(time.time() * 1000) % 100000  # Use timestamp-based unique negative ID
                _shell_process_callback(pseudo_pid, os.getpid(), shell)
            except Exception as e:
                # Don't let callback errors affect process execution
                log_error(f"Error in shell process callback: {str(e)}")

        result = _orig_system(cmd)
        return result
    except Exception as e:
        # Log the exception but let it propagate
        log_event(
            "process.exec.error",
            level="ERROR",
            attributes={
                "error.type": type(e).__name__,
                "error.message": str(e),
                "proc.path": shell,
                "proc.args": cmd,
                "session.id": get_session_id(),
                "proc.user": proc_metadata.get("proc.user", "unknown"),
                "proc.calling_context": proc_metadata.get("proc.calling_context", ""),
            }
        )
        raise


def analyze_sql_query(query: str, context: Dict = None) -> None:
    """
    Analyze SQL queries for potential command injection patterns.
    Handles both SQL injection and remote code execution attempts.

    Args:
        query: The SQL query string to analyze
        context: Additional context for the query
    """
    if not ENABLE_RCE_DETECTION or not query:
        return

    try:
        # Check for command injection patterns in the SQL query
        alert = check_sql_command_injection(query)
        if alert:
            # Determine the appropriate category based on the alert
            category = alert.get("category", "sql_command_injection")
            severity = alert.get("severity", "high")

            # Build alert context
            alert_context = {
                "security.category": category,
                "security.severity": severity,
                "security.description": alert.get("description", "Detected suspicious SQL query pattern"),
                "session.id": get_session_id(),
                "sql.query": query
            }

            # Add any additional context
            if context:
                alert_context.update(context)

            # Log the security alert
            alert_data = {
                "alert.type": alert.get("alert", "Suspicious SQL Query Detected"),
                "alert.severity": severity,
                "alert.evidence": alert.get("evidence", "Query contains suspicious pattern"),
                "security.risk": alert.get("risk", category),
                **alert_context
            }

            # Map severity to appropriate log level
            # Only use CRITICAL for critical severity, all others use WARNING
            log_level = "WARNING"
            if severity.lower() == "critical":
                log_level = "CRITICAL"

            log_event(
                name="security.alert",
                level=log_level,
                attributes=alert_data
            )
    except Exception as e:
        # This is a true system error
        log_error(f"Error in SQL query analysis: {str(e)}")


def enable_rce_detection(enabled: bool = True) -> None:
    """
    Enable or disable RCE detection.

    Args:
        enabled: Whether RCE detection should be enabled
    """
    global ENABLE_RCE_DETECTION
    ENABLE_RCE_DETECTION = enabled


def initialize():
    """Initialize the process monitoring sensor."""
    # Apply monkey patches
    subprocess.Popen = _span_popen
    os.system = _span_system
