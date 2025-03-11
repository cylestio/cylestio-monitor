# Quick Start Guide

Get Cylestio Monitor up and running in your AI agent project in minutes.

## Basic Setup

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

# Use your client as normal - monitoring happens automatically
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

With just these few lines of code, Cylestio Monitor will:

- Track all LLM API calls
- Log request and response data
- Monitor for security threats
- Record performance metrics
- Store events in a queryable database

## Monitoring with JSON Logging

If you prefer to also log events to JSON files for external processing:

```python
# Enable monitoring with both SQLite and JSON logging
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/monitoring.json"
)

# Or log to a directory (a timestamped file will be created)
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/"
)
```

## Monitoring MCP

For Multi-Component Programs (MCP), enable monitoring before creating your session:

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

# Enable monitoring before creating your MCP session
enable_monitoring(agent_id="mcp-project")

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

## Accessing Monitoring Data

Query the monitoring database to analyze interactions:

```python
from cylestio_monitor import get_database_path
from cylestio_monitor.db import utils as db_utils

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get events by type
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get events from the last 24 hours
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")
```

## Visualizing Data with the Dashboard

To see monitoring data in our interactive dashboard, install the separate dashboard package:

```bash
pip install cylestio-dashboard
```

Run it with:

```bash
cylestio-dashboard
```

Visit `http://localhost:8501` to access the dashboard.

## Disabling Monitoring

When you're done, you can disable monitoring:

```python
from cylestio_monitor import disable_monitoring

# Disable monitoring
disable_monitoring()
```

## Next Steps

- Learn about [configuration options](configuration.md)
- Explore the [security features](../user-guide/security-features.md)
- Check out the [API reference](../api-reference/overview.md) 