# Configuration

Cylestio Monitor provides several configuration options to customize its behavior.

## Global Configuration File

The configuration file is stored in an OS-specific location:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\config.yaml`
- **macOS**: `~/Library/Application Support/cylestio-monitor/config.yaml`
- **Linux**: `~/.local/share/cylestio-monitor/config.yaml`

## Default Configuration

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

## Runtime Configuration

```python
from cylestio_monitor import enable_monitoring

# Enable monitoring with custom settings
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file="/path/to/logs/monitoring.json",
    debug_level="DEBUG"  # Override the default logging level
)
```

## Configuration Parameters

- **agent_id**: Unique identifier for your agent or project
- **llm_client**: LLM client instance to monitor
- **llm_method_path**: Path to the LLM client method to patch (default: "messages.create")
- **log_file**: Path to the output log file (if None, only SQLite logging is used)
- **debug_level**: Logging level for the SDK's internal debug logs (default: "INFO")

## Customizing Security Keywords

Edit the global configuration file to customize security keywords:

```yaml
security:
  suspicious_keywords:
    - "REMOVE"
    - "CLEAR"
    - "HACK"
    - "BOMB"
    - "YOUR_CUSTOM_TERM"
  
  dangerous_keywords:
    - "DROP"
    - "DELETE"
    - "SHUTDOWN"
    - "EXEC("
    - "FORMAT"
    - "RM -RF"
    - "KILL"
    - "YOUR_CUSTOM_DANGEROUS_TERM"
```

## Monitoring Channels

Cylestio Monitor categorizes events into different channels to help organize and filter monitoring data. The default channels are:

- **SYSTEM**: Events related to the SDK itself
- **LLM**: Events related to LLM API calls
- **API**: Events related to general API calls
- **MCP**: Events related to MCP tool calls

You can customize the enabled channels in the global configuration file:

```yaml
monitoring:
  channels:
    - "SYSTEM"
    - "LLM"
    - "API"
    - "MCP"
    - "YOUR_CUSTOM_CHANNEL"
```

For more information about monitoring channels, see [Monitoring Channels](../advanced-topics/monitoring-channels.md).

## Next Steps

Now that you understand how to configure Cylestio Monitor, you can:

1. Learn more about [monitoring LLM calls](../user-guide/monitoring-llm.md)
2. Explore [monitoring MCP](../user-guide/monitoring-mcp.md)
3. Check out the [security features](../user-guide/security-features.md)
4. Review [logging options](../user-guide/logging-options.md) 