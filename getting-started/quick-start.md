# Quick Start Guide for AI Agent Developers

This guide will help you quickly integrate Cylestio Monitor into your AI agent project to gain comprehensive security and performance monitoring.

## Common Use Cases

- **Development-time Protection**: Monitor and secure your AI agents during development
- **Production Monitoring**: Continuously monitor deployed AI agents
- **Security Compliance**: Generate audit logs and security reports
- **Performance Analysis**: Track response times and resource usage

## Basic Setup

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring with API endpoint
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)

# Use your client as normal - monitoring happens automatically
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

With just these few lines of code, Cylestio Monitor will:

- Track all AI interactions
- Log request and response data
- Monitor for security threats
- Record performance metrics
- Send events to the configured API endpoint

## Monitoring with JSON Logging

If you prefer to also log events to JSON files for local backup:

```python
# Enable monitoring with API and JSON logging
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/path/to/logs/monitoring.json"
    }
)

# Or log to a directory (a timestamped file will be created)
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/path/to/logs/"
    }
)
```

## Monitoring Different Frameworks

### Model Context Protocol (MCP)

For [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), enable monitoring before creating your session:

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

# Enable monitoring before creating your MCP session
enable_monitoring(
    agent_id="mcp-project",
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

### OpenAI Client

```python
from openai import OpenAI
from cylestio_monitor import enable_monitoring

# Create your OpenAI client
client = OpenAI()

# Enable monitoring
enable_monitoring(
    agent_id="openai-project", 
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)

# Use your client as normal
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, world!"}]
)
```

### Custom Frameworks

For additional frameworks or custom integrations, see our [Framework Support](../user-guide/frameworks/index.md) documentation.

## Manually Sending Events

You can manually send events to the API using the API client:

```python
from cylestio_monitor.api_client import send_event_to_api

# Send a custom event
send_event_to_api(
    agent_id="my-agent",
    event_type="custom-event",
    data={
        "message": "Something interesting happened",
        "custom_field": "custom value"
    },
    channel="CUSTOM",
    level="info"
)
```

## Checking API Endpoint

To check the configured API endpoint:

```python
from cylestio_monitor import get_api_endpoint

# Get the current API endpoint
endpoint = get_api_endpoint()
print(f"Sending events to: {endpoint}")
```

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
- Check out the [SDK reference](../sdk-reference/overview.md) 