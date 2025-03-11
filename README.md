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

## Tools and Utilities

### Synthetic Data Generator

A tool for generating synthetic monitoring data for demo and testing purposes. It creates realistic events for five different AI agents over a one-month period with varied event types, alert levels, and metrics.

To use the synthetic data generator:

```bash
cd tools/synthetic_data_generator
./run_demo.sh
```

For more details, see the [Synthetic Data Generator README](tools/synthetic_data_generator/README.md).

## Documentation

For full documentation, visit [cylestio.github.io/cylestio-monitor](https://cylestio.github.io/cylestio-monitor/).

## License

MIT
