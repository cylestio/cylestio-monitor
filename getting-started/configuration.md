# Configuration

Cylestio Monitor provides flexible configuration options to customize its behavior to your specific requirements.

## Configuration Location

The configuration file is automatically created on first use and stored in an OS-specific location:

- **Linux**: `~/.config/cylestio-monitor/config.yaml`
- **macOS**: `~/Library/Application Support/cylestio-monitor/config.yaml`
- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\config.yaml`

## Configuration Options

Below is the complete configuration schema with default values and descriptions:

```yaml
# Security monitoring settings
security:
  # Enable or disable security monitoring
  enabled: true
  
  # Keywords that trigger a suspicious flag (case-insensitive)
  suspicious_keywords:
    - "hack"
    - "exploit"
    - "bypass"
    - "vulnerability"
    - "override"
    - "inject"
    - "ignore previous"
    # ... and more
  
  # Keywords that block the request (case-insensitive)
  dangerous_keywords:
    - "sql injection"
    - "cross-site scripting"
    - "steal credentials"
    - "ignore all previous instructions"
    # ... and more
    
  # Action to take for suspicious content: "alert" (default), "block", or "log"
  suspicious_action: "alert"
  
  # Action to take for dangerous content: "block" (default), "alert", or "log"
  dangerous_action: "block"

# Data masking for PII/PHI protection
data_masking:
  # Enable or disable data masking
  enabled: true
  
  # Patterns to mask in logs and stored data
  patterns:
    - name: "credit_card"
      regex: "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b"
      replacement: "[CREDIT_CARD]"
    - name: "ssn"
      regex: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
      replacement: "[SSN]"
    - name: "email"
      regex: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
      replacement: "[EMAIL]"
    - name: "phone"
      regex: "\\b(\\+\\d{1,2}\\s?)?\\(?\\d{3}\\)?[\\s.-]?\\d{3}[\\s.-]?\\d{4}\\b"
      replacement: "[PHONE]"
    # ... and more

# API client settings
api:
  # API endpoint for sending events
  endpoint: ""
  
  # Request timeout in seconds
  timeout: 5
  
  # Retry on failure (not yet implemented)
  retry_enabled: false

# Logging settings
logging:
  # Log level for SDK operations
  level: "INFO"
  
  # Whether to include timestamps in logs
  include_timestamp: true
  
  # Whether to include agent_id in logs
  include_agent_id: true
  
  # Format for console logs: "text" or "json"
  console_format: "text"
```

## Modifying Configuration

You can modify the configuration in three ways:

### 1. Edit the Configuration File

Simply edit the YAML file directly. Changes will be picked up the next time you enable monitoring.

### 2. API Configuration

Set specific configuration options when enabling monitoring:

```python
from cylestio_monitor import enable_monitoring

enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events",
        "security": {
            "suspicious_keywords": ["custom", "keywords", "here"],
            "dangerous_action": "alert"  # Don't block, just alert
        },
        "data_masking": {
            "enabled": False  # Disable data masking
        }
    }
)
```

### 3. Environment Variables

Set configuration via environment variables:

```bash
# Set API endpoint
export CYLESTIO_API_ENDPOINT="https://api.example.com/events"

# Disable security monitoring
export CYLESTIO_SECURITY_ENABLED=false

# Add custom dangerous keywords (comma-separated)
export CYLESTIO_SECURITY_DANGEROUS_KEYWORDS="custom term 1,custom term 2"
```

## Configuration Priorities

The configuration system follows this priority order (highest to lowest):

1. Runtime configuration from `enable_monitoring()`
2. Environment variables
3. Configuration file
4. Default values

## Testing Your Configuration

To verify your configuration is working as expected:

```python
from cylestio_monitor import get_api_endpoint
from cylestio_monitor.config import ConfigManager

# Check API endpoint
api_endpoint = get_api_endpoint()
print(f"API endpoint: {api_endpoint}")

# Check other configuration values
config = ConfigManager()
print(f"Security enabled: {config.get('security.enabled')}")
```

## Configuration Reference

### API Client Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_endpoint` | string | `""` | URL of the remote API endpoint |
| `api.timeout` | integer | 5 | Request timeout in seconds |

