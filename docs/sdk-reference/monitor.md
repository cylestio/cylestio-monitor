# Monitor Module

The Monitor Module is the core component of Cylestio Monitor, providing the main functions for enabling and configuring monitoring of AI agents with OpenTelemetry-compliant telemetry.

## Core Functions

### `start_monitoring`

Initializes monitoring for an AI agent.

```python
from cylestio_monitor import start_monitoring

# Basic usage
start_monitoring(agent_id="my-agent")

# With additional configuration
start_monitoring(
    agent_id="my-agent",
    config={
        "debug_level": "INFO",
        "log_file": "/path/to/logs/monitoring.json",
        "api_endpoint": "https://api.example.com/events",
        "development_mode": False,
        "enable_framework_patching": True
    }
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Unique identifier for the agent being monitored |
| `config` | dict | (Optional) Configuration dictionary with the following options: |
| - `debug_level` | string | Logging level for SDK's internal logs (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| - `log_file` | string | Path to log file or directory for telemetry events |
| - `api_endpoint` | string | URL of the remote API endpoint to send events to |
| - `development_mode` | boolean | Enable additional development features like detailed logging |
| - `enable_framework_patching` | boolean | Whether to automatically patch frameworks like LangChain, LangGraph, etc. |

#### Returns

None

### `stop_monitoring`

Stops monitoring and cleans up resources.

```python
from cylestio_monitor import stop_monitoring

# Stop monitoring
stop_monitoring()
```

#### Parameters

None

#### Returns

None

### `get_api_endpoint`

Gets the configured API endpoint for sending events.

```python
from cylestio_monitor import get_api_endpoint

# Get API endpoint
endpoint = get_api_endpoint()
print(f"API endpoint: {endpoint}")
```

#### Parameters

None

#### Returns

string: URL of the configured API endpoint

## Trace Context

The Monitor Module automatically manages trace context following OpenTelemetry standards:

```python
from cylestio_monitor.utils.trace_context import TraceContext

# Get current trace context
context = TraceContext.get_current_context()
print(f"Trace ID: {context['trace_id']}")
print(f"Span ID: {context['span_id']}")
```

### Trace Context Fields

| Field | Description |
|-------|-------------|
| `trace_id` | 32-character hex string identifying the entire trace |
| `span_id` | 16-character hex string identifying the current operation |
| `parent_span_id` | ID of the parent span, establishing hierarchical relationships |
| `agent_id` | Identifier of the agent associated with this trace |

## Examples

### Basic Monitoring

```python
from cylestio_monitor import start_monitoring, stop_monitoring
from anthropic import Anthropic

# Create LLM client
client = Anthropic()

# Start monitoring
start_monitoring(
    agent_id="my-agent",
    config={
        "log_file": "output/monitoring.json"
    }
)

try:
    # Use client as normal
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Hello, Claude!"}]
    )
finally:
    # Always stop monitoring when done
    stop_monitoring()
```

### Production Monitoring with API Endpoint

```python
from cylestio_monitor import start_monitoring

# Enable production-grade monitoring
start_monitoring(
    agent_id="production-agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/var/log/cylestio/monitoring.json"
    }
)
```

### Monitoring with Framework Patching

Cylestio Monitor automatically detects and patches supported frameworks:

```python
from cylestio_monitor import start_monitoring
import langchain
import langgraph

# Start monitoring with framework patching enabled
start_monitoring(
    agent_id="ai-agent",
    config={
        "log_file": "output/monitoring.json",
        "enable_framework_patching": True  # This is the default
    }
)

# LangChain and LangGraph operations will be automatically monitored
```

## Using API Client Directly

```python
from cylestio_monitor.api_client import send_event_to_api

# Send custom event to API
event = {
    "name": "custom.event",
    "level": "INFO",
    "attributes": {
        "custom_field": "custom_value"
    }
}
send_event_to_api(event)
``` 