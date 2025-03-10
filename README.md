# Cylestio Monitor

A lightweight, drop-in monitoring SDK for MCP and LLM API calls.

## Overview

Cylestio Monitor intercepts key MCP and LLM calls and logs call parameters, durations, and responses as structured JSON events. Each event includes a severity flag ("alert") if suspicious or dangerous terms are detected. Dangerous prompts are blocked, while suspicious ones are flagged for review.

## Features

- **Zero-configuration setup**: Just import and enable monitoring
- **Automatic framework detection**: Works with MCP and popular LLM clients
- **Security monitoring**: Detects and blocks dangerous prompts
- **Structured logging**: All events are logged in a structured JSON format
- **Performance tracking**: Monitors call durations and response times
- **Global SQLite database**: Stores all events in a shared, OS-agnostic location
- **Agent-based aggregation**: Logs include agent ID for multi-project aggregation
- **Flexible output options**: Log to both SQLite database and JSON files

## Installation

```bash
pip install cylestio-monitor
```

## Quick Start

```python
from cylestio_monitor import enable_monitoring, disable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring with SQLite database only
enable_monitoring(
    agent_id="my_agent",
    llm_client=client  # Pass your LLM client for monitoring
)

# Enable monitoring with both SQLite and JSON logging
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/"
)

# Use your client as normal - monitoring happens automatically
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# When done, you can disable monitoring
disable_monitoring()
```

## Logging

The Cylestio Monitor SDK logs events to both a SQLite database and optionally to JSON files.

### SQLite Database

All events are logged to a SQLite database, which is created in the user's application data directory. The database contains tables for agents, events, and other monitoring data.

### JSON Logging

You can enable JSON logging by providing a `log_file` parameter to the `enable_monitoring` function:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Log to a specific file
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/monitoring.json"
)

# Log to a directory (a timestamped file will be created)
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/"
)
```

The SDK will use the following naming conventions for JSON log files:

1. If a directory is provided, a file named `{agent_id}_monitoring_{timestamp}.json` will be created.
2. If a file without extension is provided, `.json` will be added.

For more details, see the [Integration Tests README](tests/integration/README.md).

## Monitoring MCP

The SDK automatically patches the MCP `ClientSession` class to monitor tool calls:

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

# Enable monitoring before creating your MCP session
enable_monitoring(agent_id="mcp-project")

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

## Configuration Options

The `enable_monitoring` function accepts the following parameters:

- `agent_id`: Unique identifier for this agent/project (required)
- `llm_client`: Optional LLM client instance (Anthropic, OpenAI, etc.)
- `llm_method_path`: Path to the LLM client method to patch (default: "messages.create")
- `log_file`: Path to the output log file (if None, only SQLite logging is used)
- `debug_level`: Logging level for SDK's internal debug logs (default: "INFO")

## Global SQLite Database

Cylestio Monitor stores all events in a global SQLite database, ensuring that all instances of the SDK write to the same database regardless of the virtual environment in which they're installed.

### Location

The database file is stored in an OS-specific location determined by the `platformdirs` library:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
- **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

### Database Schema

The database has two main tables:

1. **agents**: Stores information about each agent (project)
   - `id`: Primary key
   - `agent_id`: Unique ID of the agent
   - `created_at`: When the agent was first seen
   - `last_seen`: When the agent was last seen

2. **events**: Stores all monitoring events
   - `id`: Primary key
   - `agent_id`: Foreign key to the agents table
   - `event_type`: Type of event (e.g., "LLM_call_start", "MCP_tool_call_finish")
   - `channel`: Channel of the event (e.g., "LLM", "MCP", "SYSTEM")
   - `level`: Log level (e.g., "info", "warning", "error")
   - `timestamp`: When the event occurred
   - `data`: JSON data containing the event details

### Accessing the Database

You can access the database programmatically:

```python
from cylestio_monitor import get_database_path
from cylestio_monitor.db import utils as db_utils

# Get the path to the database
db_path = get_database_path()
print(f"Database path: {db_path}")

# Get recent events for a specific agent
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get events by type
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get events from the last 24 hours
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")

