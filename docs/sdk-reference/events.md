# Events System

The Events System is responsible for processing, logging, and storing events generated during AI agent monitoring. This includes both built-in events and custom events.

## Core Components

The Events System consists of two main components:

1. **Events Processor**: Processes and logs monitoring events
2. **Events Listener**: Intercepts events from AI frameworks and LLM clients

## Events Processor Functions

### `log_event`

Logs a monitoring event.

```python
from cylestio_monitor.events_processor import log_event

# Log a custom event
log_event(
    event_type="custom_event",
    data={"key": "value"},
    channel="CUSTOM_CHANNEL",
    level="info"
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | string | Type of event |
| `data` | dict | Event data |
| `channel` | string | Event channel (SYSTEM, LLM, API, MCP, etc.) |
| `level` | string | Event level (info, warning, error, alert) |

#### Returns

None

### `get_event_history`

Gets the history of logged events.

```python
from cylestio_monitor.events_processor import get_event_history

# Get all events
all_events = get_event_history()

# Get events for a specific agent
agent_events = get_event_history(agent_id="my-agent")

# Get events of a specific type
type_events = get_event_history(event_type="LLM_call_start")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | (Optional) Filter by agent ID |
| `event_type` | string | (Optional) Filter by event type |
| `limit` | int | (Optional) Maximum number of events to return |

#### Returns

list: A list of event dictionaries

## Event Types

Cylestio Monitor produces several types of events:

### System Events

- `monitoring_enabled`: When monitoring is enabled
- `monitoring_disabled`: When monitoring is disabled
- `config_updated`: When configuration is updated

### LLM Events

- `LLM_call_start`: When an LLM API call starts
- `LLM_call_finish`: When an LLM API call completes
- `LLM_call_error`: When an LLM API call fails
- `LLM_call_blocked`: When an LLM API call is blocked due to security concerns

### MCP Events

- `MCP_tool_call_start`: When an MCP tool call starts
- `MCP_tool_call_finish`: When an MCP tool call completes
- `MCP_tool_call_error`: When an MCP tool call fails
- `MCP_tool_call_blocked`: When an MCP tool call is blocked due to security concerns

### Security Events

- `security_alert`: When a security issue is detected
- `security_block`: When content is blocked for security reasons
- `security_warning`: When potentially concerning content is detected

## Event Structure

Events are structured as JSON objects with the following fields:

```json
{
  "event": "LLM_call_start",
  "data": {
    "model": "claude-3-sonnet-20240229",
    "messages": [...],
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "timestamp": "2024-06-15T14:30:22.123456",
  "agent_id": "my-agent",
  "channel": "LLM",
  "level": "info"
}
```

## Custom Events

You can define and log custom events for your specific use cases:

```python
from cylestio_monitor.events_processor import log_event

# Log a custom event for user activity
log_event(
    event_type="user_login",
    data={
        "user_id": "user123",
        "ip_address": "192.168.1.1",
        "successful": True
    },
    channel="USER_ACTIVITY",
    level="info"
)

# Log a custom security event
log_event(
    event_type="permission_change",
    data={
        "user_id": "admin",
        "resource": "database",
        "old_permission": "read",
        "new_permission": "write"
    },
    channel="SECURITY",
    level="warning"
)
```

## Event Channels

Events are organized into channels for better organization and filtering:

- **SYSTEM**: System-level events
- **LLM**: LLM API call events
- **MCP**: MCP tool call events
- **SECURITY**: Security-related events
- **API**: General API call events
- **Custom channels**: You can define your own channels

For more information on channels, see [Monitoring Channels](../monitoring_channels.md). 