# Monitor Module

The Monitor Module is the core component of Cylestio Monitor, providing the main functions for enabling and configuring monitoring of AI agents.

## Core Functions

### `enable_monitoring`

Enables monitoring for an AI agent.

```python
from cylestio_monitor import enable_monitoring

# Basic usage
enable_monitoring(agent_id="my-agent")

# With an LLM client
enable_monitoring(
    agent_id="my-agent",
    llm_client=client
)

# With additional configuration
enable_monitoring(
    agent_id="my-agent",
    llm_client=client,
    block_dangerous=True,
    security_level="high",
    log_file="/path/to/logs/monitoring.json",
    development_mode=False
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Unique identifier for the agent being monitored |
| `llm_client` | object | (Optional) LLM client instance to monitor |
| `block_dangerous` | boolean | (Optional) Whether to block dangerous prompts |
| `security_level` | string | (Optional) Security level: "low", "medium", "high" |
| `log_file` | string | (Optional) Path to log file or directory |
| `development_mode` | boolean | (Optional) Enable additional debug information |

#### Returns

None

### `disable_monitoring`

Disables monitoring and cleans up resources.

```python
from cylestio_monitor import disable_monitoring

# Disable monitoring
disable_monitoring()
```

#### Parameters

None

#### Returns

None

### `get_database_path`

Gets the path to the monitoring database.

```python
from cylestio_monitor import get_database_path

# Get database path
db_path = get_database_path()
print(f"Database path: {db_path}")
```

#### Parameters

None

#### Returns

string: Path to the monitoring database

### `setup_periodic_reporting`

Sets up periodic reporting of monitoring data.

```python
from cylestio_monitor import setup_periodic_reporting

# Setup periodic reporting
setup_periodic_reporting(
    hours=24,
    report_path="/path/to/reports/",
    include_security=True,
    include_performance=True
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `hours` | int | Hours between reports |
| `report_path` | string | Path to store reports |
| `include_security` | boolean | Include security information |
| `include_performance` | boolean | Include performance information |

#### Returns

None

## Examples

### Basic Monitoring

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my-agent",
    llm_client=client
)

# Use client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# Disable monitoring when done
from cylestio_monitor import disable_monitoring
disable_monitoring()
```

### Production Monitoring

```python
from cylestio_monitor import enable_monitoring

# Enable production-grade monitoring
enable_monitoring(
    agent_id="production-agent",
    llm_client=client,
    block_dangerous=True,
    security_level="high",
    log_file="/var/log/cylestio/monitoring.json"
)
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