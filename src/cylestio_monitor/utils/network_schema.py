"""
Network connection schema definitions.

This module defines schema attributes and event types for network connection monitoring.
"""

from cylestio_monitor.security_detection import (
    SECURITY_ATTRIBUTES,
    ALERT_ATTRIBUTES
)

# Network connection attributes
NETWORK_ATTRIBUTES = {
    "net.transport": {
        "description": "Transport protocol used for the network connection",
        "type": "string",
        "example": "tcp"
    },
    "net.dst.ip": {
        "description": "Destination IP address or hostname",
        "type": "string",
        "example": "93.184.216.34"
    },
    "net.dst.port": {
        "description": "Destination port number",
        "type": "int",
        "example": 443
    },
    "net.is_local": {
        "description": "Whether the connection is to localhost",
        "type": "boolean",
        "example": False
    },
    "net.conn.result": {
        "description": "Result code from the connection attempt",
        "type": "int",
        "example": 0
    },
    "net.conn.error": {
        "description": "Error message if the connection failed",
        "type": "string",
        "example": "Connection refused"
    }
}

# Network security categories
NETWORK_SECURITY_CATEGORIES = [
    "outbound_connection",
    "direct_ip",
    "potential_c2",
    "potential_data_exfiltration",
    "network_connection"
]

# Network security risk types
NETWORK_SECURITY_RISK_TYPES = [
    "potential_c2",
    "potential_data_exfiltration"
]

# Network connection event schema
NETWORK_SPAN_SCHEMA = {
    "net.conn_open": {
        "description": "Network connection event",
        "required_attributes": ["net.transport", "net.dst.ip", "net.dst.port", "session.id"],
        "optional_attributes": ["net.is_local", "net.conn.result", "net.conn.error", 
                              "security.category", "security.severity"],
        "example": {
            "net.transport": "tcp",
            "net.dst.ip": "example.com",
            "net.dst.port": 443,
            "net.is_local": False,
            "security.category": "outbound_connection",
            "security.severity": "low",
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    },
    "net.conn_error": {
        "description": "Network connection error event",
        "required_attributes": ["net.transport", "net.dst.ip", "net.dst.port", "net.conn.error", "session.id"],
        "optional_attributes": ["net.is_local", "security.category", "security.severity"],
        "example": {
            "net.transport": "tcp", 
            "net.dst.ip": "example.com",
            "net.dst.port": 443,
            "net.conn.error": "Connection refused",
            "security.category": "outbound_connection",
            "security.severity": "low",
            "session.id": "abcd1234-5678-efgh-ijkl"
        }
    }
} 