# Database

The Database module provides functions for storing and retrieving monitoring events.

## Overview

Cylestio Monitor stores all monitoring events in a SQLite database. The database is located at a global location specific to the operating system:

- **Linux**: `~/.local/share/cylestio/monitoring.db`
- **macOS**: `~/Library/Application Support/cylestio/monitoring.db`
- **Windows**: `%LOCALAPPDATA%\cylestio\monitoring.db`

## Database Managers

The database module provides two manager classes:

1. **DBManager** - Handles database operations for storing and retrieving monitoring events
2. **DatabaseManager** - Handles database initialization, verification, updates, and reset operations

### DatabaseManager

The `DatabaseManager` class provides comprehensive database management functionality, allowing for initialization, verification, updates, and reset operations. It ensures the database schema matches the SQLAlchemy model definitions and provides detailed reporting on any discrepancies.

#### Initialization

```python
from cylestio_monitor.db import DatabaseManager

# Create a DatabaseManager instance
db_manager = DatabaseManager()

# Initialize the database with default location
result = db_manager.initialize_database()

if result["success"]:
    print(f"Database initialized at: {result['db_path']}")
    print(f"Tables created: {', '.join(result['tables'])}")
else:
    print(f"Failed to initialize: {result['error']}")

# Don't forget to close when done
db_manager.close()
```

You can also specify a custom database path:

```python
from pathlib import Path
from cylestio_monitor.db import DatabaseManager

# Create a DatabaseManager instance
db_manager = DatabaseManager()

# Initialize with a custom path
custom_path = Path("/path/to/custom/database.db")
result = db_manager.initialize_database(custom_path)

if result["success"]:
    print(f"Database initialized at custom location: {result['db_path']}")
```

#### Schema Verification

The `verify_schema()` method checks if the database schema matches the SQLAlchemy model definitions:

```python
from cylestio_monitor.db import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize_database()

# Verify the schema
verification = db_manager.verify_schema()

if verification["success"]:
    if verification["matches"]:
        print("Database schema matches model definitions.")
    else:
        print("Database schema has discrepancies:")
        
        if verification["missing_tables"]:
            print(f"Missing tables: {', '.join(verification['missing_tables'])}")
        
        if verification["missing_columns"]:
            for table, columns in verification["missing_columns"].items():
                print(f"Table '{table}' missing columns: {', '.join(columns)}")
```

#### Schema Updates

The `update_schema()` method adds missing tables and columns to match the SQLAlchemy model definitions:

```python
from cylestio_monitor.db import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize_database()

# First verify the schema
verification = db_manager.verify_schema()

if not verification["matches"]:
    print("Schema discrepancies found. Updating schema...")
    
    # Update the schema
    update_result = db_manager.update_schema()
    
    if update_result["success"]:
        print("Schema update successful!")
        
        if update_result["tables_added"]:
            print(f"Tables added: {', '.join(update_result['tables_added'])}")
        
        if update_result["tables_modified"]:
            print(f"Tables modified: {', '.join(update_result['tables_modified'])}")
```

#### Database Reset

The `reset_database()` method drops all tables and recreates the schema:

```python
from cylestio_monitor.db import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize_database()

try:
    # The force parameter is required to confirm this destructive operation
    result = db_manager.reset_database(force=True)
    
    if result["success"]:
        print("Database reset successful!")
        
        if result["backed_up"]:
            print(f"Backup created at: {result['backup_path']}")
except ValueError as e:
    print(f"Error: {str(e)}")
```

#### Integration with Existing Code

The `DatabaseManager` class is designed to work alongside the existing `DBManager` class:

```python
from cylestio_monitor.db import DatabaseManager, DBManager

# First initialize and verify the database
db_manager = DatabaseManager()
db_manager.initialize_database()
db_manager.verify_schema()

# Then use DBManager for regular database operations
db_ops = DBManager()  # This will use the same database
agent_id = db_ops.get_or_create_agent("example_agent")

# Close both managers when done
db_ops.close()
db_manager.close()
```

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
from pathlib import Path

# Use a custom database path
custom_db_path = Path("/path/to/custom/database.db")

# Initialize the database
from cylestio_monitor.db import DatabaseManager
db_manager = DatabaseManager()
db_manager.initialize_database(custom_db_path)

# Now enable monitoring with the existing database
enable_monitoring(agent_id="my-agent", db_path=str(custom_db_path))
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