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

# Database settings
database:
  # Number of days to keep events before automatic cleanup
  retention_days: 30
  
  # Whether to vacuum the database on startup
  vacuum_on_startup: true
  
  # Maximum database size in MB (0 for unlimited)
  max_size_mb: 1000

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
    config_overrides={
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
# Set retention period to 60 days
export CYLESTIO_DATABASE_RETENTION_DAYS=60

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
from cylestio_monitor import get_current_config

# Get the full active configuration
config = get_current_config()
print(config)

# Test a specific security setting
if config["security"]["enabled"]:
    print("Security monitoring is enabled")
```

## Next Steps

- Learn how to use [monitoring with LLM providers](../user-guide/monitoring-llm.md)
- Explore the [security features](../user-guide/security-features.md) in depth
- Set up the [dashboard](https://github.com/cylestio/cylestio-dashboard) for visualization 