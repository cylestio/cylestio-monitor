# HTTP-based RCE Detection

This PR implements HTTP-based RCE detection capabilities in Cylestio Monitor to detect shell access patterns and command execution in HTTP traffic.

## Overview

The implementation addresses a critical security gap where RCE attacks could occur over HTTP/HTTPS connections (like the one demonstrated in the MCP shell transition attack), which were previously undetected by the socket-level network monitoring.

## Key Components

1. **HTTP Client Patching**:
   - Added patching for popular HTTP client libraries (`httpx` and `requests`)
   - Monitors both request and response bodies for shell patterns
   - Detects MCP to shell transitions and shell command execution patterns

2. **MCP Shell Transition Detection**:
   - Added specific detection for MCP shell mode activation
   - Tracks transitions to shell command mode
   - Identifies command execution disguised as queries

3. **Enhanced Pattern Recognition**:
   - Added patterns for shell session control sequences
   - Added detection for shell command responses
   - Added detection for attack mode activation messages

4. **Test Coverage**:
   - Created a test script that simulates the MCP shell transition attack
   - Verifies detection of shell command execution in HTTP traffic
   - Confirms the system correctly generates security alerts

## Security Enhancements

This implementation significantly improves our ability to detect RCE attacks by:

1. Monitoring HTTP traffic at the application layer
2. Detecting when legitimate interfaces (like database connectors) are exploited to gain shell access
3. Detecting shell command execution disguised in HTTP request/response bodies
4. Alerting on specific patterns indicating successful exploitation

## Usage

The feature is enabled by default when starting Cylestio Monitor:

```python
import cylestio_monitor

cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "enable_http_monitoring": True,  # Default is True
        "log_file": "output/monitoring.json"
    }
)
```

## Testing

To test the new HTTP monitoring capabilities:

```bash
python examples/security/test_http_shell_detection.py
```

The test script simulates various HTTP-based attack patterns and verifies that the system correctly detects them.
