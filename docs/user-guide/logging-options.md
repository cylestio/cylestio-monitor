# Logging Options

Cylestio Monitor provides flexible logging options to help you capture and analyze monitoring data.

## Logging Destinations

### SQLite Database

The database file is stored in an OS-specific location:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
- **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database path: {db_path}")
```

### JSON Files

```python
from cylestio_monitor import enable_monitoring

# Log to a specific file
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/monitoring.json"
)

# Log to a directory (a timestamped file will be created)
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/"
)
```

## Log Levels

- **DEBUG**: Detailed information, typically of interest only when diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: An indication that something unexpected happened
- **ERROR**: Due to a more serious problem, the software has not been able to perform a function
- **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running

```python
from cylestio_monitor import enable_monitoring

enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    debug_level="DEBUG"  # More verbose logging
)
```

## Event Structure

```json
{
  "event": "EVENT_TYPE",
  "data": {
    // Event-specific data
  },
  "timestamp": "2024-03-10T22:15:30.123456",
  "channel": "CHANNEL",
  "level": "LEVEL"
}
```

## Querying Logs

### Querying the SQLite Database

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get events by type
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get events from the last 24 hours
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")

# Get events by channel
mcp_events = db_utils.get_events_by_channel("MCP", agent_id="my-project")

# Get events by level
warning_events = db_utils.get_events_by_level("warning", agent_id="my-project")

# Search events
search_results = db_utils.search_events("error", agent_id="my-project")
```

## Database Maintenance

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 30 days
deleted_count = cleanup_old_events(days=30)
print(f"Deleted {deleted_count} old events")
``` 