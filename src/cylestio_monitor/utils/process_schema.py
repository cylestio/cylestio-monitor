"""
Process execution schema definitions.

This module defines schema attributes and event types for process execution monitoring.
"""

from cylestio_monitor.security_detection import (
    SECURITY_ATTRIBUTES,
    ALERT_ATTRIBUTES,
    PROCESS_SECURITY_CATEGORIES,
    SECURITY_RISK_TYPES
)

# Process execution attributes
PROCESS_ATTRIBUTES = {
    "proc.path": {
        "description": "The path to the executed process",
        "type": "string",
        "example": "/bin/bash"
    },
    "proc.args": {
        "description": "The command line arguments passed to the process",
        "type": "string",
        "example": "-c 'ls -la'"
    },
    "proc.shell": {
        "description": "Whether the process was executed through a shell",
        "type": "boolean",
        "example": True
    },
    "proc.shell_used": {
        "description": "Whether a shell was used for this process execution",
        "type": "boolean",
        "example": True
    },
    "proc.shell_args": {
        "description": "The arguments passed to the shell",
        "type": "string",
        "example": "-c 'cat /etc/passwd'"
    },
    "proc.parent_id": {
        "description": "The process ID of the parent that spawned this process",
        "type": "int",
        "example": 12345
    },
    "proc.child_id": {
        "description": "The process ID of the spawned child process",
        "type": "int",
        "example": 12346
    },
    "proc.user": {
        "description": "The user who executed the process",
        "type": "string",
        "example": "johndoe"
    },
    "proc.username": {
        "description": "The username associated with the user ID",
        "type": "string",
        "example": "johndoe"
    },
    "proc.uid": {
        "description": "The real user ID of the process",
        "type": "int",
        "example": 1000
    },
    "proc.euid": {
        "description": "The effective user ID of the process (important for privilege escalation)",
        "type": "int",
        "example": 0
    },
    "proc.gid": {
        "description": "The real group ID of the process",
        "type": "int",
        "example": 1000
    },
    "proc.egid": {
        "description": "The effective group ID of the process",
        "type": "int",
        "example": 1000
    },
    "proc.is_privileged": {
        "description": "Whether the process has elevated privileges (e.g., root/admin)",
        "type": "boolean",
        "example": False
    },
    "proc.cwd": {
        "description": "The current working directory where the process was executed",
        "type": "string",
        "example": "/home/user/projects"
    },
    "proc.env_modified": {
        "description": "Whether the process environment variables were modified from parent",
        "type": "boolean",
        "example": True
    },
    "proc.parent_pid": {
        "description": "The parent process ID (different from process.parent_id which is the monitoring agent's PID)",
        "type": "int",
        "example": 12340
    },
    "proc.command_path": {
        "description": "The command path of the parent process",
        "type": "string",
        "example": "/usr/bin/python3"
    },
    "proc.platform": {
        "description": "The platform on which the process is running",
        "type": "string",
        "example": "linux"
    },
    "proc.calling_context": {
        "description": "Stack trace information showing which code initiated the process",
        "type": "string",
        "example": "main.py:45:handle_request|server.py:102:execute_command"
    },
    "proc.stdin": {
        "description": "Configuration of standard input for the process",
        "type": "string",
        "example": "PIPE"
    },
    "proc.stdout": {
        "description": "Configuration of standard output for the process",
        "type": "string",
        "example": "PIPE"
    },
    "proc.stderr": {
        "description": "Configuration of standard error for the process",
        "type": "string",
        "example": "STDOUT"
    }
}

# Process execution event schema
PROCESS_SPAN_SCHEMA = {
    "process.exec": {
        "description": "Process execution event",
        "required_attributes": ["proc.path", "proc.args", "proc.parent_id", "session.id"],
        "optional_attributes": ["proc.shell", "proc.child_id", "proc.cwd", "proc.user", "proc.euid",
                               "proc.uid", "proc.is_privileged", "proc.calling_context", "proc.shell_args"],
        "example": {
            "proc.path": "/bin/sh",
            "proc.args": "-c 'cat /etc/passwd'",
            "proc.shell": True,
            "proc.parent_id": 12345,
            "proc.child_id": 12346,
            "proc.user": "johndoe",
            "proc.uid": 1000,
            "proc.euid": 1000,
            "proc.is_privileged": False,
            "proc.cwd": "/home/johndoe",
            "proc.calling_context": "app.py:102:process_request",
            "security.category": "process_execution",
            "security.severity": "high",
            "security.direct_shell": True,
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    },
    "process.started": {
        "description": "Process started successfully",
        "required_attributes": ["proc.child_id", "proc.path", "session.id"],
        "optional_attributes": ["proc.args", "proc.user", "proc.is_privileged", "proc.cwd", "proc.calling_context"],
        "example": {
            "proc.child_id": 12346,
            "proc.path": "/bin/ls",
            "proc.args": "-la /tmp",
            "proc.user": "johndoe",
            "proc.is_privileged": False,
            "proc.cwd": "/home/johndoe",
            "proc.calling_context": "app.py:102:process_request",
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    },
    "process.exec.error": {
        "description": "Error during process execution",
        "required_attributes": ["error.type", "error.message", "proc.path", "session.id"],
        "optional_attributes": ["proc.args", "proc.user", "proc.cwd", "proc.calling_context"],
        "example": {
            "error.type": "FileNotFoundError",
            "error.message": "No such file or directory: '/bin/nonexistent'",
            "proc.path": "/bin/nonexistent",
            "proc.args": "-c 'echo test'",
            "proc.user": "johndoe",
            "proc.cwd": "/home/johndoe",
            "proc.calling_context": "app.py:102:process_request",
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    }
}
