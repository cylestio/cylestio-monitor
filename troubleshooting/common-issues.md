# Common Issues

This guide addresses common issues you might encounter when using Cylestio Monitor and provides solutions to help you resolve them.

## Installation Issues

### Issue: Package Not Found

**Problem**: When trying to install Cylestio Monitor, you get a "package not found" error.

```
ERROR: Could not find a version that satisfies the requirement cylestio-monitor
ERROR: No matching distribution found for cylestio-monitor
```

**Solution**:

1. Ensure you're using the correct package name:

```bash
pip install cylestio-monitor
```

2. Check your internet connection and PyPI access.

3. If you're behind a corporate firewall, you might need to configure pip to use a proxy:

```bash
pip install --proxy http://user:password@proxyserver:port cylestio-monitor
```

### Issue: Dependency Conflicts

**Problem**: Installation fails due to dependency conflicts with existing packages.

**Solution**:

1. Consider using a virtual environment to isolate the installation:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install cylestio-monitor
```

2. If you need to use it in an existing environment, you can try to install with the `--no-dependencies` flag and then manually install compatible versions of the dependencies:

```bash
pip install --no-dependencies cylestio-monitor
pip install anthropic==0.18.0 mcp==1.3.0 pydantic==2.0.0 python-dotenv==1.0.0 structlog==24.1.0 platformdirs==4.0.0 pyyaml==6.0.0
```

## Configuration Issues

### Issue: Permission Denied for Database

**Problem**: When trying to use Cylestio Monitor, you get a "permission denied" error for the database file.

```
PermissionError: [Errno 13] Permission denied: '/path/to/cylestio_monitor.db'
```

**Solution**:

1. Check the permissions of the database directory:

```bash
ls -la ~/.local/share/cylestio-monitor/  # On Linux
ls -la ~/Library/Application\ Support/cylestio-monitor/  # On macOS
```

2. Ensure your user has write permissions to the directory:

```bash
chmod 755 ~/.local/share/cylestio-monitor/  # On Linux
chmod 755 ~/Library/Application\ Support/cylestio-monitor/  # On macOS
```

3. If you're running in a Docker container or other restricted environment, you might need to specify a different database location:

```python
import os
from cylestio_monitor import enable_monitoring

# Set environment variable to change database location
os.environ["CYLESTIO_DB_PATH"] = "/path/to/writable/directory/cylestio_monitor.db"

# Enable monitoring
enable_monitoring(agent_id="my-agent")
```

### Issue: Configuration File Not Found

**Problem**: Cylestio Monitor can't find the configuration file.

```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/config.yaml'
```

**Solution**:

1. Check if the configuration directory exists:

```bash
ls -la ~/.local/share/cylestio-monitor/  # On Linux
ls -la ~/Library/Application\ Support/cylestio-monitor/  # On macOS
```

2. If the directory doesn't exist, create it:

```bash
mkdir -p ~/.local/share/cylestio-monitor/  # On Linux
mkdir -p ~/Library/Application\ Support/cylestio-monitor/  # On macOS
```

3. Copy the default configuration file to the correct location:

```python
import shutil
import os
from pathlib import Path
import platformdirs

# Get the default config file path
default_config = Path(__file__).parent / "config" / "default_config.yaml"

# Get the user config directory
config_dir = platformdirs.user_data_dir("cylestio-monitor", "cylestio")
config_file = os.path.join(config_dir, "config.yaml")

# Create the directory if it doesn't exist
os.makedirs(os.path.dirname(config_file), exist_ok=True)

# Copy the default config file
shutil.copy(default_config, config_file)
```

## Monitoring Issues

### Issue: LLM Client Not Monitored

**Problem**: You've enabled monitoring for your LLM client, but you don't see any events in the logs.

**Solution**:

1. Ensure you're passing the client instance to `enable_monitoring`:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring with the client
enable_monitoring(
    agent_id="my_agent",
    llm_client=client  # Make sure to pass the client here
)
```

