# Installation

Installing Cylestio Monitor is straightforward. The package is available on PyPI and can be installed with pip.

## Requirements

- Python 3.9 or higher
- pip (Python package installer)

## Standard Installation

```bash
pip install cylestio-monitor
```

This command installs the core monitoring package with all essential dependencies.

## Verifying Installation

You can verify your installation by importing the package:

```python
import cylestio_monitor
print(cylestio_monitor.__version__)  # Should print 0.1.5 or newer
```

## Basic Usage

Once installed, you can start using Cylestio Monitor with just two lines of code:

```python
import cylestio_monitor

# Start monitoring at the beginning of your application
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Your application code here...
# Use Anthropic, LangChain, MCP, etc. as normal

# Stop monitoring at the end of your application
cylestio_monitor.stop_monitoring()
```

## Next Steps

Once installed, you can:

1. Read the [Quick Start Guide](quick-start.md) for basic monitoring setup
2. Check out our [examples](../../examples/agents/) for real-world implementations
3. Learn about [Custom Integrations](../custom-integrations.md) for advanced use cases

## Development Installation

If you plan to contribute to Cylestio Monitor, install the package with development dependencies:

```bash
# Clone the repository
git clone https://github.com/cylestio/cylestio-monitor.git
cd cylestio-monitor

# Install the package in development mode with extra dependencies
pip install -e ".[dev,test]"
```
