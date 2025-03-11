# Cylestio Monitor

A comprehensive security and monitoring solution for AI agents. Cylestio Monitor provides lightweight, drop-in security monitoring for various frameworks, including Model Context Protocol (MCP) and popular LLM providers.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml)

## Overview

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents. While it works as a standalone solution, it integrates seamlessly with the Cylestio UI and smart dashboards for enhanced user experience and additional security and monitoring capabilities across your entire agentic workforce.

**For full documentation, visit [https://docs.cylestio.com](https://docs.cylestio.com)**

## Installation

```bash
pip install cylestio-monitor
```

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

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **Multi-framework support**: Works with popular LLM clients and frameworks including Model Context Protocol (MCP)
- **Security monitoring**: Detects and blocks dangerous prompts
- **Performance tracking**: Monitors call durations and response times
- **Structured logging**: Events stored in SQLite with optional JSON output

## Security Features

- **Prompt injection detection**: Identify and block malicious prompt injection attempts
- **PII detection**: Detect and redact personally identifiable information
- **Content filtering**: Filter out harmful or inappropriate content
- **Security rules**: Define custom security rules for your specific use case

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## Documentation

For complete documentation, including detailed guides, API reference, and best practices, visit:

**[https://docs.cylestio.com](https://docs.cylestio.com)**

## License

MIT
