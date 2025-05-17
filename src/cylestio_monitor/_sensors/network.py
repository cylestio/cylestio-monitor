"""
Network connection monitoring sensor.

This module provides monitoring of outbound socket connections to detect
potential C2 channels or data exfiltration attempts after RCE.
"""

import socket
import functools
import threading
import urllib.parse
import os
import re
from typing import Tuple, Any, Optional, Union, List, Dict, Set

from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.event_context import get_session_id
from cylestio_monitor.utils.security_patterns import get_shell_access_network_patterns
from cylestio_monitor.config import ConfigManager

# Store original methods
_orig_connect = socket.socket.connect
_orig_connect_ex = socket.socket.connect_ex
_orig_send = socket.socket.send
_orig_sendall = socket.socket.sendall
_orig_recv = socket.socket.recv
_local_host = threading.local()  # Thread-local storage for connection context

# Toggle for enabling/disabling network detection
ENABLE_NETWORK_DETECTION = True

# Track our own telemetry endpoints to avoid monitoring our own connections
_OWN_ENDPOINTS: Set[Tuple[str, int]] = set()

# Track connection data for analysis
_connection_data: Dict[Tuple[socket.socket, int], Dict[str, Any]] = {}
_connection_data_lock = threading.RLock()


def _setup_own_endpoints():
    """
    Setup the list of our own endpoints that should not be monitored.
    Gets telemetry endpoint from config or environment variables.
    """
    global _OWN_ENDPOINTS

    # Get telemetry endpoint from environment variable first
    telemetry_endpoint = os.environ.get("CYLESTIO_TELEMETRY_ENDPOINT")

    # If not in environment, try from config
    if not telemetry_endpoint:
        config_manager = ConfigManager()
        telemetry_endpoint = config_manager.get("api.endpoint")

    # Default endpoint if none configured
    if not telemetry_endpoint:
        telemetry_endpoint = "http://127.0.0.1:8000"

    # Parse the endpoint to get host and port
    try:
        parsed = urllib.parse.urlparse(telemetry_endpoint)
        host = parsed.hostname or "127.0.0.1"
        # Use default ports if not specified
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # Add to our exclusion set
        _OWN_ENDPOINTS.add((host, port))

        # Also add the host with default ports in case they're used implicitly
        _OWN_ENDPOINTS.add((host, 80))
        _OWN_ENDPOINTS.add((host, 443))

        # Add localhost/127.0.0.1 alternatives
        if host in ("localhost", "127.0.0.1"):
            _OWN_ENDPOINTS.add(("localhost", port))
            _OWN_ENDPOINTS.add(("127.0.0.1", port))
    except Exception:
        # Fallback to default exclusion
        _OWN_ENDPOINTS.add(("127.0.0.1", 8000))


def _is_own_endpoint(host: str, port: int) -> bool:
    """Determine if this connection is to our own telemetry endpoint."""
    if not _OWN_ENDPOINTS:
        _setup_own_endpoints()

    # Normalize host
    normalized_host = host.lower()
    if normalized_host == "localhost":
        normalized_host = "127.0.0.1"

    return (normalized_host, port) in _OWN_ENDPOINTS


def _get_ip_port(address: Any) -> Tuple[str, int]:
    """Extract IP and port from various address formats."""
    if isinstance(address, tuple) and len(address) >= 2:
        # Standard (host, port) tuple
        return str(address[0]), int(address[1])
    elif hasattr(address, 'ip') and hasattr(address, 'port'):
        # Socket address object
        return str(address.ip), int(address.port)
    else:
        # Best effort for other formats
        try:
            addr_str = str(address)
            return addr_str, 0
        except:
            return "unknown", 0


def _categorize_connection(host: str, port: int) -> str:
    """Categorize the connection for security classification."""
    # Check for common C2 patterns
    if port in [4444, 4445, 1337, 6667, 6668, 6669, 31337]:  # Common reverse shell/C2 ports
        return "potential_c2"

    # Check for common exfiltration ports
    if port in [21, 22, 2222, 23]:  # FTP, SSH, Telnet
        return "potential_exfiltration"

    # Check for direct IP connections vs domain names
    if all(c.isdigit() or c == '.' for c in host):
        return "direct_ip"

    # Default category
    return "outbound_connection"


def _determine_severity(host: str, port: int, is_local: bool) -> str:
    """Determine the security severity based on connection details."""
    if is_local:
        return "low"

    category = _categorize_connection(host, port)

    if category == "potential_c2":
        return "critical"
    elif category == "potential_exfiltration":
        return "high"
    elif category == "direct_ip":
        return "medium"

    # Standard web ports are lower severity
    if port in [80, 443, 8080, 8443]:
        return "low"

    return "medium"


