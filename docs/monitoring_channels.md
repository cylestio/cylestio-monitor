# Monitoring Channels

Monitoring channels provide a way to organize and route events in Cylestio Monitor, working alongside OpenTelemetry trace context to create a complete picture of your agent's activities.

## Overview

Channels act as logical groupings for events, allowing you to:

- Filter events by channel
- Apply different processing rules to different channels
- Route events to different destinations
- Configure channel-specific settings

## Built-in Channels

Cylestio Monitor includes several built-in channels:

| Channel | Description |
|---------|-------------|
| `SYSTEM` | System-level events (startup, shutdown, configuration changes) |
| `LLM` | Events related to LLM API calls (requests, responses) |
| `SECURITY` | Security-related events (suspicious or dangerous content) |
| `MCP` | Events related to Model Context Protocol operations |
| `API` | API client events (event submission, connectivity) |
| `FRAMEWORK` | Framework-specific events (LangChain, LangGraph) |

## Event Names by Channel

Events follow a consistent naming pattern with prefixes indicating their channel:

### LLM Channel
- `llm.request` - LLM API request event
- `llm.response` - LLM API response event
- `llm.call.start` - Start of an LLM call
- `llm.call.finish` - Completion of an LLM call

### SYSTEM Channel
- `monitoring.start` - Monitoring initialization
- `monitoring.stop` - Monitoring shutdown
- `framework.initialization` - Framework detection and initialization

### SECURITY Channel
- `security.content.suspicious` - Detection of suspicious content
- `security.content.dangerous` - Detection of dangerous content

### MCP Channel
- `mcp.request` - MCP request event
- `mcp.response` - MCP response event
- `mcp.call.start` - Start of MCP tool call
- `mcp.call.finish` - Completion of MCP tool call

## Working with Channels

### Event Logging with Channels

When logging events, the channel is determined by the event name:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log an event in the custom channel
log_event(
    name="custom.operation.start",
    attributes={"operation_type": "data_processing"},
    level="INFO"
)
```

### Filtering Events by Channel

When analyzing logs, you can filter events by their name prefix:

```bash
# Filter logs for security events
grep "security" monitoring.json

# Filter logs for LLM events
grep "llm" monitoring.json
```

## Channel and Trace Context

Channels work alongside trace context to provide a complete picture:

- **Channels** - Categorize events by type or subsystem
- **Trace Context** - Connect related events hierarchically, regardless of channel

This combination allows you to both:
1. Group similar events (via channels)
2. Track operational flows and relationships (via trace context)

## Channel Output Configuration

You can configure how events from different channels are handled:

### Configuration via API Endpoint

When using the API endpoint, all events are sent to the same endpoint, but can be filtered server-side based on channel.

### Configuration via Log File

When using log file output, all events are written to the same log file. You can use log analysis tools to filter by channel as needed.

## Best Practices

- Use consistent naming patterns for custom events (e.g., `custom.category.operation`)
- Leverage trace context and spans for tracking operation flows
- Use appropriate log levels for different types of events:
  - `DEBUG` - Detailed debugging information
  - `INFO` - Normal operational events
  - `WARNING` - Issues that might need attention
  - `ERROR` - Errors that prevent normal operation
  - `CRITICAL` - Critical failures requiring immediate attention

## Integrating with Log Analysis Tools

The OpenTelemetry-compliant event structure makes it easy to integrate with log analysis tools:

- **Trace ID** and **Span ID** fields enable distributed tracing visualization
- **Channel** prefixes in event names allow for logical grouping
- **Attributes** provide detailed filtering capabilities

## Next Steps

- Learn about the [Events System](sdk-reference/events.md)
- Explore [Trace Context](sdk-reference/monitor.md#trace-context) for connecting related events 