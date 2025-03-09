# Cylestio Monitor

A powerful open-source monitoring solution for AI agents, providing real-time event logging, security intelligence, and performance tracking with Model Context Protocol (MCP) support.

## Overview

Cylestio Monitor is designed to seamlessly integrate with various AI frameworks and tools, offering comprehensive monitoring capabilities through dynamic function patching and MCP integration. It captures events, logs, and performance metrics while performing security checks on prompts and responses, making it ideal for enterprise AI deployments.

## Features

- **Real-Time Event Logging**: 
  - Capture detailed metrics about LLM calls, tool usage, and system events
  - Track token usage, response times, and model performance
  - Monitor tool invocations and their outcomes
  
- **Security Intelligence**: 
  - Detect dangerous keywords and patterns
  - Identify potential security vulnerabilities
  - Block high-risk operations automatically
  - Comprehensive audit trails for compliance
  
- **Model Context Protocol Support**:
  - Full MCP client and server integration
  - Standardized context handling
  - Interoperable with MCP-compliant systems
  - Enhanced context management capabilities

- **Framework Agnostic**: Support for multiple frameworks through dedicated patchers:
  - Anthropic Client
  - Model Context Protocol
  - More frameworks coming soon...

- **Enterprise Features**:
  - Role-based access control
  - Audit logging
  - Performance analytics
  - Security compliance reporting

## Installation

```bash
pip install cylestio-monitor
```

## Quick Start

### Basic Usage

```python
from anthropic import Anthropic
from cylestio_monitor import patch_anthropic_client

# Initialize your Anthropic client
client = Anthropic()

# Patch the client with Cylestio monitoring
patch_anthropic_client(client)

# Use the client as normal - all calls will be monitored
response = client.messages.create(
    model="claude-3-opus-20240229",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### MCP Integration

```python
from cylestio_monitor.mcp import MCPClient, MCPServer

# Initialize MCP client
client = MCPClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Create a monitored context
context = client.create_context({
    "messages": [
        {"role": "user", "content": "Hello!"}
    ]
})

# Get response with full monitoring
response = client.get_completion(context)
```

## Architecture

The monitoring system consists of several key components:

1. **Patchers**: Framework-specific modules that intercept and monitor function calls
2. **Event Listeners**: Capture and process events in real-time
3. **Event Processors**: Handle logging and security checks
4. **Security Analyzer**: Evaluates prompts and responses for potential risks
5. **MCP Integration**: Handles Model Context Protocol compatibility
6. **Analytics Engine**: Processes and visualizes monitoring data

## Security & Compliance

- Enterprise-grade security measures
- SOC 2 compliance ready
- GDPR and CCPA compliant
- Regular security audits
- Comprehensive access controls

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) file for details

## Documentation

Full documentation is available at [docs.cylestio.com](https://docs.cylestio.com)

## Contact

- Website: [cylestio.com](https://cylestio.com)
- Email: support@cylestio.com
- GitHub: [github.com/cylestio](https://github.com/cylestio)
