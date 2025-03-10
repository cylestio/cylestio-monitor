# Cylestio Monitor Configuration Management

This module provides configuration management for the Cylestio Monitor SDK. It ensures that the configuration is stored in a global location that is accessible across different virtual environments.

## Overview

The configuration management system follows these principles:

1. **Single Source of Truth**: The configuration is stored in a global location that is accessible across different virtual environments.
2. **Default Configuration**: The SDK ships with a default configuration file that is used as a template for the global configuration.
3. **First Run Logic**: On first run, the SDK copies the default configuration to the global location if it doesn't exist.
4. **Configuration Access**: The SDK provides a simple API for accessing and modifying the configuration.

## Configuration Location

The configuration is stored in a global location determined by the `platformdirs` library, which ensures OS-agnostic behavior:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\config.yaml`
- **macOS**: `~/Library/Application Support/cylestio-monitor/config.yaml`
- **Linux**: `~/.local/share/cylestio-monitor/config.yaml`

## Usage

### Accessing Configuration Values

```python
from cylestio_monitor.config import ConfigManager

# Get the configuration manager instance
config_manager = ConfigManager()

# Get a configuration value
suspicious_keywords = config_manager.get_suspicious_keywords()
dangerous_keywords = config_manager.get_dangerous_keywords()

# Get a configuration value by key
log_level = config_manager.get("logging.level", "INFO")
```

### Modifying Configuration Values

```python
from cylestio_monitor.config import ConfigManager

# Get the configuration manager instance
config_manager = ConfigManager()

# Set a configuration value
config_manager.set("logging.level", "DEBUG")

# Add a new suspicious keyword
suspicious_keywords = config_manager.get_suspicious_keywords()
suspicious_keywords.append("NEW_KEYWORD")
config_manager.set("security.suspicious_keywords", suspicious_keywords)
```

> **Important**: After modifying the configuration file, any running agents or applications using the Cylestio Monitor SDK must be restarted for the changes to take effect. The configuration is loaded when the SDK is initialized, and changes to the global configuration file are not automatically detected during runtime.

### Getting the Configuration Path

```python
from cylestio_monitor.config import get_config_path

# Get the path to the global configuration file
config_path = get_config_path()
print(f"Configuration file is located at: {config_path}")
```

## Dashboard Integration

The dashboard can access and modify the configuration using the same API:

```python
from cylestio_monitor.config import ConfigManager, get_config_path

# Get the configuration manager instance
config_manager = ConfigManager()

# Get the path to the global configuration file
config_path = get_config_path()

# Load the configuration
config = config_manager._config

# Modify the configuration
config["security"]["suspicious_keywords"].append("NEW_KEYWORD")

# Save the configuration
config_manager.save_config()
```

## Configuration Schema

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
  alert_levels:
    - "none"
    - "suspicious"
    - "dangerous"
  
# Dashboard integration
dashboard:
  enabled: true
  metrics_retention_days: 30
``` 