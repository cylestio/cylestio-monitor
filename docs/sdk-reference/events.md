# Events System

The Cylestio Monitor Events System provides a comprehensive framework for capturing, processing, and responding to events in your AI agent ecosystem, following OpenTelemetry standards for distributed tracing.

## Overview

The Events System consists of two main components:

1. **Events Listener**: Captures events from your AI agents
2. **Events Processor**: Processes and routes events to appropriate handlers

This modular design allows for flexible event handling and custom integrations, while maintaining OpenTelemetry compatibility.

## Event Types

Cylestio Monitor captures several types of events:

| Event Name | Description |
|------------|-------------|
| `llm.request` | Outgoing requests to LLM providers |
| `llm.response` | Incoming responses from LLM providers |
| `error` | Errors that occur during agent operation |
| `security.content.suspicious` | Security-related events for suspicious content |
| `security.content.dangerous` | Security-related events for dangerous content |
| `monitoring.start` | System event when monitoring begins |
| `monitoring.stop` | System event when monitoring stops |
| `mcp.request` | MCP protocol request events |
| `mcp.response` | MCP protocol response events |
| `mcp.call.start` | Start of MCP tool calls |
| `mcp.call.finish` | Completion of MCP tool calls |

## Using the Events System

### Basic Usage

The Events System is automatically enabled when you use the `start_monitoring` function:

```python
from cylestio_monitor import start_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
start_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "output/monitoring.json"
    }
)
```

### Custom Event Handlers

You can register custom event handlers to process specific event types:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log a custom event
log_event(
    name="custom.event",
    attributes={
        "custom_key": "custom_value",
        "source": "my_module"
    },
    level="INFO"
)
```

## Event Structure

Each event follows OpenTelemetry standards with this structure:

```python
{
    "timestamp": "2024-03-27T15:31:40.622017",        # ISO timestamp
    "trace_id": "2a8ec755032d4e2ab0db888ab84ef595",   # OpenTelemetry trace ID
    "span_id": "96d8c2be667e4c78",                    # OpenTelemetry span ID
    "parent_span_id": "f1490a668d69d1dc",             # OpenTelemetry parent span ID
    "name": "mcp.call.start",                         # Event name
    "level": "INFO",                                  # Event severity
    "attributes": {                                   # Event-specific attributes
        "method": "call_tool",
        "tool": "get_forecast",
        "args": "{'latitude': 37.7749, 'longitude': -122.4194}",
        "kwargs": "{}",
        "session.id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "agent_id": "weather-agent",                      # Agent identifier
    "schema_version": "1.0"                           # Schema version
}
```

## Trace Context and Spans

Cylestio Monitor implements OpenTelemetry trace context to provide hierarchical relationships between events:

- **Trace ID**: A unique identifier for a complete operation (e.g., a user request)
- **Span ID**: A unique identifier for a specific operation within a trace
- **Parent Span ID**: The span ID of the parent operation, creating a hierarchical relationship

This allows for proper tracking of operation flow and dependencies, helping you understand the relationships between events and the sequence of operations.

### Trace Context Management

The trace context is automatically managed, but you can also manually control it:

```python
from cylestio_monitor.utils.trace_context import TraceContext

# Start a new span
span_info = TraceContext.start_span("custom-operation")

try:
    # Perform some operation
    result = perform_operation()
    
    # Log success event
    log_event(
        name="custom.operation.success",
        attributes={"result": result}
    )
finally:
    # Always end the span
    TraceContext.end_span()
```

## Event Channels

Events can be routed to different channels for processing. See the [Monitoring Channels](../monitoring_channels.md) documentation for more details.

## Advanced Usage

### Filtering Events

You can filter events before they're processed:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log an event with specific attributes for filtering
log_event(
    name="custom.important.event",
    attributes={
        "priority": "high",
        "component": "user-auth",
        "environment": "production"
    },
    level="WARNING"
)
```

## Performance Considerations

- Event handlers should be lightweight and non-blocking
- For intensive processing, consider using background workers
- Monitor queue size to prevent memory issues

## Next Steps

- Learn about [Event Processors](events-processor.md) for handling events
- See [Monitoring Channels](../monitoring_channels.md) for routing events 