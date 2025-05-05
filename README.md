# Cylestio Monitor

A comprehensive security and monitoring solution for AI agents with OpenTelemetry-compliant telemetry. Cylestio Monitor provides lightweight, drop-in security monitoring for LLM clients and frameworks with just two lines of code.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml)

## Overview

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents with OpenTelemetry-compliant telemetry. While it works as a standalone solution, it integrates seamlessly with the Cylestio UI and smart dashboards for enhanced visibility and security monitoring across your entire agentic workforce.

**For full documentation, visit [https://docs.cylestio.com](https://docs.cylestio.com)**

## Installation

```bash
pip install cylestio-monitor
```

## Quick Start

```python
import cylestio_monitor
from anthropic import Anthropic

# Start monitoring with minimal configuration
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Create your LLM client - it will be automatically patched
client = Anthropic()

# Use your client as normal - all calls are automatically monitored
response = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# When finished, stop monitoring
cylestio_monitor.stop_monitoring()

# All events will use ISO8601 format with UTC timezone and Z suffix
# e.g., "2024-03-27T15:31:40.622Z"
```

## How It Works

Cylestio Monitor works by automatically patching supported LLM clients and frameworks. No additional configuration is required - the SDK detects which libraries are available and applies the appropriate monitoring.

### Supported Frameworks

- **LLM Clients**:
  - Anthropic Claude (all versions)
  - OpenAI (Chat Completions and Completions APIs)
  - Additional LLM providers
- **Agent Frameworks**:
  - MCP (Model Context Protocol)
  - LangChain (v0.1.0+)
  - LangChain Core
  - LangChain Community
  - LangGraph

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **OpenTelemetry compliance**: Generate structured telemetry with trace context for distributed tracing
- **Multi-framework support**: Works with popular LLM clients and frameworks
- **Hierarchical operation tracking**: Understand relationships between operations with spans and trace context
- **Complete request-response tracking**: Captures both outgoing LLM requests and incoming responses
- **Security monitoring**: Detects and flags suspicious or dangerous content
- **Token usage tracking**: Monitor token consumption across supported providers
- **Tool execution monitoring**: Track tool calls and their execution details
- **Chain execution tracking**: Monitor LangChain chain execution with detailed metrics
- **Performance tracking**: Monitors call durations and response times
- **Flexible storage options**: Events can be sent to a remote API endpoint or stored locally in JSON files

## Configuration Options

The `start_monitoring` function accepts these configuration options:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",  # Required: unique identifier for your agent
    config={  # Optional: configuration dictionary
        "debug_level": "INFO",  # Logging level (DEBUG, INFO, WARNING, ERROR)
        "log_file": "output/my_logs.json",  # Path for local JSON logs
        "api_endpoint": "https://api.example.com/events",  # Remote endpoint
        "telemetry_endpoint": "http://custom.telemetry.server:9000",  # Custom telemetry host/port
        "development_mode": False  # Enable additional development features
    }
)
```

### Local Logging

By default, Cylestio Monitor logs events to a file when the `log_file` option is provided:

```python
cylestio_monitor.start_monitoring(
    agent_id="weather-agent",
    config={
        "log_file": "output/weather_monitoring.json"
    }
)
```

## OpenTelemetry Compliance

All events follow OpenTelemetry standards with trace context:

```json
{
    "timestamp": "2024-03-27T15:31:40.622Z",
    "trace_id": "2a8ec755032d4e2ab0db888ab84ef595",
    "span_id": "96d8c2be667e4c78",
    "parent_span_id": "f1490a668d69d1dc",
    "name": "llm.call.start",
    "attributes": {
        "method": "messages.create",
        "model": "claude-3-haiku-20240307"
    },
    "agent_id": "weather-agent"
}
```

## Security Features

- **Content safety monitoring**: Identify potentially suspicious or dangerous content
- **PII detection**: Detect and redact personally identifiable information
- **Content filtering**: Flag harmful or inappropriate content
- **Security classification**: Events are automatically classified by security risk level
- **Regulatory compliance**: Designed to help satisfy SOC2, GDPR, and HIPAA monitoring requirements
- **Audit-ready logging**: Generate detailed logs suitable for security audits and compliance verification

## Compliance for Agentic Workforces

Cylestio Monitor enables organizations to maintain regulatory compliance as they transition to agentic workforces. The system:

- **Monitors agent activities** across all interactions with LLM providers
- **Detects sensitive data** including PII, credentials, and regulated information
- **Alerts on potential prompt injections** and other security vulnerabilities
- **Maintains comprehensive audit trails** for all agent operations
- **Automatically masks sensitive data** in logs and telemetry

The monitoring system itself is designed with compliance in mind, ensuring all sensitive data is properly masked in logs and events. Security patterns and detection rules are fully configurable to match your organization's specific compliance requirements.

## Complete Example

The project includes several example agents with full integration:

- **Weather Agent**: Uses MCP and Anthropic Claude
- **RAG Agent**: Demonstrates retrieval-augmented generation
- **Chatbot**: Simple LLM-based chatbot

Example source: [examples/agents/weather_agent/weather_client.py](examples/agents/weather_agent/weather_client.py)

## Version History

Latest release: v0.1.10 (May 12, 2025)

Highlights:
- Added configurable telemetry endpoint to allow custom host/port configuration
- Improved error handling for endpoint connections
- Documentation improvements for configuration options

Previous releases:
- v0.1.9 (May 5, 2025): Reimplemented MCP patching with version-specific method signatures
- v0.1.8 (May 5, 2025): Fixed MCP patching compatibility issue for tool call monitoring
- v0.1.7 (May 1, 2025): Added compatibility layer for various framework versions
- v0.1.6 (April 30, 2025): Added OpenAI API support and enhanced LangChain integration

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

Apache License 2.0

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
