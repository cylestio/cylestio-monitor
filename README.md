# Cylestio Monitor

A comprehensive security and monitoring solution for AI agents with OpenTelemetry-compliant telemetry. Cylestio Monitor provides lightweight, drop-in security monitoring for various frameworks, including Model Context Protocol (MCP), LangChain, LangGraph, and popular LLM providers.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml)

## Overview

Cylestio Monitor is a Python SDK that provides security and monitoring capabilities for AI agents with OpenTelemetry-compliant telemetry. While it works as a standalone solution, it integrates seamlessly with the Cylestio UI and smart dashboards for enhanced user experience and additional security and monitoring capabilities across your entire agentic workforce.

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
from cylestio_monitor import start_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Start monitoring with a remote API endpoint
start_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://your-api-endpoint.com/events",
        "log_file": "output/monitoring.json"  # Optional local JSON logging
    }
)

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# When finished, stop monitoring
from cylestio_monitor import stop_monitoring
stop_monitoring()
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

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **OpenTelemetry compliance**: Generate structured telemetry with trace context for distributed tracing
- **Multi-framework support**: Works with popular LLM clients and frameworks including Model Context Protocol (MCP), LangChain, and LangGraph
- **Hierarchical operation tracking**: Understand relationships between operations with spans and trace context
- **Complete request-response tracking**: Captures both outgoing LLM requests and incoming responses 
- **Security monitoring**: Detects and flags suspicious or dangerous content
- **Performance tracking**: Monitors call durations and response times
- **Flexible storage options**: Events can be sent to a remote API endpoint or stored locally in JSON files

## Trace Context Management

Cylestio Monitor automatically manages trace context following OpenTelemetry standards:

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

## Security Features

- **Content safety monitoring**: Identify potentially suspicious or dangerous content
- **PII detection**: Detect and redact personally identifiable information
- **Content filtering**: Flag harmful or inappropriate content
- **Security classification**: Events are automatically classified by security risk level

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
│       └── utils/             # Utility functions and trace context management
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

Cylestio Monitor uses a comprehensive testing approach with custom tooling to ensure consistent test execution across different environments. 

### Running Tests

We recommend using our custom test runner which handles dependency mocking and environment setup:

```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --cov=src --cov-report=term-missing

# Run specific tests
python tests/run_tests.py tests/test_api_client.py

# Run tests with specific markers
python tests/run_tests.py -m "integration"
```

This approach ensures that tests run consistently regardless of the environment or installed dependencies. See [docs/TESTING.md](docs/TESTING.md) for detailed information about our testing approach.

## API Client

The Cylestio Monitor uses a lightweight REST API client to send OpenTelemetry-compliant telemetry events to a remote endpoint. This approach offers several advantages:

- **Centralized Event Storage**: All events from different agents can be collected in a central location
- **Real-time Monitoring**: Events are sent in real-time to the API for immediate analysis
- **Minimal Storage Requirements**: No local database maintenance required
- **Distributed Tracing**: Trace context propagation enables end-to-end visibility
- **Scalability**: Easily scale monitoring across multiple agents and applications

The API client can be configured by providing an endpoint URL either through the `api_endpoint` configuration parameter or by setting the `CYLESTIO_API_ENDPOINT` environment variable.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## Documentation

For complete documentation, including detailed guides, API reference, and best practices, visit:

**[https://docs.cylestio.com](https://docs.cylestio.com)**

## License

MIT
