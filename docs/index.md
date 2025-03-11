# Cylestio Monitor SDK

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents. It offers lightweight, drop-in security monitoring for various frameworks, including Model Context Protocol (MCP) and popular LLM providers.

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **Multi-framework support**: Works with popular LLM clients and frameworks including Model Context Protocol (MCP)
- **Security monitoring**: Detects and blocks dangerous prompts
- **Performance tracking**: Monitors call durations and response times
- **Structured logging**: Events stored in SQLite with optional JSON output

## Quick Start

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

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
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