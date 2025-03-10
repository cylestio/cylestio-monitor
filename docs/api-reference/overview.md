# API Reference Overview

## Core Modules

- **[Monitor Module](monitor.md)**: The main entry point for enabling and disabling monitoring
- **[Events Processor](events-processor.md)**: Processes and logs monitoring events
- **[Events Listener](events-listener.md)**: Listens for and intercepts events from LLM clients and MCP
- **[Database](database.md)**: Stores and retrieves monitoring events

## Public API Functions

### `enable_monitoring`

```python
from cylestio_monitor import enable_monitoring

enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    llm_method_path="messages.create",
    log_file="/path/to/logs/monitoring.json",
    debug_level="INFO"
)
```

### `disable_monitoring`

```python
from cylestio_monitor import disable_monitoring

disable_monitoring()
```

### `log_event`

```python
from cylestio_monitor import log_event

log_event(
    event_type="custom_event",
    data={"key": "value"},
    channel="SYSTEM",
    level="info"
)
```

### `get_database_path`

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database path: {db_path}")
```

### `cleanup_old_events`

```python
from cylestio_monitor import cleanup_old_events

deleted_count = cleanup_old_events(days=30)
print(f"Deleted {deleted_count} old events")
```

## Database Utility Functions

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events
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

# Get agent statistics
stats = db_utils.get_agent_stats(agent_id="my-project")
```

## Configuration

The `config` module provides access to the global configuration:

```python
from cylestio_monitor.config import ConfigManager

# Get the configuration manager
config_manager = ConfigManager()

# Get a configuration value
suspicious_keywords = config_manager.get_suspicious_keywords()

# Set a configuration value
config_manager.set("security.enabled", True)
```

## Module Structure

The SDK is organized into the following modules:

```
cylestio_monitor/
├── __init__.py           # Public API
├── monitor.py            # Main monitoring functionality
├── events_processor.py   # Event processing and logging
├── events_listener.py    # Event interception
├── db/                   # Database functionality
│   ├── __init__.py
│   ├── db_manager.py     # Database connection management
│   └── utils.py          # Database utility functions
├── config/               # Configuration management
│   ├── __init__.py
│   ├── config_manager.py # Configuration loading and access
│   └── default_config.yaml # Default configuration
└── patchers/             # Framework-specific patchers
    ├── __init__.py
    ├── anthropic.py      # Anthropic Claude patcher
    └── mcp.py            # MCP patcher
```

## Next Steps

To learn more about specific modules, check out the following pages:

- [Monitor Module](monitor.md): Details on the main monitoring functionality
- [Events Processor](events-processor.md): How events are processed and logged
- [Events Listener](events-listener.md): How events are intercepted
- [Database](database.md): How events are stored and retrieved 