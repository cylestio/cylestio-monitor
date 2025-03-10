# Database Module

The database module provides a SQLite-based storage solution for Cylestio Monitor events. It ensures that all instances of the SDK write to the same database, regardless of the virtual environment in which they're installed.

## Overview

The database module uses SQLite with the JSON1 extension to store monitoring events in a structured format. It uses the `platformdirs` library to determine an OS-agnostic location for the database file, ensuring that it's accessible from any virtual environment.

## Database Location

The database file is stored in an OS-specific location determined by the `platformdirs` library:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
- **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

You can get the path to the database file programmatically:

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database path: {db_path}")
```

## Database Schema

The database has two main tables:

### agents

Stores information about each agent (project):

- `id`: Primary key
- `agent_id`: Unique ID of the agent
- `created_at`: When the agent was first seen
- `last_seen`: When the agent was last seen

### events

Stores all monitoring events:

- `id`: Primary key
- `agent_id`: Foreign key to the agents table
- `event_type`: Type of event (e.g., "LLM_call_start", "MCP_tool_call_finish")
- `channel`: Channel of the event (e.g., "LLM", "MCP", "SYSTEM")
- `level`: Log level (e.g., "info", "warning", "error")
- `timestamp`: When the event occurred
- `data`: JSON data containing the event details

## Indexes

The database includes several indexes to optimize query performance:

- `idx_events_agent_id`: Index on the agent_id column
- `idx_events_event_type`: Index on the event_type column
- `idx_events_timestamp`: Index on the timestamp column
- `idx_events_channel`: Index on the channel column
- `idx_events_level`: Index on the level column

## Usage

### Logging Events

Events are automatically logged to the database when you use the `log_event` function from the `events_processor` module. You don't need to interact with the database directly for logging.

### Querying Events

You can query events from the database using the utility functions in the `db.utils` module:

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get events by type
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get events from the last 24 hours
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")

# Get events from the last 7 days
weekly_events = db_utils.get_events_last_days(7, agent_id="my-project")

# Get events by channel
mcp_events = db_utils.get_events_by_channel("MCP", agent_id="my-project")

# Get events by level
warning_events = db_utils.get_events_by_level("warning", agent_id="my-project")

# Search events
search_results = db_utils.search_events("error", agent_id="my-project")
```

### Agent Statistics

You can get statistics about agents:

```python
from cylestio_monitor.db import utils as db_utils

# Get statistics for all agents
all_stats = db_utils.get_agent_stats()

# Get statistics for a specific agent
agent_stats = db_utils.get_agent_stats(agent_id="my-project")

# Get event type distribution
event_types = db_utils.get_event_type_distribution(agent_id="my-project")

# Get channel distribution
channels = db_utils.get_channel_distribution(agent_id="my-project")

# Get level distribution
levels = db_utils.get_level_distribution(agent_id="my-project")
```

### Maintenance

You can perform maintenance operations on the database:

```python
from cylestio_monitor.db import utils as db_utils

# Delete events older than 30 days
deleted_count = db_utils.cleanup_old_events(days=30)

# Optimize the database
db_utils.optimize_database()
```

## Advanced Usage

If you need more control over the database, you can use the `DBManager` class directly:

```python
from cylestio_monitor.db.db_manager import DBManager

# Get the database manager instance
db_manager = DBManager()

# Execute a custom query
conn = db_manager._get_connection()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM events WHERE level = ?", ("error",))
error_count = cursor.fetchone()[0]
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