### Security Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `security.enabled` | boolean | true | Enable or disable security monitoring |
| `security.suspicious_keywords` | list | [see config] | Keywords that trigger a suspicious flag |
| `security.dangerous_keywords` | list | [see config] | Keywords that block the request |
| `security.suspicious_action` | string | "alert" | Action to take for suspicious content: "alert", "block", or "log" |
| `security.dangerous_action` | string | "block" | Action to take for dangerous content: "block", "alert", or "log" |

### Data Masking Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_masking.enabled` | boolean | true | Enable or disable data masking |
| `data_masking.patterns` | list | [see config] | Patterns to mask in logs and stored data |

### Logging Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `logging.level` | string | "INFO" | Log level for SDK operations |
| `logging.include_timestamp` | boolean | true | Whether to include timestamps in logs |
| `logging.include_agent_id` | boolean | true | Whether to include agent_id in logs |
| `logging.console_format` | string | "text" | Format for console logs: "text" or "json" |
| `log_file` | string | null | Path to output JSON log file |

## Environment Variables

| Environment Variable | Configuration Parameter |
|----------------------|-------------------------|
| `CYLESTIO_API_ENDPOINT` | API endpoint URL |
| `CYLESTIO_SECURITY_ENABLED` | `security.enabled` |
| `CYLESTIO_SECURITY_SUSPICIOUS_KEYWORDS` | `security.suspicious_keywords` (comma-separated) |
| `CYLESTIO_SECURITY_DANGEROUS_KEYWORDS` | `security.dangerous_keywords` (comma-separated) |
| `CYLESTIO_SECURITY_SUSPICIOUS_ACTION` | `security.suspicious_action` |
| `CYLESTIO_SECURITY_DANGEROUS_ACTION` | `security.dangerous_action` |
| `CYLESTIO_LOG_FILE` | Path to output JSON log file |
| `CYLESTIO_LOG_LEVEL` | `logging.level` |

## Example Configuration File

Here's a complete example configuration file:

```yaml
security:
  enabled: true
  suspicious_keywords:
    - "hack"
    - "exploit"
    - "vulnerability"
  dangerous_keywords:
    - "sql injection"
    - "ignore all instructions"
  suspicious_action: "alert"
  dangerous_action: "block"

data_masking:
  enabled: true
  patterns:
    - name: "credit_card"
      regex: "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b"
      replacement: "[CREDIT_CARD]"

api:
  endpoint: "https://api.example.com/events"
  timeout: 10

logging:
  level: "INFO"
  include_timestamp: true
  include_agent_id: true
  console_format: "text"
```

## Next Steps

