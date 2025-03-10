# Database Module

The database module provides a SQLite-based storage solution for Cylestio Monitor events.

## Database Location

The database file is stored in an OS-specific location:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
- **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database path: {db_path}")
```

## Database Schema

The database has two main tables:

1. **agents**: Stores information about each agent (project)
   - `id`: Primary key
   - `agent_id`: Unique ID of the agent
   - `created_at`: When the agent was first seen
   - `last_seen`: When the agent was last seen

2. **events**: Stores all monitoring events
   - `id`: Primary key
   - `agent_id`: Foreign key to the agents table
   - `event_type`: Type of event (e.g., "LLM_call_start", "MCP_tool_call_finish")
   - `channel`: Channel of the event (e.g., "LLM", "MCP", "SYSTEM")
   - `level`: Log level (e.g., "info", "warning", "error")
   - `timestamp`: When the event occurred
   - `data`: JSON data containing the event details

## Utility Functions

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

# Clean up old events
deleted_count = db_utils.cleanup_old_events(days=30)
```

## Indexes

The database includes several indexes to optimize query performance:

- `idx_events_agent_id`: Index on the agent_id column
- `idx_events_event_type`: Index on the event_type column
- `idx_events_timestamp`: Index on the timestamp column
- `idx_events_channel`: Index on the channel column
- `idx_events_level`: Index on the level column

## Database Utility Functions

The `db.utils` module provides utility functions for working with the database:

### `get_db_path`

```python
def get_db_path() -> str:
```

Gets the path to the global SQLite database.

#### Parameters

- None

#### Returns

- str: Path to the database file

#### Example

```python
from cylestio_monitor.db import utils as db_utils

db_path = db_utils.get_db_path()
print(f"Database path: {db_path}")
```

### `get_recent_events`

```python
def get_recent_events(agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets the most recent events for a specific agent or all agents.

#### Parameters

- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get recent events for all agents
all_events = db_utils.get_recent_events(limit=10)
```

### `get_events_by_type`

```python
def get_events_by_type(event_type: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets events of a specific type for a specific agent or all agents.

#### Parameters

- `event_type` (str): The event type to filter by
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get LLM call start events for a specific agent
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get LLM call start events for all agents
all_llm_events = db_utils.get_events_by_type("LLM_call_start")
```

### `get_events_last_hours`

```python
def get_events_last_hours(hours: int, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets events from the last N hours for a specific agent or all agents.

#### Parameters

- `hours` (int): The number of hours to look back
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get events from the last 24 hours for a specific agent
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")

# Get events from the last 24 hours for all agents
all_recent_events = db_utils.get_events_last_hours(24)
```

### `get_events_last_days`

```python
def get_events_last_days(days: int, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets events from the last N days for a specific agent or all agents.

#### Parameters

- `days` (int): The number of days to look back
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get events from the last 7 days for a specific agent
weekly_events = db_utils.get_events_last_days(7, agent_id="my-project")

# Get events from the last 7 days for all agents
all_weekly_events = db_utils.get_events_last_days(7)
```

### `get_events_by_channel`

```python
def get_events_by_channel(channel: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets events of a specific channel for a specific agent or all agents.

#### Parameters

- `channel` (str): The channel to filter by
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get MCP events for a specific agent
mcp_events = db_utils.get_events_by_channel("MCP", agent_id="my-project")

# Get MCP events for all agents
all_mcp_events = db_utils.get_events_by_channel("MCP")
```

### `get_events_by_level`

```python
def get_events_by_level(level: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Gets events of a specific level for a specific agent or all agents.

#### Parameters

- `level` (str): The level to filter by
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get warning events for a specific agent
warning_events = db_utils.get_events_by_level("warning", agent_id="my-project")

# Get warning events for all agents
all_warning_events = db_utils.get_events_by_level("warning")
```

### `search_events`

```python
def search_events(query: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
```

Searches events for a specific query for a specific agent or all agents.

#### Parameters

- `query` (str): The search query
- `agent_id` (str, optional): The agent ID to filter by. If None, events for all agents are returned. Defaults to None.
- `limit` (int, optional): The maximum number of events to return. Defaults to 100.

#### Returns

- List[Dict]: A list of event dictionaries

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Search for events containing "error" for a specific agent
search_results = db_utils.search_events("error", agent_id="my-project")

# Search for events containing "error" for all agents
all_search_results = db_utils.search_events("error")
```

### `get_agent_stats`

```python
def get_agent_stats(agent_id: Optional[str] = None) -> Dict:
```

Gets statistics for a specific agent or all agents.

#### Parameters

- `agent_id` (str, optional): The agent ID to filter by. If None, statistics for all agents are returned. Defaults to None.

#### Returns

- Dict: A dictionary of statistics

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Get statistics for a specific agent
agent_stats = db_utils.get_agent_stats(agent_id="my-project")

# Get statistics for all agents
all_stats = db_utils.get_agent_stats()
```

### `cleanup_old_events`

```python
def cleanup_old_events(days: int = 30) -> int:
```

Deletes events older than the specified number of days.

#### Parameters

- `days` (int, optional): Number of days to keep. Events older than this will be deleted. Defaults to 30.

#### Returns

- int: Number of deleted events

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Delete events older than 30 days
deleted_count = db_utils.cleanup_old_events(days=30)
print(f"Deleted {deleted_count} old events")
```

### `optimize_database`

```python
def optimize_database() -> None:
```

Optimizes the database by running VACUUM and ANALYZE.

#### Parameters

- None

#### Returns

- None

#### Example

```python
from cylestio_monitor.db import utils as db_utils

# Optimize the database
db_utils.optimize_database()
```

## DBManager Class

The `DBManager` class is responsible for managing the database connection and executing queries. It's used internally by the utility functions and is not typically used directly.

```python
class DBManager:
    def __init__(self):
        self._db_path = None
        self._connection_lock = threading.RLock()
        self._local = threading.local()
        
    def _get_connection(self):
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self._get_db_path())
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection
```

## Thread Safety

The database module is thread-safe. It uses a lock to protect critical sections and thread-local connections to ensure that each thread has its own connection to the database.

## Error Handling

The database module includes error handling to ensure that database operations don't crash your application. If an error occurs during a database operation, it will be logged and the operation will fail gracefully.

## Performance Considerations

- The database uses indexes to optimize query performance
- The database uses the JSON1 extension to efficiently query JSON data
- The database uses prepared statements to prevent SQL injection attacks
- The database uses transactions to ensure data integrity

## Limitations

- The database is not designed for high-concurrency scenarios
- The database is not designed for distributed deployments
- The database is not designed for very large datasets (millions of events)

For high-concurrency, distributed, or very large-scale deployments, consider using a more robust database solution like PostgreSQL or MongoDB. 