# Search events
search_results = db_utils.search_events("error", agent_id="my-project")

# Get agent statistics
stats = db_utils.get_agent_stats(agent_id="my-project")

# Clean up old events
deleted_count = db_utils.cleanup_old_events(days=30)
```

## Global Configuration File

Cylestio Monitor uses a global configuration file to store settings that are shared across all installations of the SDK. This ensures consistent behavior regardless of which virtual environment or project is using the SDK.

### Location

The configuration file is stored in an OS-specific location determined by the `platformdirs` library:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\config.yaml`
- **macOS**: `~/Library/Application Support/cylestio-monitor/config.yaml`
- **Linux**: `~/.local/share/cylestio-monitor/config.yaml`

### First Run Behavior

On first run, the SDK copies a default configuration file to the global location if it doesn't exist. This ensures that the SDK has a valid configuration to work with, even if it's installed in multiple virtual environments.

### Configuration Schema

The configuration file is a YAML file with the following structure:

```yaml
# Security monitoring settings
security:
  # Keywords for security checks
  suspicious_keywords:
    - "REMOVE"
    - "CLEAR"
    - "HACK"
    - "BOMB"
  
  dangerous_keywords:
    - "DROP"
    - "DELETE"
    - "SHUTDOWN"
    - "EXEC("
    - "FORMAT"
    - "RM -RF"
    - "KILL"

# Logging configuration
logging:
  level: "INFO"
  format: "json"
  file_rotation: true
  max_file_size_mb: 10
  backup_count: 5

# Monitoring settings
monitoring:
  enabled: true
  channels:
    - "SYSTEM"
    - "LLM"
    - "API"
    - "MCP"
  alert_levels:
    - "none"
    - "suspicious"
    - "dangerous"
```

For more information about monitoring channels and what they represent, see [Monitoring Channels](docs/monitoring_channels.md).

### Modifying the Configuration

You can modify the configuration file directly, or use the provided API:

```python
from cylestio_monitor.config import ConfigManager

# Get the configuration manager instance
config_manager = ConfigManager()

# Add a new dangerous keyword
dangerous_keywords = config_manager.get_dangerous_keywords()
dangerous_keywords.append("KILL")
config_manager.set("security.dangerous_keywords", dangerous_keywords)
```

> **Important**: After modifying the configuration file, any running agents or applications using the Cylestio Monitor SDK must be restarted for the changes to take effect.

## Security Features

The SDK checks for suspicious and dangerous terms in both prompts and responses:

- **Suspicious terms**: Flagged but allowed (e.g., "REMOVE", "CLEAR", "HACK", "BOMB")
- **Dangerous terms**: Blocked entirely (e.g., "DROP", "DELETE", "SHUTDOWN", "EXEC(", "FORMAT", "RM -RF")

## Log Format

The SDK logs events in a structured JSON format:

```json
{
  "timestamp": "2023-06-15T12:34:56.789Z",
  "level": "INFO",
  "channel": "LLM",
  "agent_id": "my-project",
  "event": "LLM_call_start",
  "data": {
    "prompt": "...",
    "alert": "none"
  }
}
```

## License

MIT

## Development Setup

### Quick Setup

We provide a setup script that installs all dependencies and configures pre-commit hooks for security checks:

```bash
# Make the script executable
chmod +x setup_dev.sh

# Run the setup script
./setup_dev.sh
```

### Manual Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev,test,security]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type pre-push
   ```

### Verifying Your Setup

To verify that your local security checks are properly installed and working:

```bash
# Make the verification script executable
chmod +x verify_hooks.sh

# Run the verification script
./verify_hooks.sh
```

This script will:
- Check that pre-commit and pre-push hooks are installed
- List all configured hooks
- Run a dry-run of all pre-commit checks
- Provide guidance on the security workflow

### Security Compliance

This project implements security checks to help maintain compliance with:
- SOC2
- GDPR
- HIPAA

The pre-commit hooks automatically check for:
- Hardcoded credentials and secrets
- Known security vulnerabilities in dependencies
- Common security issues in Python code

These checks run automatically before each commit. If a check fails, the commit will be blocked until the issue is resolved.