def _analyze_network_data(sock: socket.socket, data: bytes, direction: str, conn_id: int) -> None:
    """
    Analyze network traffic data for shell access patterns.

    Args:
        sock: The socket object
        data: The data being sent or received
        direction: Either 'send' or 'recv'
        conn_id: Unique connection identifier
    """
    if not ENABLE_NETWORK_DETECTION:
        return

    # Skip if data is empty or very small
    if not data or len(data) < 8:
        return

    # Get connection info
    with _connection_data_lock:
        if (sock, conn_id) not in _connection_data:
            # We don't have info on this connection
            return

        conn_info = _connection_data[(sock, conn_id)]

    # Skip our own telemetry
    host = conn_info.get("host", "")
    port = conn_info.get("port", 0)
    if _is_own_endpoint(host, port):
        return

    # Try to decode data as text - but don't fail if binary
    try:
        text_data = data.decode('utf-8', errors='replace')
    except:
        text_data = str(data)

    # Get shell access patterns
    shell_patterns = get_shell_access_network_patterns()

    # Match against patterns
    matches = []
    for pattern_info in shell_patterns:
        pattern = pattern_info["regex"]
        description = pattern_info["description"]

        if re.search(pattern, text_data, re.MULTILINE):
            matches.append(description)

    # If we found matches, log an alert
    if matches:
        alert_attributes = {
            "alert.type": "Shell Access Pattern in Network Traffic",
            "alert.severity": "critical",
            "alert.evidence": f"Traffic {'to' if direction == 'send' else 'from'} {host}:{port} contains shell access patterns: {', '.join(matches)}",
            "security.risk": "remote_code_execution",
            "security.category": "remote_code_execution",
            "security.severity": "critical",
            "security.description": f"Network traffic contains shell command patterns indicating potential RCE",
            "net.transport": conn_info.get("transport", "unknown"),
            "net.dst.ip": host,
            "net.dst.port": port,
            "net.traffic.direction": direction,
            "session.id": get_session_id()
        }

        log_event(
            name="security.alert",
            attributes=alert_attributes,
            level="CRITICAL"
        )

        # Update connection info with shell detected flag
        with _connection_data_lock:
            if (sock, conn_id) in _connection_data:
                _connection_data[(sock, conn_id)]["shell_detected"] = True
                _connection_data[(sock, conn_id)]["shell_patterns"] = matches


def _span_connect(self, address):
    """
    Monkey-patched version of socket.connect that records network connection spans.
    """
    # Extract connection information
    host, port = _get_ip_port(address)

    # Skip localhost connections to reduce noise (option to change later)
    is_local = host in ('localhost', '127.0.0.1', '::1')

    # Skip monitoring our own telemetry connections
    if _is_own_endpoint(host, port):
        # Just call the original function without monitoring
        return _orig_connect(self, address)

    # Determine connection type
    sock_type = getattr(self, 'type', 0)
    sock_type_name = {
        socket.SOCK_STREAM: 'tcp',
        socket.SOCK_DGRAM: 'udp'
    }.get(sock_type, 'unknown')

    # Set security severity based on the connection type
    category = _categorize_connection(host, port)
    severity = _determine_severity(host, port, is_local)

    # Prepare connection event attributes
    conn_attributes = {
        "net.transport": sock_type_name,
        "net.dst.ip": host,
        "net.dst.port": port,
        "net.is_local": is_local,
        "session.id": get_session_id(),
        "security.category": category,
        "security.severity": severity
    }

    # Log the connection event
    log_event(
        name="net.conn_open",
        attributes=conn_attributes,
        level="INFO"
    )

    # Emit high-severity alert directly for suspicious connections
    if severity in ["critical", "high"]:
        alert_attributes = {
            "alert.type": f"Suspicious Network Connection ({category})",
            "alert.severity": severity,
            "alert.evidence": f"Connection to {host}:{port} using {sock_type_name}",
            "security.risk": "potential_data_exfiltration" if category == "potential_exfiltration" else "potential_c2",
            "security.category": "network_connection",
            "security.severity": severity,
            "security.description": f"Potentially suspicious outbound connection to {host}:{port}",
            "net.transport": sock_type_name,
            "net.dst.ip": host,
            "net.dst.port": port,
            "session.id": get_session_id()
        }

        # Log critical alerts at CRITICAL level, others at WARNING
        log_level = "CRITICAL" if severity == "critical" else "WARNING"

        log_event(
            name="security.alert",
            attributes=alert_attributes,
            level=log_level
        )

    # Actually establish the connection
    try:
        result = _orig_connect(self, address)
        # Update local information for future reference
        _local_host.current_host = host
        _local_host.current_port = port

        # Store connection info for traffic analysis
        conn_id = id(self)
        with _connection_data_lock:
            _connection_data[(self, conn_id)] = {
                "host": host,
                "port": port,
                "transport": sock_type_name,
                "is_local": is_local,
                "shell_detected": False
            }

        return result
    except Exception as e:
        # Record the exception but let it propagate
        conn_attributes["net.conn.error"] = str(e)
        log_event(
            name="net.conn_error",
            attributes=conn_attributes,
            level="WARNING"
        )
        raise