- Learn how to use [monitoring with LLM providers](../user-guide/monitoring-llm.md)
- Explore the [security features](../user-guide/security-features.md) in depth
- Set up the [dashboard](https://github.com/cylestio/cylestio-dashboard) for visualization 

## Basic Configuration

When enabling monitoring, you can provide several configuration options:

```python
from cylestio_monitor import enable_monitoring

enable_monitoring(
    agent_id="my-agent",
    llm_client=client,
    block_dangerous=True,
    security_level="high",
    log_file="/path/to/logs/monitoring.json",
    development_mode=False
)
```

## Common Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `agent_id` | string | Required | Unique identifier for the agent being monitored |
| `llm_client` | object | None | LLM client instance to monitor |
| `block_dangerous` | boolean | False | Whether to block dangerous prompts |
| `security_level` | string | "medium" | Security level: "low", "medium", "high" |
| `log_file` | string | None | Path to log file or directory |
| `development_mode` | boolean | False | Enable additional debug information |
| `database_path` | string | System default | Custom path for the monitoring database |

## Security Configuration

### Security Levels

Cylestio Monitor supports three security levels:

- **Low**: Only blocks the most dangerous prompts (e.g., explicit attempts to hack the AI)
- **Medium**: Blocks dangerous prompts and flags suspicious ones (default)
- **High**: Blocks dangerous prompts, flags suspicious ones, and limits access to sensitive features

```python
from cylestio_monitor import enable_monitoring

# High security level for production
enable_monitoring(
    agent_id="production-agent",
    security_level="high",
    block_dangerous=True
)

# Low security level for development
enable_monitoring(
    agent_id="dev-agent",
    security_level="low",
    block_dangerous=False
)
```

### Custom Security Rules

You can add custom security rules:

```python
from cylestio_monitor import enable_monitoring, add_security_rule

# Enable monitoring
enable_monitoring(agent_id="my-agent")

# Add custom security rules
add_security_rule(
    name="block-financial-data",
    pattern=r"credit.card|ssn|bank.account",
    action="block",
    severity="high"
)
```

## Logging Configuration

### File Logging

You can log events to a file:

```python
from cylestio_monitor import enable_monitoring

# Log to a specific file
enable_monitoring(
    agent_id="my-agent",
    log_file="/path/to/logs/monitoring.json"
)

# Log to a directory (a timestamped file will be created)
enable_monitoring(
    agent_id="my-agent",
    log_file="/path/to/logs/"
)
```

### Logging Format

The log file format is JSON, with each event on a new line (JSON Lines format):

```json
{"event": "LLM_call_start", "data": {"model": "claude-3-sonnet-20240229", "messages": [...]}, "timestamp": "2024-06-15T14:30:22.123456", "agent_id": "my-agent", "channel": "LLM", "level": "info"}
{"event": "LLM_call_finish", "data": {"duration_ms": 1234, "response": {...}}, "timestamp": "2024-06-15T14:30:23.456789", "agent_id": "my-agent", "channel": "LLM", "level": "info"}
```

## Database Configuration

### Custom Database Path

You can specify a custom database path:

```python
from cylestio_monitor import enable_monitoring

# Use a custom database path
enable_monitoring(
    agent_id="my-agent",
    database_path="/path/to/custom/database.db"
)
```

### Data Retention

You can configure how long data is retained:

```python
from cylestio_monitor import enable_monitoring

# Set data retention to 60 days
enable_monitoring(
    agent_id="my-agent",
    data_retention_days=60
)
```

## MCP-Specific Configuration

When using Cylestio Monitor with Model Context Protocol (MCP), additional configuration options are available:

```python
from cylestio_monitor import enable_monitoring

enable_monitoring(
    agent_id="mcp-agent",
    mcp_config={
        # MCP-specific settings
        "context_window": 4096,
        "max_tokens": 1000,
        "temperature": 0.7,
        # Security settings
        "allow_system_commands": False,
        "allow_code_execution": False,
        "restricted_tools": ["file_access", "network_access"],
        # Monitoring settings
        "log_context_windows": True,
        "track_token_usage": True
    }
)
```

### MCP Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `context_window` | integer | 4096 | Maximum context window size |
| `max_tokens` | integer | 1000 | Maximum tokens per response |
| `temperature` | float | 0.7 | Sampling temperature |
| `allow_system_commands` | boolean | False | Allow system command execution |
| `allow_code_execution` | boolean | False | Allow code execution |
| `restricted_tools` | list | [] | List of restricted tool names |
| `log_context_windows` | boolean | True | Log context window usage |
| `track_token_usage` | boolean | True | Track token usage metrics |

## Environment Variables

Cylestio Monitor also supports configuration via environment variables:

| Environment Variable | Description |
|----------------------|-------------|
| `CYLESTIO_AGENT_ID` | Default agent ID |
| `CYLESTIO_LOG_FILE` | Path to log file |
| `CYLESTIO_SECURITY_LEVEL` | Security level (low, medium, high) |
| `CYLESTIO_BLOCK_DANGEROUS` | Whether to block dangerous prompts (true/false) |
| `CYLESTIO_DATABASE_PATH` | Custom database path |
| `CYLESTIO_DEVELOPMENT_MODE` | Enable development mode (true/false) |

Example:

```bash
export CYLESTIO_AGENT_ID="my-agent"
export CYLESTIO_SECURITY_LEVEL="high"
export CYLESTIO_BLOCK_DANGEROUS="true"
```

Then in your code:

```python
from cylestio_monitor import enable_monitoring

# Configuration will be loaded from environment variables
enable_monitoring()
```

## Configuration File

You can also use a configuration file:

```python
from cylestio_monitor import enable_monitoring_from_config

# Load configuration from a file
enable_monitoring_from_config("/path/to/config.yaml")
```

Example configuration file (`config.yaml`):

```yaml
agent_id: my-agent
security:
  level: high
  block_dangerous: true
logging:
  log_file: /path/to/logs/monitoring.json
database:
  path: /path/to/custom/database.db
  retention_days: 60
``` 