# Monitor Module

The Monitor Module is the core component of Cylestio Monitor, providing the main functions for enabling and configuring monitoring of AI agents with OpenTelemetry-compliant telemetry.

## Core Functions

### `start_monitoring`

Initializes monitoring for an AI agent.

```python
import cylestio_monitor

# Basic usage
cylestio_monitor.start_monitoring(agent_id="my-agent")

# With additional configuration
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "debug_level": "INFO",
        "log_file": "output/monitoring.json",
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
import cylestio_monitor

# Stop monitoring
cylestio_monitor.stop_monitoring()
```

#### Parameters

None

#### Returns

None

### `get_api_endpoint`

Gets the configured API endpoint for sending events.

```python
import cylestio_monitor

# Get API endpoint
endpoint = cylestio_monitor.get_api_endpoint()
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
print(f"Trace ID: {context.get('trace_id')}")
print(f"Span ID: {context.get('span_id')}")
```

### Trace Context Fields

| Field | Description |
|-------|-------------|
| `trace_id` | 32-character hex string identifying the entire trace |
| `span_id` | 16-character hex string identifying the current operation |
| `parent_span_id` | ID of the parent span, establishing hierarchical relationships |
| `agent_id` | Identifier of the agent associated with this trace |

## Event Logging

For custom event logging, see the [Events System](events.md) documentation.

```python
from cylestio_monitor.utils.event_logging import log_event

# Log a custom event
log_event(
    name="custom.operation.complete",
    attributes={"records_processed": 100}
)
```

## Examples

### Basic Monitoring

```python
import cylestio_monitor
from anthropic import Anthropic

# Start monitoring
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "log_file": "output/monitoring.json"
    }
)

# Create Anthropic client - will be automatically patched
client = Anthropic()

try:
    # Use client as normal - all calls are automatically monitored
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Hello, Claude!"}]
    )
finally:
    # Always stop monitoring when done
    cylestio_monitor.stop_monitoring()
```

### Production Monitoring with API Endpoint

```python
import cylestio_monitor

# Enable production-grade monitoring
cylestio_monitor.start_monitoring(
    agent_id="production-agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/var/log/cylestio/monitoring.json"
    }
)
```

### Automatic Framework Detection

Cylestio Monitor automatically detects and patches supported frameworks:

```python
import cylestio_monitor

# Start monitoring before importing any frameworks
cylestio_monitor.start_monitoring(
    agent_id="ai-agent",
    config={
        "log_file": "output/monitoring.json",
        "enable_framework_patching": True  # This is the default
    }
)

# Now import and use frameworks - they will be automatically monitored
import langchain
from langchain.chat_models import ChatAnthropic

# LangChain operations will be automatically monitored
llm = ChatAnthropic()
```

## Creating Custom Spans

For custom operation tracking, use the Span context manager:

```python
from cylestio_monitor.utils.instrumentation import Span

# Create a span for a custom operation
with Span("database-query", attributes={
    "database.name": "users",
    "database.operation": "select"
}):
    # Run the database query
    result = db.execute_query(query, params)
```

For more detailed information about event logging and spans, see the [Tracing](tracing.md) documentation.
