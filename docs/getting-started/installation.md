# Installation

!!! info "Quick Install"
    ```bash
    pip install cylestio-monitor
    ```

## Requirements

- Python 3.11 or higher
- SQLite 3.35.0 or higher (for JSON1 extension support)

## Installation Methods

### Using pip

```bash
pip install cylestio-monitor
```

### From Source

```bash
git clone https://github.com/cylestio/cylestio-monitor.git
cd cylestio-monitor
pip install -e .
```

## Dependencies

!!! note "Dependencies"
    Cylestio Monitor has the following dependencies:

    - `anthropic`: For monitoring Anthropic Claude API calls
    - `mcp`: For monitoring MCP tool calls
    - `pydantic`: For data validation
    - `python-dotenv`: For environment variable support
    - `structlog`: For structured logging
    - `platformdirs`: For OS-agnostic file paths
    - `pyyaml`: For configuration file parsing

## Verifying Installation

You can verify that Cylestio Monitor is installed correctly by running:

```python
import cylestio_monitor
print(cylestio_monitor.__version__)
```

!!! tip "Database Location"
    The database file is stored in an OS-specific location:

    - **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
    - **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
    - **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

## Next Steps

Now that you have installed Cylestio Monitor, you can:

1. Check out the [Quick Start Guide](quick-start.md) to get up and running
2. Learn about [Configuration Options](configuration.md) to customize the SDK 