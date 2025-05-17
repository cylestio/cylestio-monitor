"""
Security schema definitions.

This module defines schema attributes and event types for security monitoring.
"""

# Security-related attributes
SECURITY_ATTRIBUTES = {
    "security.category": {
        "description": "The security category of the event",
        "type": "string",
        "example": "remote_code_execution"
    },
    "security.severity": {
        "description": "The severity level of the security event",
        "type": "string",
        "example": "high"
    },
    "security.direct_shell": {
        "description": "Whether the process is directly using a shell (high risk)",
        "type": "boolean",
        "example": True
    },
    "security.risk": {
        "description": "The specific security risk identified",
        "type": "string",
        "example": "command_injection"
    },
    "security.description": {
        "description": "Detailed description of the security event",
        "type": "string",
        "example": "Detected attempt to transition from database context to shell execution"
    }
}

# Alert attributes for security events
ALERT_ATTRIBUTES = {
    "alert.type": {
        "description": "The type of security alert",
        "type": "string",
        "example": "Suspicious Shell Command Pattern Detected"
    },
    "alert.severity": {
        "description": "The severity level of the alert (critical, high, medium, low)",
        "type": "string",
        "example": "critical"
    },
    "alert.evidence": {
        "description": "Evidence supporting the alert",
        "type": "string",
        "example": "Query contains pattern that may enable command execution or context switching"
    }
}

# Security categories related to process execution
PROCESS_SECURITY_CATEGORIES = [
    "process_execution",
    "command_injection",
    "remote_code_execution",
    "privilege_escalation"
]

# Security categories related to network connections
NETWORK_SECURITY_CATEGORIES = [
    "outbound_connection",
    "direct_ip",
    "potential_c2",
    "potential_data_exfiltration",
    "network_connection",
    "shell_access_detected",
    "network_shell_traffic"
]

# Combined security categories
SECURITY_CATEGORIES = PROCESS_SECURITY_CATEGORIES + NETWORK_SECURITY_CATEGORIES

# Security risk types
SECURITY_RISK_TYPES = [
    # Process security risks
    "command_injection",
    "potential_rce",
    "mcp_shell_transition",
    "context_switching_attempt",
    "unusual_execution_directory",
    "privilege_escalation",
    # Network security risks
    "potential_c2",
    "potential_data_exfiltration",
    "network_shell_access",
    "interactive_shell_detected"
]

# Security alert schema
SECURITY_ALERT_SCHEMA = {
    "security.alert": {
        "description": "Security alert for suspicious activity",
        "required_attributes": ["alert.type", "alert.severity", "session.id"],
        "optional_attributes": [
            "alert.evidence", "security.risk", "security.description",
            # Process attributes
            "proc.path", "proc.args", "proc.calling_context",
            # Network attributes
            "net.transport", "net.dst.ip", "net.dst.port", "net.traffic.direction"
        ],
        "example": {
            "alert.type": "Context Switching Attempt Detected",
            "alert.severity": "critical",
            "alert.evidence": "Query contains pattern that may enable command execution or context switching",
            "security.risk": "mcp_shell_transition",
            "security.category": "remote_code_execution",
            "security.description": "Detected attempt to transition from database query to shell execution",
            "proc.path": "/bin/bash",
            "proc.args": "cat /etc/passwd | grep root",
            "proc.calling_context": "sqlite_handler.py:45:execute_query|database.py:102:run_sql",
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    }
}
