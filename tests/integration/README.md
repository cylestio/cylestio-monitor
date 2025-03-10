# Integration Tests for Cylestio Monitor

This directory contains integration tests for the Cylestio Monitor SDK. These tests verify that the SDK works correctly with all its components integrated together.

## Available Tests

### `test_db_logging_integration.py`

This test demonstrates how the cylestio-monitor SDK logs events to both SQLite database and JSON files. It simulates a typical usage scenario where MCP tool calls are monitored and logged.

#### Usage

Run as a standalone script:
```bash
PYTHONPATH=src python tests/integration/test_db_logging_integration.py
```

Run with pytest:
```bash
pytest tests/integration/test_db_logging_integration.py -v
```

## JSON Logging

The Cylestio Monitor SDK can log events to both a SQLite database and JSON files. The JSON logging feature is particularly useful for real-time monitoring and analysis.

### JSON Log File Naming

When enabling monitoring with a log file, the SDK will use the following naming conventions:

1. If a directory is provided as `log_file`, a file named `{agent_id}_monitoring_{timestamp}.json` will be created in that directory.
2. If a file without extension is provided, `.json` will be added to the filename.

Example:
```python
# Log to a specific file
enable_monitoring(agent_id="my_agent", log_file="/path/to/logs/monitoring.json")
# Result: /path/to/logs/monitoring.json

# Log to a directory (a timestamped file will be created)
enable_monitoring(agent_id="my_agent", log_file="/path/to/logs/")
# Result: /path/to/logs/my_agent_monitoring_20250310_123456.json
```

### JSON Log Format

Each log entry is a JSON object with the following structure:

```json
{
  "timestamp": "2025-03-10T23:32:48.145793",
  "level": "INFO",
  "channel": "TEST",
  "agent_id": "test_agent",
  "event": "test_event",
  "data": {
    "message": "This is a test event"
  }
}
```

The `data` field contains event-specific information that varies depending on the event type.

## SQLite Database

The SDK also logs all events to a SQLite database. The database is created in the following locations:

- During testing: In a temporary directory specified by the `CYLESTIO_TEST_DB_DIR` environment variable
- In production: In the user's application data directory (platform-specific)

The database contains tables for agents, events, and other monitoring data. You can query this database using the utilities provided in the `cylestio_monitor.db.utils` module. 