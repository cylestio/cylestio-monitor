# Cylestio Monitor SDK

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents with OpenTelemetry-compliant telemetry. It offers lightweight, drop-in security monitoring for various frameworks, including Model Context Protocol (MCP) and popular LLM providers.

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **Multi-framework support**: Works with popular LLM clients and frameworks including Model Context Protocol (MCP), LangChain, and LangGraph
- **OpenTelemetry compliance**: Generate structured telemetry with trace context for distributed tracing
- **Security monitoring**: Detects and flags suspicious or dangerous content
- **Performance tracking**: Monitors call durations and response times
- **Hierarchical operation tracking**: Understand relationships between operations with spans and trace context
- **Flexible logging**: Send events to a remote API endpoint with optional JSON file backup

## Quick Start

```python
from cylestio_monitor import start_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Start monitoring with API endpoint
start_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "output/monitoring.json"
    }
)

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# Stop monitoring when done
from cylestio_monitor import stop_monitoring
stop_monitoring()
```

## OpenTelemetry-Compliant Event Structure

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

## Integration with Cylestio Ecosystem

While Cylestio Monitor works as a standalone solution, it integrates seamlessly with the Cylestio UI and smart dashboards for enhanced user experience and additional security and monitoring capabilities across your entire agentic workforce.

## Documentation Sections

- [Getting Started](getting-started/quick-start.md): Basic setup and configuration
- [SDK Reference](sdk-reference/overview.md): Detailed API documentation
- [Security](security/best-practices.md): Security features and best practices
- [Advanced Topics](advanced-topics/custom-integrations.md): Advanced usage and customization
- [Development](development/contributing.md): Contributing to the project
- [Troubleshooting](troubleshooting/common-issues.md): Common issues and solutions 