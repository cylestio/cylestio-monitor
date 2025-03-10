# Cylestio Monitor

A lightweight, drop-in monitoring SDK for AI agents, MCP, and LLM API calls.

## Overview

Cylestio Monitor intercepts key MCP and LLM calls and logs call parameters, durations, and responses as structured JSON events. Each event includes a severity flag ("alert") if suspicious or dangerous terms are detected. Dangerous prompts are blocked, while suspicious ones are flagged for review.

## Key Features

- **Zero-configuration setup**: Just import and enable monitoring
- **Automatic framework detection**: Works with MCP and popular LLM clients
- **Security monitoring**: Detects and blocks dangerous prompts
- **Structured logging**: All events are logged in a structured JSON format
- **Performance tracking**: Monitors call durations and response times
- **Global SQLite database**: Stores all events in a shared, OS-agnostic location

## Quick Installation

```bash
pip install cylestio-monitor
```

## Basic Usage

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

## Getting Started

Ready to start monitoring your AI agents? Check out the [Installation Guide](getting-started/installation.md) and [Quick Start Guide](getting-started/quick-start.md) to get up and running in minutes. 