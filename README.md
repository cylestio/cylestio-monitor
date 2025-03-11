# Cylestio Monitor

A lightweight, drop-in monitoring SDK for AI agents, MCP, and LLM API calls.

[![PyPI version](https://badge.fury.io/py/cylestio-monitor.svg)](https://badge.fury.io/py/cylestio-monitor)
[![CI](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/ci.yml)
[![Security](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml/badge.svg)](https://github.com/cylestio/cylestio-monitor/actions/workflows/security.yml)
[![Documentation](https://github.com/cylestio/cylestio-monitor/actions/workflows/deploy_docs.yml/badge.svg)](https://cylestio.github.io/cylestio-monitor/)

## Overview

Cylestio Monitor intercepts key MCP and LLM calls and logs call parameters, durations, and responses as structured JSON events. Each event includes a severity flag ("alert") if suspicious or dangerous terms are detected. Dangerous prompts are blocked, while suspicious ones are flagged for review.

## Features

- **Zero-configuration setup**: Just import and enable monitoring
- **Automatic framework detection**: Works with MCP and popular LLM clients
- **Security monitoring**: Detects and blocks dangerous prompts
- **Structured logging**: All events are logged in a structured JSON format
- **Performance tracking**: Monitors call durations and response times
- **Global SQLite database**: Stores all events in a shared, OS-agnostic location
- **Compliance-ready**: Built with SOC2, GDPR, and HIPAA compliance in mind
- **Data masking**: Configurable masking of sensitive data
- **Extensible**: Easy to add support for additional LLM providers

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

## Configuration

Cylestio Monitor uses a global configuration file stored in a platform-specific location:

- **Linux**: `~/.config/cylestio-monitor/config.yaml`
- **macOS**: `~/Library/Application Support/cylestio-monitor/config.yaml`
- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\config.yaml`

The configuration file is automatically created on first run with default settings. You can modify it to customize the behavior of the SDK:

```yaml
# Security settings
security:
  # Keywords that will trigger a suspicious flag
  suspicious_keywords:
    - "hack"
    - "exploit"
    # ... more keywords
  
  # Keywords that will block the request
  dangerous_keywords:
    - "sql injection"
    - "cross-site scripting"
    # ... more keywords

# Data masking settings
data_masking:
  enabled: true
  patterns:
    - name: "credit_card"
      regex: "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b"
      replacement: "[CREDIT_CARD]"
    - name: "ssn"
      regex: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
      replacement: "[SSN]"
    # ... more patterns

# Database settings
database:
  retention_days: 30
  vacuum_on_startup: true
```

## Database

Cylestio Monitor stores all events in a SQLite database located in a platform-specific data directory:

- **Linux**: `~/.local/share/cylestio-monitor/monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/monitor.db`
- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\monitor.db`

You can access the database path programmatically:

```python
from cylestio_monitor import get_database_path

db_path = get_database_path()
print(f"Database is stored at: {db_path}")
```

## Querying Events

The SDK provides utilities for querying events from the database:

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events for a specific agent
events = db_utils.get_events(agent_id="my_agent", limit=10)

# Search for events containing specific text
search_results = db_utils.search_events(query="error", agent_id="my_agent")

# Get statistics for an agent
stats = db_utils.get_agent_stats(agent_id="my_agent")
```

## Compliance & Security

Cylestio Monitor is designed with compliance in mind:

- **SOC2**: Comprehensive logging and monitoring
- **GDPR**: Data masking and retention policies
- **HIPAA**: Secure storage and access controls

The SDK includes features to help you maintain compliance:

- **Data masking**: Automatically mask sensitive data like PII and PHI
- **Retention policies**: Configure how long data is stored
- **Access controls**: Database is stored in a user-specific location

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

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://cylestio.github.io/cylestio-monitor/development/contributing/) for details.

## Security & Compliance

For compliance with SOC2, GDPR, and HIPAA requirements:
- Never commit credentials or secrets
- Never commit PII or PHI data
- Address security vulnerabilities promptly
- Run security checks before commits: `pre-commit run --all-files`
