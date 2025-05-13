# Cylestio Monitor

A comprehensive security and monitoring solution for AI agents with OpenTelemetry-compliant telemetry. Cylestio Monitor provides lightweight, drop-in security monitoring for LLM clients and frameworks with just two lines of code.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/dependency-review.yml)

## Overview

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents with OpenTelemetry-compliant telemetry. While it works as a standalone solution, it integrates seamlessly with the Cylestio UI and smart dashboards for enhanced visibility and security monitoring across your entire agentic workforce.

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

### Security Pipeline

Cylestio Monitor maintains security through a comprehensive security pipeline that includes:

- **Dependency scanning**: Automated scanning for vulnerable dependencies using pip-audit to detect and remediate known CVEs
- **OWASP Dependency Check**: In-depth analysis of dependencies against the OWASP Top 10 and known CVEs
- **Secret detection**: Detection of potential leaked credentials or API keys with detect-secrets across the entire codebase
- **Static analysis**: Code vulnerability scanning with Semgrep and Bandit to identify security anti-patterns
- **Secure package validation**: Verification that packages don't contain sensitive information before publishing
- **Pre-commit hooks**: Local security checks before code is committed to prevent security issues from entering the codebase
- **Secure cryptography**: Using SHA-256 instead of MD5 for all hash generation to comply with cryptographic best practices
- **Input validation**: Strict validation of inputs, including URLs and timestamps, to prevent injection vulnerabilities
- **Error handling**: Comprehensive error handling to ensure security operations don't fail silently

This security pipeline is designed to help organizations meet regulatory and compliance requirements including SOC2, GDPR, HIPAA, and industry best practices for machine learning systems. The pipeline is continuously monitored and updated to address emerging security threats specific to AI and LLM systems.

For more details on our security approach and best practices, see [our security documentation](docs/security/security.md).

## Development

This repository uses pre-commit hooks to ensure code quality and security:

```bash
# Install pre-commit
pip install pre-commit

# Set up the git hooks
pre-commit install
```

After installation, the hooks will run automatically on `git commit`.

## Compliance for Agentic Workforces

Cylestio Monitor enables organizations to maintain regulatory compliance as they transition to agentic workforces. The system:

- **Monitors agent activities** across all interactions with LLM providers
- **Detects sensitive data** including PII, credentials, and regulated information
- **Alerts on potential prompt injections** and other security vulnerabilities
- **Maintains comprehensive audit trails** for all agent operations
- **Automatically masks sensitive data** in logs and telemetry

The monitoring system itself is designed with compliance in mind, ensuring all sensitive data is properly masked in logs and events. Security patterns and detection rules are fully configurable to match your organization's specific compliance requirements.

## Example Use Cases

For practical implementations of Cylestio Monitor in various agent architectures, check out the [Cylestio Use Cases repository](https://github.com/cylestio/usecases), which includes working examples such as:

- **CustomerSuccessAgent**: A customer service agent with SQLite integration and comprehensive monitoring
- **WeatherAgent**: A weather forecast agent using the National Weather Service API via MCP
- Additional examples demonstrating different agent patterns and monitoring scenarios

Each example demonstrates how to integrate Cylestio monitoring with just a few lines of code:

```python
import cylestio_monitor

cylestio_monitor.start_monitoring(
    agent_id="agent-name",
    config={
        "log_file": "output/monitoring.json",
        "debug_level": "DEBUG"
    }
)

# Your agent code here...

cylestio_monitor.stop_monitoring()
```

## Version History

Latest release: v0.1.12 (May 13, 2025)

Highlights:
- Implemented comprehensive security pipeline with pip-audit, OWASP Dependency Check, detect-secrets, and Semgrep
- Enhanced cryptographic security by replacing MD5 with SHA-256
- Improved URL validation to prevent file scheme vulnerabilities
- Added secure random number generation for span IDs
- Fixed error handling in patchers and utility functions

Previous releases:
- v0.1.11 (May 12, 2025): Fixed token usage tracking and improved error reporting
- v0.1.10 (May 12, 2025): Added configurable telemetry endpoint
- v0.1.9 (May 5, 2025): Reimplemented MCP patching with version-specific signatures
- v0.1.8 (May 5, 2025): Fixed MCP patching compatibility for tool call monitoring
- v0.1.7 (May 1, 2025): Added compatibility layer for various framework versions
- v0.1.6 (April 30, 2025): Added OpenAI API support and enhanced LangChain integration

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

Apache License 2.0

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
