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

## Development Installation

If you plan to contribute to Cylestio Monitor, install the package with development dependencies:

```bash
# Clone the repository
git clone https://github.com/cylestio/cylestio-monitor.git
cd cylestio-monitor

# Install the package in development mode with extra dependencies
pip install -e ".[dev,test,security]"
```

## Verifying Installation

You can verify your installation by importing the package:

```python
import cylestio_monitor
print(cylestio_monitor.__version__)
```

## Next Steps

Once installed, you can:

1. [Get started](quick-start.md) with basic monitoring
2. Review the [configuration options](configuration.md)
3. Explore [advanced use cases](../monitoring_channels.md)

## Dashboard Installation

For visualization of your monitoring data, we recommend installing our separate [dashboard application](https://github.com/cylestio/cylestio-dashboard).

```bash
pip install cylestio-dashboard
```

The dashboard provides a web interface for viewing events, alerts, and performance metrics collected by Cylestio Monitor. 