2. Check if you're using a supported LLM client. Currently, Cylestio Monitor supports:
   - Anthropic Claude (via the `anthropic` Python client)

3. If you're using a custom or unsupported LLM client, you might need to specify the method path:

```python
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    llm_method_path="custom_method.path"  # Specify the method path
)
```

4. Verify that you're actually using the monitored client instance:

```python
# Correct: Using the monitored client
response = client.messages.create(...)

# Incorrect: Creating a new, unmonitored client
new_client = Anthropic()
response = new_client.messages.create(...)  # This won't be monitored
```

### Issue: MCP Not Monitored

**Problem**: You've enabled monitoring, but MCP tool calls aren't being logged.

**Solution**:

1. Ensure you're enabling monitoring before creating the MCP session:

```python
from cylestio_monitor import enable_monitoring
from mcp import ClientSession

# Enable monitoring first
enable_monitoring(agent_id="mcp-project")

# Then create the MCP session
session = ClientSession(stdio, write)
```

2. Check if you're using a supported MCP version. Cylestio Monitor supports MCP version 1.3.0 and above.

3. Verify that the MCP module is installed and accessible:

```python
try:
    import mcp
    print(f"MCP version: {mcp.__version__}")
except ImportError:
    print("MCP not installed")
```

### Issue: Security Checks Too Strict

**Problem**: Legitimate operations are being blocked by the security checks.

**Solution**:

1. Customize the security keywords in the configuration file:

```yaml
security:
  suspicious_keywords:
    - "HACK"
    - "BOMB"
    # Remove or modify keywords that are causing false positives
  
  dangerous_keywords:
    - "DROP"
    - "DELETE"
    # Remove or modify keywords that are causing false positives
```

2. If you need to temporarily disable security checks for testing, you can modify the configuration:

```yaml
security:
  enabled: false
```

3. For a more permanent solution, consider implementing custom security checks:

```python
from cylestio_monitor.events_processor import contains_suspicious, contains_dangerous

# Original functions
original_contains_suspicious = contains_suspicious
original_contains_dangerous = contains_dangerous

# Custom functions
def custom_contains_suspicious(text):
    # Implement your custom logic
    if "LEGITIMATE_TERM" in text:
        return False
    return original_contains_suspicious(text)

def custom_contains_dangerous(text):
    # Implement your custom logic
    if "LEGITIMATE_TERM" in text:
        return False
    return original_contains_dangerous(text)

# Replace the original functions
import cylestio_monitor.events_processor
cylestio_monitor.events_processor.contains_suspicious = custom_contains_suspicious
cylestio_monitor.events_processor.contains_dangerous = custom_contains_dangerous
```

## Database Issues

### Issue: Database Locked

**Problem**: You get a "database is locked" error when trying to access the database.

```
sqlite3.OperationalError: database is locked
```

**Solution**:

1. This usually happens when multiple processes are trying to access the database simultaneously. Ensure that you're not running multiple instances of your application.

2. If you need to access the database from multiple processes, you can try increasing the timeout:

```python
from cylestio_monitor.db.db_manager import DBManager

# Get a connection
conn = DBManager()._get_connection()

# Increase the timeout (in milliseconds)
conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
```

3. Consider using a more robust database solution for high-concurrency scenarios.

### Issue: Database File Too Large

**Problem**: The database file is growing too large and consuming too much disk space.

**Solution**:

1. Implement regular cleanup of old events:

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 30 days
cleanup_old_events(days=30)
```

2. Optimize the database to reclaim space:

```python
from cylestio_monitor.db import utils as db_utils

# Optimize the database
db_utils.optimize_database()
```

3. Consider implementing a log rotation policy for JSON logs:

```yaml
logging:
  file_rotation: true
  max_file_size_mb: 10
  backup_count: 5
```

## Logging Issues

### Issue: JSON Logs Not Created

**Problem**: You've specified a `log_file` parameter, but no JSON logs are being created.

**Solution**:

1. Check if the directory exists and is writable:

```python
import os

