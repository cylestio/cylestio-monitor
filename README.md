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

## Installation

```bash
pip install cylestio-monitor
```

## Quick Start

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
llm_client = Anthropic()

# Enable monitoring
enable_monitoring(
    logger_id="my-app",  # Optional identifier
    llm_client=llm_client,  # Your LLM client instance
    log_file="monitoring.json"  # Output file path
)

# Use your client as normal - monitoring happens automatically
response = llm_client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

# When done, you can disable monitoring
from cylestio_monitor import disable_monitoring
disable_monitoring()
```

## Monitoring MCP

The SDK automatically patches the MCP `ClientSession` class to monitor tool calls:

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

# Enable monitoring before creating your MCP session
enable_monitoring(logger_id="mcp-app")

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

## Configuration Options

The `enable_monitoring` function accepts the following parameters:

- `logger_id`: Optional identifier for the logger
- `llm_client`: Optional LLM client instance (Anthropic, OpenAI, etc.)
- `llm_method_path`: Path to the LLM client method to patch (default: "messages.create")
- `log_file`: Path to the output log file (default: "cylestio_monitoring.json")
- `debug_level`: Logging level for SDK's internal debug logs (default: "INFO")

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

### Local Security Workflow

Our security workflow consists of:

1. **Pre-commit hooks** (fast, run on every commit):
   - Detect private keys and credentials
   - Run basic security linting (Ruff, Bandit)
   - Scan for vulnerable dependencies (Safety)

2. **Pre-push hooks** (comprehensive, run before push):
   - Run more thorough Bandit security scan
   - Run complete dependency vulnerability checks
   - Run security-specific tests

3. **CI/CD Pipeline** (complete, runs on GitHub):
   - Runs all security checks in a clean environment
   - Performs additional scans not feasible locally
   - Generates security reports

### CI/CD Pipeline

Our CI/CD pipeline runs additional security checks on each pull request. To avoid CI failures:
1. Always run `pre-commit run --all-files` before pushing changes
2. Address all security warnings and errors locally
3. Document any false positives or accepted risks in your PR description