def _span_connect_ex(self, address):
    """
    Monkey-patched version of socket.connect_ex that records network connection spans.
    """
    host, port = _get_ip_port(address)

    # Skip monitoring our own telemetry connections
    if _is_own_endpoint(host, port):
        # Just call the original function without monitoring
        return _orig_connect_ex(self, address)

    is_local = host in ('localhost', '127.0.0.1', '::1')

    sock_type = getattr(self, 'type', 0)
    sock_type_name = {
        socket.SOCK_STREAM: 'tcp',
        socket.SOCK_DGRAM: 'udp'
    }.get(sock_type, 'unknown')

    category = _categorize_connection(host, port)
    severity = _determine_severity(host, port, is_local)

    # Prepare connection event attributes
    conn_attributes = {
        "net.transport": sock_type_name,
        "net.dst.ip": host,
        "net.dst.port": port,
        "net.is_local": is_local,
        "session.id": get_session_id(),
        "security.category": category,
        "security.severity": severity
    }

    # Log the connection attempt
    log_event(
        name="net.conn_open",
        attributes=conn_attributes,
        level="INFO"
    )

    # Actually attempt the connection
    result = _orig_connect_ex(self, address)

    # If connection succeeded (result == 0)
    if result == 0:
        # Update connection info for traffic analysis
        conn_id = id(self)
        with _connection_data_lock:
            _connection_data[(self, conn_id)] = {
                "host": host,
                "port": port,
                "transport": sock_type_name,
                "is_local": is_local,
                "shell_detected": False
            }

        # Update local information for future reference
        _local_host.current_host = host
        _local_host.current_port = port
    else:
        # Connection failed
        conn_attributes["net.conn.error_code"] = result
        log_event(
            name="net.conn_error",
            attributes=conn_attributes,
            level="INFO"
        )

    return result


def _span_send(self, data, *args, **kwargs):
    """
    Monkey-patched version of socket.send that monitors data for shell patterns.
    """
    # Call original method first
    result = _orig_send(self, data, *args, **kwargs)

    # Get connection ID
    conn_id = id(self)

    # Analyze the data
    try:
        _analyze_network_data(self, data, 'send', conn_id)
    except Exception as e:
        log_error(f"Error analyzing network send data: {e}")

    return result


def _span_sendall(self, data, *args, **kwargs):
    """
    Monkey-patched version of socket.sendall that monitors data for shell patterns.
    """
    # Get connection ID
    conn_id = id(self)

    # Analyze the data
    try:
        _analyze_network_data(self, data, 'send', conn_id)
    except Exception as e:
        log_error(f"Error analyzing network sendall data: {e}")

    # Call original method
    return _orig_sendall(self, data, *args, **kwargs)


def _span_recv(self, bufsize, *args, **kwargs):
    """
    Monkey-patched version of socket.recv that monitors received data for shell patterns.
    """
    # Call original method first
    data = _orig_recv(self, bufsize, *args, **kwargs)

    # Get connection ID
    conn_id = id(self)

    # Analyze the data if we got something
    if data:
        try:
            _analyze_network_data(self, data, 'recv', conn_id)
        except Exception as e:
            log_error(f"Error analyzing network receive data: {e}")

    return data


def enable_network_detection(enabled: bool = True) -> None:
    """
    Enable or disable network detection.

    Args:
        enabled: Whether network detection should be enabled
    """
    global ENABLE_NETWORK_DETECTION
    ENABLE_NETWORK_DETECTION = enabled


def initialize():
    """Initialize network connection monitoring."""
    # Patch the socket.connect method
    socket.socket.connect = _span_connect
    socket.socket.connect_ex = _span_connect_ex
    socket.socket.send = _span_send
    socket.socket.sendall = _span_sendall
    socket.socket.recv = _span_recv

    # Ensure endpoints are initialized
    _setup_own_endpoints()
