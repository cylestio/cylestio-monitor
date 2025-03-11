# Monitor Module

The monitor module is the main entry point for enabling and disabling monitoring in Cylestio Monitor.

## Functions

### `enable_monitoring`

```python
def enable_monitoring(
    agent_id: str,
    llm_client: Any = None,
    llm_method_path: str = "messages.create",
    log_file: Optional[str] = None,
    debug_level: str = "INFO",
) -> None:
```

Enables monitoring for LLM API calls and MCP tool calls.

#### Parameters

- `agent_id` (str): Unique identifier for the agent or project
- `llm_client` (Any, optional): LLM client instance to monitor
- `llm_method_path` (str, optional): Path to the LLM client method to patch
- `log_file` (str, optional): Path to the output log file
- `debug_level` (str, optional): Logging level for SDK's internal debug logs

#### Example

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/monitoring.json",
    debug_level="DEBUG"
)
```

### `disable_monitoring`

```python
def disable_monitoring() -> None:
```

Disables monitoring and cleans up resources.

#### Example

```python
from cylestio_monitor import disable_monitoring

# Disable monitoring
disable_monitoring()
```

### `get_database_path`

```python
def get_database_path() -> str:
```

Gets the path to the global SQLite database.

#### Returns

- str: Path to the database file

#### Example

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database path: {db_path}")
```

### `cleanup_old_events`

```python
def cleanup_old_events(days: int = 30) -> int:
```

Deletes events older than the specified number of days.

#### Parameters

- `days` (int, optional): Number of days to keep. Events older than this will be deleted.

#### Returns

- int: Number of deleted events

#### Example

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 30 days
deleted_count = cleanup_old_events(days=30)
print(f"Deleted {deleted_count} old events")
``` 