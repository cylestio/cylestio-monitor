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

## Filtering Events by Channel

You can filter events by channel when querying the database:

```python
from cylestio_monitor.db import utils as db_utils

# Get all LLM events
llm_events = db_utils.get_events_by_channel("LLM")

# Get all MCP events
mcp_events = db_utils.get_events_by_channel("MCP")

# Get all SYSTEM events
system_events = db_utils.get_events_by_channel("SYSTEM")
```

## Channel Distribution Analysis

You can analyze the distribution of events across channels:

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3

# Get the database connection
db_path = db_utils.get_db_path()
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Query for channel distribution
cursor = conn.execute("""
    SELECT channel, COUNT(*) as count
    FROM events
    WHERE agent_id = ?
    GROUP BY channel
    ORDER BY count DESC
""", ("my-project",))

# Print the results
for row in cursor:
    print(f"Channel: {row['channel']}, Count: {row['count']}")

conn.close()
```

## Best Practices for Using Channels

1. **Use the appropriate channel for each event**: This helps keep your monitoring data organized and makes it easier to filter and analyze.

2. **Create custom channels for specific components**: If you have a specific component or activity that generates a lot of events, consider creating a custom channel for it.

3. **Include the channel in your log analysis**: When analyzing logs, consider the channel as a key dimension for filtering and aggregation.

4. **Set up alerts based on channels**: You might want different alerting thresholds for different channels (e.g., more sensitive alerts for security-related channels).

5. **Document your custom channels**: If you create custom channels, make sure to document what they represent and what types of events they capture. 