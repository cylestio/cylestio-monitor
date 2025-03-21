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

### Installation for Example Projects

If you're using one of the example projects in a subdirectory with its own virtual environment:

```bash
# Navigate to the example directory 
cd examples/agents/your_agent_dir

# Activate your virtual environment
source venv/bin/activate  # (or venv\Scripts\activate on Windows)

# Install the Cylestio Monitor from the parent directory in development mode
pip install -e ../../..
```

## Quick Start

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring with a remote API endpoint
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://your-api-endpoint.com/events"
    }
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
- **Complete request-response tracking**: Captures both outgoing LLM requests and incoming responses 
- **Security monitoring**: Detects and blocks dangerous prompts
- **Performance tracking**: Monitors call durations and response times
- **Flexible storage options**: Events can be sent to a remote API endpoint or stored locally in JSON files

## Security Features

- **Prompt injection detection**: Identify and block malicious prompt injection attempts
- **PII detection**: Detect and redact personally identifiable information
- **Content filtering**: Filter out harmful or inappropriate content
- **Security rules**: Define custom security rules for your specific use case

## Framework Support

Cylestio Monitor supports:

- **Direct API calls**: Anthropic, Claude models (all versions)
- **LangChain**: Chains, agents, and callbacks
- **LangGraph**: Graph-based agents and workflows 
- **MCP (Model Context Protocol)**: Tool calls and responses

See [docs/compatibility.md](docs/compatibility.md) for the full compatibility matrix.

## Repository Structure

The Cylestio Monitor repository is organized as follows:

```
cylestio-monitor/
├── src/                       # Source code for the Cylestio Monitor package
│   └── cylestio_monitor/      # Main package
│       ├── patchers/          # Framework-specific patchers (Anthropic, MCP, etc.)
│       ├── events/            # Event definitions and processing
│       ├── config/            # Configuration management
│       └── utils/             # Utility functions
├── examples/                  # Example implementations
│   └── agents/                # Various agent examples demonstrating integration
├── tests/                     # Test suite
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
└── docs/                      # Documentation
    ├── compatibility.md       # Framework compatibility information
    ├── getting-started/       # Getting started guides
    ├── advanced-topics/       # Advanced usage documentation
    └── sdk-reference/         # API reference documentation
```

## Testing

For the MVP release, we focus on testing core functionality while excluding non-critical edge cases. The testing strategy includes:

1. **Core Functionality Tests**: These are critical tests that verify essential features of the monitoring system:
   - API client functionality
   - Configuration management
   - Security features (keyword detection, text normalization)
   - Monitoring functionality
   - Patchers for LLM providers (Anthropic, etc.)
   - Event processing and analysis

2. **Running Critical Tests**:
   To run only the critical tests needed for the MVP:
   ```bash
   python -m pytest tests/test_import.py tests/test_config_manager.py tests/test_api_client.py tests/test_security.py tests/test_monitor.py::test_enable_monitoring_import_error tests/test_patchers_anthropic.py::test_anthropic_patcher_init tests/test_events_processor.py::test_normalize_text -v
   ```

3. **Test Coverage**:
   - Critical tests for MVP: ~30 tests
   - Total test suite: 350+ tests (including edge cases and advanced features)

4. **Running All Tests**:
   To run the complete test suite (including tests that might fail due to edge cases):
   ```bash
   python -m pytest tests/
   ```

## API Client

The Cylestio Monitor now uses a lightweight REST API client to send telemetry events to a remote endpoint instead of storing them in a local database. This approach offers several advantages:

- **Centralized Event Storage**: All events from different agents can be collected in a central location
- **Real-time Monitoring**: Events are sent in real-time to the API for immediate analysis
- **Minimal Storage Requirements**: No local database maintenance required
- **Scalability**: Easily scale monitoring across multiple agents and applications

The API client can be configured by providing an endpoint URL either through the `api_endpoint` configuration parameter or by setting the `CYLESTIO_API_ENDPOINT` environment variable.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## Documentation

For complete documentation, including detailed guides, API reference, and best practices, visit:

**[https://docs.cylestio.com](https://docs.cylestio.com)**

## License

MIT