log_dir = "/path/to/logs/"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
```

2. Ensure you're providing a valid path:

```python
# Correct: Absolute path
enable_monitoring(
    agent_id="my_agent",
    log_file="/path/to/logs/monitoring.json"
)

# Correct: Relative path with file name
enable_monitoring(
    agent_id="my_agent",
    log_file="logs/monitoring.json"
)

# Correct: Directory path (will create a timestamped file)
enable_monitoring(
    agent_id="my_agent",
    log_file="/path/to/logs/"
)
```

3. Check if you have permission to write to the specified location:

```python
import os

log_file = "/path/to/logs/monitoring.json"
log_dir = os.path.dirname(log_file)

# Check if directory exists and is writable
if not os.path.exists(log_dir):
    print(f"Directory {log_dir} does not exist")
elif not os.access(log_dir, os.W_OK):
    print(f"Directory {log_dir} is not writable")
else:
    print(f"Directory {log_dir} exists and is writable")
```

### Issue: Duplicate Logs

**Problem**: You're seeing duplicate log entries in your logs.

**Solution**:

1. Ensure you're not calling `enable_monitoring` multiple times:

```python
# Incorrect: Calling enable_monitoring multiple times
enable_monitoring(agent_id="my_agent")
enable_monitoring(agent_id="my_agent")  # This will create duplicate logs

# Correct: Call enable_monitoring once
enable_monitoring(agent_id="my_agent")
```

2. Check if you have multiple log handlers configured:

```python
import logging

# Check the number of handlers
logger = logging.getLogger("CylestioMonitor")
print(f"Number of handlers: {len(logger.handlers)}")

# Remove all handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
```

## Performance Issues

### Issue: Monitoring Slows Down Application

**Problem**: Enabling monitoring significantly slows down your application.

**Solution**:

1. Disable JSON logging if you don't need it:

```python
enable_monitoring(
    agent_id="my_agent",
    log_file=None  # Disable JSON logging
)
```

2. Optimize database operations:

```python
from cylestio_monitor.db.db_manager import DBManager

# Get a connection
conn = DBManager()._get_connection()

# Optimize for performance
conn.execute("PRAGMA synchronous=OFF")  # Less reliable but faster
conn.execute("PRAGMA journal_mode=MEMORY")  # Less reliable but faster
```

3. Implement selective monitoring:

```python
from cylestio_monitor.events_listener import monitor_call

# Only monitor critical functions
critical_function = monitor_call(critical_function, "CRITICAL")

# Don't monitor high-volume, low-risk functions
# high_volume_function = monitor_call(high_volume_function, "HIGH_VOLUME")
```

4. Consider using a more robust database solution for high-volume scenarios.

## Integration Issues

### Issue: Framework Integration Problems

**Problem**: You're having trouble integrating Cylestio Monitor with your web framework.

**Solution**:

1. Check the [Integration Patterns](../best-practices/integration-patterns.md) guide for examples of integrating with popular frameworks.

2. Ensure you're initializing monitoring at the right time:

```python
# Flask example
from flask import Flask
from cylestio_monitor import enable_monitoring

app = Flask(__name__)

# Enable monitoring before defining routes
enable_monitoring(agent_id="flask-app")

@app.route('/')
def index():
    return "Hello, World!"
```

3. If you're using a framework with a complex initialization process, consider using a factory pattern:

```python
# Flask factory example
def create_app():
    app = Flask(__name__)
    
    # Enable monitoring
    enable_monitoring(agent_id="flask-app")
    
    # Register routes
    app.register_blueprint(main_bp)
    
    return app
```

## Conclusion

If you're still experiencing issues after trying these solutions, please check the [FAQs](faqs.md) or reach out to the Cylestio Monitor community for help. You can also file an issue on the [GitHub repository](https://github.com/cylestio/cylestio-monitor/issues) with a detailed description of your problem. 