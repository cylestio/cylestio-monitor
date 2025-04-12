# Events System

## Overview

The Events System in Cylestio Monitor captures and processes events according to OpenTelemetry standards. It provides detailed visibility into LLM operations, agent execution, and custom application events.

## Event Types

Cylestio Monitor captures the following event types:

| Event Type | Description |
|------------|-------------|
| `llm.call.start` | The start of an LLM API call |
| `llm.call.finish` | The completion of an LLM API call with response data |
| `llm.error` | Errors occurring during LLM API calls |
| `agent.execution.start` | The beginning of an agent's execution cycle |
| `agent.execution.finish` | The completion of an agent's execution cycle |
| `agent.error` | Errors occurring during agent execution |
| `custom.event` | User-defined custom events |

## Basic Usage

The simplest way to use the Events System is through the core monitoring functions:

```python
import cylestio_monitor
from anthropic import Anthropic

# Start monitoring your application
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Create LLM client - automatically instrumented
client = Anthropic()

# Make LLM calls - events are automatically captured
response = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# Stop monitoring when done
cylestio_monitor.stop_monitoring()
```

## Custom Event Logging

You can log custom events using the `log_event` function:

```python
from cylestio_monitor.utils.event_logging import log_event
from cylestio_monitor.utils.event_utils import format_timestamp

# Log a custom event
log_event(
    name="data.processing.complete",
    attributes={
        "records_processed": 1500,
        "processing_time_ms": 350,
        "success": True
    },
    # timestamp is automatically set using format_timestamp() if not provided
)

# Or explicitly provide a timestamp
log_event(
    name="data.processing.complete",
    attributes={
        "records_processed": 1500,
        "processing_time_ms": 350,
        "success": True
    },
    timestamp=format_timestamp()  # Explicitly using the timestamp utility
)
```

## Event Structure

All events in Cylestio Monitor follow a standard structure:

```python
{
    "name": "llm.call.finish",          # Event type/name
    "timestamp": "2023-07-14T12:34:56.789Z", # ISO 8601 timestamp with UTC (Z suffix)
    "trace_id": "abc123...",            # Trace ID for correlation
    "span_id": "def456...",             # Span ID for this event
    "parent_span_id": "ghi789...",      # Parent span ID (optional)
    "agent_id": "my-agent",             # Agent identifier
    "attributes": {                     # Event-specific attributes
        "model": "claude-3-haiku-20240307",
        "prompt_tokens": 15,
        "completion_tokens": 42,
        "duration_ms": 1200
    }
}
```

> **Important**: All timestamps MUST use ISO8601 format with UTC timezone and the "Z" suffix. For details on timestamp handling, see the [Timestamp Guidelines](/docs/developers/timestamps.md).

## Trace Context Management

Events are automatically associated with the current trace context:

```python
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event

# Get current trace context
context = TraceContext.get_current_context()
print(f"Current trace ID: {context.get('trace_id')}")

# Events inherit the current trace context
log_event(
    name="custom.checkpoint",
    attributes={"checkpoint": "validation_complete"}
)
```

For more information on trace context, see the [Tracing](tracing.md) documentation.

## Error Logging

Errors can be logged with additional details:

```python
from cylestio_monitor.utils.event_logging import log_error

try:
    # Attempt an operation
    result = process_data()
except Exception as e:
    # Log the error with context
    log_error(
        name="data.processing.error",
        error=e,
        attributes={
            "data_source": "customer_database",
            "operation": "data_validation"
        }
    )
```

## Advanced Usage

### Function Instrumentation

You can automatically instrument functions to create events:

```python
from cylestio_monitor.utils.instrumentation import instrument_function

@instrument_function
def process_data(source, options=None):
    # This function is automatically instrumented
    # Events will be created at start and end
    result = transform_data(source, options)
    return result
```

### Error Handling

Combine error logging with proper trace context:

```python
from cylestio_monitor.utils.instrumentation import Span
from cylestio_monitor.utils.event_logging import log_error

def process_data(source):
    with Span("data.processing", attributes={"source": source}):
        try:
            # Process data
            result = transform(source)
            return result
        except Exception as e:
            # Log error with current span context
            log_error(
                name="data.processing.error",
                error=e,
                attributes={"source": source}
            )
            # Re-raise or handle as needed
            raise
```

## Configuring Event Logging

Event logging behavior can be configured when starting monitoring:

```python
import cylestio_monitor

cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "log_file": "output/events.json",  # Save events to a file
        "api_endpoint": "https://api.example.com/events",  # Send to remote API
        "debug_level": "INFO"  # Set logging level
    }
)
```

## Best Practices

1. **Use Descriptive Event Names**: Follow the `category.operation.result` pattern
2. **Include Relevant Attributes**: Add data that helps with debugging and analysis
3. **Handle Errors**: Log errors with sufficient context
4. **Manage Trace Context**: Use spans to create proper hierarchical relationships
5. **Avoid Sensitive Data**: Don't include PII or secrets in event attributes
