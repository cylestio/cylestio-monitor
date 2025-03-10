# Cylestio Monitor

<div class="grid-container">
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Security Monitoring</h3>
      <p>Detect and block dangerous prompts, flag suspicious activity</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Performance Tracking</h3>
      <p>Monitor call durations and response times</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <rect x="2" y="3" width="20" height="18" rx="2" ry="2" />
        <line x1="7" y1="7" x2="7" y2="7" />
        <line x1="7" y1="11" x2="7" y2="11" />
        <line x1="7" y1="15" x2="7" y2="15" />
        <line x1="11" y1="7" x2="17" y2="7" />
        <line x1="11" y1="11" x2="17" y2="11" />
        <line x1="11" y1="15" x2="17" y2="15" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Structured Logging</h3>
      <p>Store events in SQLite with flexible output options</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Zero Configuration</h3>
      <p>Drop-in monitoring for MCP and popular LLM clients</p>
    </div>
  </div>
</div>

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