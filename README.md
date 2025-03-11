# Cylestio Monitor

A lightweight, drop-in monitoring SDK for AI agents, MCP, and LLM API calls.

## Overview

Cylestio Monitor intercepts key MCP and LLM calls and logs call parameters, durations, and responses as structured JSON events. Each event includes a severity flag ("alert") if suspicious or dangerous terms are detected. Dangerous prompts are blocked, while suspicious ones are flagged for review.

## Features

- **Zero-configuration setup**: Just import and enable monitoring
- **Automatic framework detection**: Works with MCP and popular LLM clients
- **Security monitoring**: Detects and blocks dangerous prompts
- **Structured logging**: All events are logged in a structured JSON format
- **Performance tracking**: Monitors call durations and response times
- **Global SQLite database**: Stores all events in a shared, OS-agnostic location

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

## Documentation

For full documentation, visit [cylestio.github.io/cylestio-monitor](https://cylestio.github.io/cylestio-monitor/).

## License

MIT

## Development Setup

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

## Security & Compliance

For compliance with SOC2, GDPR, and HIPAA requirements:
- Never commit credentials or secrets
- Never commit PII or PHI data
- Address security vulnerabilities promptly
- Run security checks before commits: `pre-commit run --all-files`
