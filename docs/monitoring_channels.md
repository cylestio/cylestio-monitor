# Monitoring Channels in Cylestio Monitor

Cylestio Monitor categorizes events into different channels to help organize and filter monitoring data. Each channel represents a specific type of activity or component being monitored.

## Available Channels

### SYSTEM

The `SYSTEM` channel captures events related to the Cylestio Monitor SDK itself, such as:

- Initialization and shutdown events
- Configuration changes
- Patching of LLM and MCP clients
- Internal errors and warnings

Example events:
- `monitoring_enabled`: When monitoring is first enabled
- `monitoring_disabled`: When monitoring is disabled
- `LLM_patch`: When an LLM client is patched
- `MCP_patch`: When an MCP client is patched

### LLM (Large Language Model)

The `LLM` channel captures events related to interactions with Large Language Models, such as:

- LLM API calls
- Prompt content and parameters
- Response content and metadata
- Security alerts related to prompts and responses
- Performance metrics (duration, token usage)

Example events:
- `LLM_call_start`: When an LLM API call begins
- `LLM_call_finish`: When an LLM API call completes
- `LLM_call_blocked`: When an LLM API call is blocked due to security concerns

### API

The `API` channel captures events related to general API calls that are not specifically LLM-related, such as:

- External service API calls
- Authentication events
- Rate limiting events
- API errors and warnings

Example events:
- `API_call_start`: When an API call begins
- `API_call_finish`: When an API call completes
- `API_error`: When an API call fails

### MCP (Machine-Controlled Programs)

The `MCP` channel captures events related to MCP tool calls and interactions, such as:

- Tool registration and discovery
- Tool call parameters and arguments
- Tool call results and errors
- Security alerts related to tool calls

Example events:
- `MCP_tool_call_start`: When an MCP tool call begins
- `MCP_tool_call_finish`: When an MCP tool call completes
- `MCP_tool_call_error`: When an MCP tool call fails

## Extending Monitoring Channels

The monitoring system is designed to be extensible. You can add custom channels to monitor specific components or activities in your application:

1. Add the channel to the configuration file:
   ```yaml
   monitoring:
     channels:
       - "SYSTEM"
       - "LLM"
       - "API"
       - "MCP"
       - "MY_CUSTOM_CHANNEL"
   ```

2. Use the channel in your logging:
   ```python
   from cylestio_monitor.events_processor import log_event
   
   log_event("custom_event", {"key": "value"}, channel="MY_CUSTOM_CHANNEL")
   ```

## Channel-Specific Configuration

In future versions, Cylestio Monitor will support channel-specific configuration options, such as:

- Channel-specific logging levels
- Channel-specific security rules
- Channel-specific output destinations

This will allow for more granular control over monitoring behavior based on the type of activity being monitored. 