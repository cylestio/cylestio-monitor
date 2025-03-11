# Events System

The Cylestio Monitor Events System provides a comprehensive framework for capturing, processing, and responding to events in your AI agent ecosystem.

## Overview

The Events System consists of two main components:

1. **Events Listener**: Captures events from your AI agents
2. **Events Processor**: Processes and routes events to appropriate handlers

This modular design allows for flexible event handling and custom integrations.

## Event Types

Cylestio Monitor captures several types of events:

| Event Type | Description |
|------------|-------------|
| `request` | Outgoing requests to LLM providers |
| `response` | Incoming responses from LLM providers |
| `error` | Errors that occur during agent operation |
| `security` | Security-related events (suspicious or dangerous content) |
| `system` | System-level events (startup, shutdown, etc.) |
| `custom` | Custom events defined by your application |

## Using the Events System

### Basic Usage

The Events System is automatically enabled when you use the `enable_monitoring` function:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_agent",
    llm_client=client
)
```

### Custom Event Handlers

You can register custom event handlers to process specific event types:

```python
from cylestio_monitor import register_event_handler

# Define a custom handler
def my_security_handler(event):
    if event.type == "security" and event.severity == "high":
        # Take action (e.g., send alert)
        send_alert(event)
    
    # Return True to continue processing, False to stop
    return True

# Register the handler
register_event_handler(
    event_type="security",
    handler=my_security_handler,
    priority=10  # Lower numbers run first
)
```

### Emitting Custom Events

You can emit custom events from your application:

```python
from cylestio_monitor import emit_event

# Emit a custom event
emit_event(
    event_type="custom",
    agent_id="my_agent",
    data={
        "action": "user_login",
        "user_id": "12345",
        "timestamp": "2024-03-11T12:34:56Z"
    },
    severity="info"
)
```

## Event Structure

Each event has the following structure:

```python
{
    "id": "evt_123456789",           # Unique event ID
    "type": "request",               # Event type
    "agent_id": "my_agent",          # Agent ID
    "timestamp": "2024-03-11T12:34:56Z", # ISO timestamp
    "severity": "info",              # Event severity
    "data": {                        # Event-specific data
        # Varies by event type
    },
    "metadata": {                    # Additional metadata
        "source": "anthropic",
        "version": "1.0.0"
    }
}
```

## Event Channels

Events can be routed to different channels for processing. See the [Monitoring Channels](../monitoring_channels.md) documentation for more details.

## Advanced Usage

### Filtering Events

You can filter events before they're processed:

```python
from cylestio_monitor import register_event_filter

def my_filter(event):
    # Only process events from specific agents
    if event.agent_id in ["agent1", "agent2"]:
        return True
    return False

register_event_filter(my_filter)
```

### Batch Processing

For high-volume applications, you can enable batch processing:

```python
from cylestio_monitor import configure_events

configure_events(
    batch_size=100,           # Process events in batches of 100
    batch_interval_ms=1000,   # Process at least every 1000ms
    max_queue_size=10000      # Maximum queue size
)
```

## Performance Considerations

- Event handlers should be lightweight and non-blocking
- For intensive processing, consider using background workers
- Use batch processing for high-volume applications
- Monitor queue size to prevent memory issues

## Next Steps

- Learn about [Event Listeners](events-listener.md) for capturing events
- Explore [Event Processors](events-processor.md) for handling events
- See [Monitoring Channels](../monitoring_channels.md) for routing events 