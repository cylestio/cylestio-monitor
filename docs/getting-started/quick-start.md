# Quick Start Guide for AI Agent Developers

This guide will help you quickly integrate Cylestio Monitor into your AI agent project to gain comprehensive security and performance monitoring with OpenTelemetry-compliant telemetry.

## Common Use Cases

- **Development-time Protection**: Monitor and secure your AI agents during development
- **Production Monitoring**: Continuously monitor deployed AI agents
- **Security Compliance**: Generate audit logs and security reports
- **Performance Analysis**: Track response times and resource usage
- **Operational Visibility**: Understand the flow of requests through your system with trace context

## Basic Setup

```python
from cylestio_monitor import start_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Start monitoring with API endpoint
start_monitoring(
    agent_id="my_agent",
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

# Stop monitoring when done
from cylestio_monitor import stop_monitoring
stop_monitoring()
```

With just these few lines of code, Cylestio Monitor will:

- Track all AI interactions with trace context
- Log request and response data
- Monitor for security threats
- Record performance metrics
- Send OpenTelemetry-compliant events to the configured API endpoint

## Monitoring with JSON Logging

If you prefer to also log events to JSON files for local backup:

```python
# Start monitoring with API and JSON logging
start_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/path/to/logs/monitoring.json"
    }
)

# Or log to a directory (a timestamped file will be created)
start_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "/path/to/logs/"
    }
)
```

## Monitoring Different Frameworks

### Model Context Protocol (MCP)

For [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), Cylestio Monitor automatically detects and patches MCP:

```python
from mcp import ClientSession
from cylestio_monitor import start_monitoring

# Start monitoring before creating your MCP session
start_monitoring(
    agent_id="mcp-project",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "output/monitoring.json"
    }
)

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

### LangChain and LangGraph

Cylestio Monitor can automatically detect and patch LangChain and LangGraph frameworks:

```python
import langchain
from langchain.chat_models import ChatAnthropic
from cylestio_monitor import start_monitoring

# Start monitoring with framework patching enabled (default)
start_monitoring(
    agent_id="langchain-agent",
    config={
        "log_file": "output/monitoring.json",
        "enable_framework_patching": True  # This is the default
    }
)

# Create and use LangChain components normally
model = ChatAnthropic(model="claude-3-sonnet-20240229")
result = model.invoke("What is the capital of France?")
```

## OpenTelemetry-Compliant Event Structure

Cylestio Monitor generates events following OpenTelemetry standards:

```json
{
    "timestamp": "2024-03-27T15:31:40.622017",
    "trace_id": "2a8ec755032d4e2ab0db888ab84ef595", 
    "span_id": "96d8c2be667e4c78",
    "parent_span_id": "f1490a668d69d1dc",
    "name": "llm.call.start",
    "level": "INFO",
    "attributes": {
        "method": "messages.create",
        "prompt": "Hello, world!",
        "model": "claude-3-sonnet-20240229"
    },
    "agent_id": "my-agent"
}
```

## Working with Trace Context

The trace context is automatically managed, but you can also work with it directly:

```python
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event

# Start a custom span for an operation
span_info = TraceContext.start_span("data-processing")

try:
    # Perform some operation
    result = process_data()
    
    # Log an event within this span
    log_event(
        name="custom.processing.complete",
        attributes={"records_processed": 100}
    )
finally:
    # Always end the span
    TraceContext.end_span()
```

## Manually Logging Events

You can manually log events using the event_logging utilities:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log a custom event
log_event(
    name="custom.event",
    attributes={
        "custom_field": "custom value",
        "operation": "user_login" 
    },
    level="INFO"
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

## Next Steps

- Learn about [configuration options](configuration.md)
- Explore the [security features](../advanced-topics/security.md)
- Check out the [SDK reference](../sdk-reference/overview.md) 