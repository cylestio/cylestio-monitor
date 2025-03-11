# Cylestio Monitor

A lightweight, drop-in security and performance monitoring SDK for AI agents, [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), and LLM API calls.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml)
[![Documentation](https://github.com/cylestio/cylestio-monitor/actions/workflows/deploy_docs.yml/badge.svg)](https://cylestio.github.io/cylestio-monitor/)

## For Agent Developers

### Why Cylestio Monitor?

Cylestio Monitor provides essential oversight for AI agents by intercepting Model Context Protocol (MCP) and LLM API calls, logging critical parameters, and detecting security threats. Our monitoring solution helps you:

- **Secure your AI systems** by detecting and blocking dangerous prompts
- **Track performance metrics** with detailed call duration and response time data
- **Meet compliance requirements** with structured, audit-ready logging
- **Debug interactions** with comprehensive event data

All with minimal configuration and zero code changes to your existing agents.

### Installation

```bash
pip install cylestio-monitor
```

### Quick Start

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

### Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **Automatic framework detection**: Works with Model Context Protocol (MCP) and popular LLM clients
- **Security monitoring**: Detects and blocks dangerous prompts
- **Performance tracking**: Monitors call durations and response times
- **Structured logging**: Events stored in SQLite with optional JSON output
- **Dashboard integration**: View your monitoring data with our open source [visualization dashboard](https://github.com/cylestio/cylestio-dashboard)

### Visualization Dashboard

For an interactive visualization of your monitoring data, check out our separate [Cylestio Dashboard](https://github.com/cylestio/cylestio-dashboard) repository. This open source dashboard provides real-time metrics, alert views, and detailed event analysis.

## For Contributors

We welcome contributions to the Cylestio Monitor project! Whether you're fixing bugs, improving documentation, or adding new features, your help is appreciated.

### Development Setup

1. Ensure you have Python 3.11+ installed
2. Clone the repository:
   ```bash
   git clone https://github.com/cylestio/cylestio-monitor.git
   cd cylestio-monitor
   ```

3. Create and activate virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -e ".[dev,test,security]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type pre-push
   ```

### Contribution Guidelines

- **Code Style**: We use Black, isort, and ruff for code formatting
- **Testing**: All new features and bug fixes must include tests
- **Documentation**: Update relevant docs for any changes you make
- **Security**: Follow security best practices in all code
- **Commit Messages**: Use conventional commits format (`type(scope): message`)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## Documentation

For full documentation, visit [cylestio.github.io/cylestio-monitor](https://cylestio.github.io/cylestio-monitor/).

## License

MIT
