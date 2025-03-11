# Database

The Database module provides functions for storing and retrieving monitoring events.

## Overview

Cylestio Monitor stores all monitoring events in a SQLite database. The database is located at a global location specific to the operating system:

- **Linux**: `~/.local/share/cylestio/monitoring.db`
- **macOS**: `~/Library/Application Support/cylestio/monitoring.db`
- **Windows**: `%LOCALAPPDATA%\cylestio\monitoring.db`

## Database Schema

The database schema is designed to efficiently store and query monitoring events:

### Events Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `event_type` | TEXT | Type of event |
| `data` | TEXT | JSON-encoded event data |
| `timestamp` | TEXT | ISO-formatted timestamp |
| `agent_id` | TEXT | ID of the agent |
| `channel` | TEXT | Event channel |
| `level` | TEXT | Event level |

## Utility Functions

The `db.utils` module provides functions for querying the database:

### `get_recent_events`

Gets the most recent events.

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events
events = db_utils.get_recent_events(limit=10)

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-agent", limit=10)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | (Optional) Filter by agent ID |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

### `get_events_by_type`

Gets events of a specific type.

```python
from cylestio_monitor.db import utils as db_utils

# Get all LLM call start events
events = db_utils.get_events_by_type("LLM_call_start")

# Get LLM call start events for a specific agent
events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-agent")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | string | Type of event |
| `agent_id` | string | (Optional) Filter by agent ID |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

### `get_events_by_channel`

Gets events from a specific channel.

```python
from cylestio_monitor.db import utils as db_utils

# Get all LLM events
events = db_utils.get_events_by_channel("LLM")

# Get LLM events for a specific agent
events = db_utils.get_events_by_channel("LLM", agent_id="my-agent")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | string | Event channel |
| `agent_id` | string | (Optional) Filter by agent ID |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

### `get_events_last_hours`

Gets events from the last N hours.

```python
from cylestio_monitor.db import utils as db_utils

# Get events from the last 24 hours
events = db_utils.get_events_last_hours(24)

# Get events from the last 24 hours for a specific agent
events = db_utils.get_events_last_hours(24, agent_id="my-agent")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `hours` | int | Number of hours to look back |
| `agent_id` | string | (Optional) Filter by agent ID |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

### `search_events`

Searches for events containing specific text.

```python
from cylestio_monitor.db import utils as db_utils

# Search for events containing "error"
events = db_utils.search_events("error")

# Search for events containing "error" for a specific agent
events = db_utils.search_events("error", agent_id="my-agent")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to search for |
| `agent_id` | string | (Optional) Filter by agent ID |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

## Data Retention

The database has built-in data retention functionality to prevent it from growing too large:

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 30 days
deleted_count = cleanup_old_events(days=30)
print(f"Deleted {deleted_count} old events")
```

## Custom Database Location

You can customize the database location:

```python
from cylestio_monitor import enable_monitoring

# Use a custom database path
enable_monitoring(
    agent_id="my-agent",
    database_path="/path/to/custom/database.db"
)
```

## Database Backup

To back up the database:

```python
import shutil
from cylestio_monitor import get_database_path

# Get the database path
db_path = get_database_path()

# Create a backup
shutil.copy(db_path, f"{db_path}.backup")
``` 