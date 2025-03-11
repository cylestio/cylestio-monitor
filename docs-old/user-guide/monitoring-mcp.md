# Model Context Protocol (MCP) Integration

## About Model Context Protocol

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open standard for AI agents to interact with tools, interfaces, and capabilities. It enables LLMs to use tools, call APIs, interact with the user, and access system resources in a standardized way.

Cylestio Monitor provides comprehensive monitoring for MCP-based AI agents as part of our broader AI monitoring ecosystem.

## Setup for MCP Projects

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

# Enable monitoring before creating your MCP session
enable_monitoring(agent_id="mcp-project")

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

## What Gets Monitored

### Tool Call Request Data
- Tool name
- Tool arguments
- Timestamp
- Security check results

### Tool Call Response Data
- Tool result
- Duration
- Error information

## Security Checks

- **Suspicious Content**: Flagged but allowed to proceed
- **Dangerous Content**: Blocked by default

## Example Events

### MCP Tool Call Start Event

```json
{
  "event": "MCP_tool_call_start",
  "data": {
    "tool": "weather",
    "args": {
      "location": "New York"
    },
    "alert": "none"
  },
  "timestamp": "2024-03-10T22:15:30.123456",
  "channel": "MCP"
}
```

### MCP Tool Call Finish Event

```json
{
  "event": "MCP_tool_call_finish",
  "data": {
    "tool": "weather",
    "duration_ms": 234,
    "result": {
      "temperature": 72,
      "conditions": "Sunny",
      "location": "New York, NY"
    }
  },
  "timestamp": "2024-03-10T22:15:30.654321",
  "channel": "MCP"
}
```

## Accessing MCP Events

```python
from cylestio_monitor.db import utils as db_utils

# Get all MCP events for a specific agent
mcp_events = db_utils.get_events_by_channel("MCP", agent_id="my-project")

# Get MCP tool call start events
start_events = db_utils.get_events_by_type("MCP_tool_call_start", agent_id="my-project")

# Get MCP tool call finish events
finish_events = db_utils.get_events_by_type("MCP_tool_call_finish", agent_id="my-project")

# Get blocked MCP tool calls
blocked_events = db_utils.get_events_by_type("MCP_tool_call_blocked", agent_id="my-project")
```

## Advanced Configuration for MCP

For more advanced configuration options specific to MCP monitoring, see our [Configuration Guide](../getting-started/configuration.md#mcp-specific-configuration).

## Additional Frameworks

Cylestio Monitor also supports other AI frameworks and LLM providers. See our [Framework Support](frameworks/index.md) documentation for details on all available integrations.

## Tool-Specific Analysis

You can analyze tool usage patterns: