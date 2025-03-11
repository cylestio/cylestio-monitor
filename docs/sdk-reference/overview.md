# SDK Reference Overview

The Cylestio Monitor SDK provides a comprehensive API for monitoring and securing AI agents. This reference section documents the core modules and functions available in the SDK.

## Core Modules

The SDK is organized into several core modules:

- **Monitor Module**: Core functionality for enabling and configuring monitoring
- **Events System**: Event processing and handling for AI interactions
- **Database**: Storage and retrieval of monitoring data

## Basic Usage

```python
from cylestio_monitor import enable_monitoring, disable_monitoring

# Enable monitoring
enable_monitoring(agent_id="my-agent")

# Disable monitoring when done
disable_monitoring()
```

## Advanced Usage

For more advanced usage, you can interact directly with the lower-level APIs:

```python
from cylestio_monitor.events_processor import log_event
from cylestio_monitor.db import utils as db_utils

# Log a custom event
log_event(
    event_type="custom_event",
    data={"key": "value"},
    channel="CUSTOM"
)

# Query the monitoring database
events = db_utils.get_recent_events(agent_id="my-agent", limit=10)
```

## Next Steps

Explore the specific module documentation for detailed information:

- [Monitor Module](monitor.md): Main monitoring functionality
- [Events System](events.md): Event processing and handling
- [Database](database.md): Database storage and retrieval 