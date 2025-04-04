# Debug Logging Configuration Guide

This guide explains how to configure debug logging in the Cylestio Monitor SDK, providing options to control the verbosity and destination of debug output.

## Quick Start

```python
from cylestio_monitor import start_monitoring

# Start monitoring with minimal debug configuration
start_monitoring(
    agent_id="my-agent", 
    config={
        "events_output_file": "logs/events.json",  # Path for storing event data
        "debug_mode": True,  # Enable debug output
        "debug_log_file": "logs/debug.log",  # Optional: Send to file instead of console
    }
)
```

## Configuration Options

When initializing the SDK with `start_monitoring()`, you can provide these debug-related configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `events_output_file` | string | `None` | Path to store structured event data in JSON format |
| `debug_mode` | boolean | `False` | Enable or disable debug output |
| `debug_level` | string | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `debug_log_file` | string | `None` | Path to write debug logs (if provided, logs go to file instead of console) |

## Usage Examples

### Default Configuration (Minimal Output)

```python
from cylestio_monitor import start_monitoring

# Start monitoring with default settings (minimal output)
start_monitoring(agent_id="my-agent")
```

### Enable Debug Output to Console

```python
from cylestio_monitor import start_monitoring

# Start monitoring with debug output to console
start_monitoring(
    agent_id="my-agent",
    config={
        "events_output_file": "logs/events.json",
        "debug_mode": True,
        "debug_level": "DEBUG"  # Optional: sets the verbosity level
    }
)
```

### Write Debug Output to File

```python
from cylestio_monitor import start_monitoring

# Start monitoring with debug output to file
start_monitoring(
    agent_id="my-agent",
    config={
        "events_output_file": "logs/events.json",
        "debug_mode": True,
        "debug_log_file": "logs/debug.log"  # Sends all debug output to this file
    }
)
```

## Complete Example

See the [debug_logging_example.py](./debug_logging_example.py) file for a complete example demonstrating all configuration options.

## Best Practices

1. **Development Environment**:
   - Enable debug mode to console for easier debugging: `"debug_mode": True`
   - Use DEBUG level for most detailed output: `"debug_level": "DEBUG"`

2. **Testing Environment**:
   - Send debug output to a file: `"debug_log_file": "logs/debug.log"`
   - Use INFO level for relevant information: `"debug_level": "INFO"`

3. **Production Environment**:
   - Disable debug mode: `"debug_mode": False` (or omit the parameter)
   - Or send debugging to a separate file: `"debug_log_file": "logs/production_debug.log"` 