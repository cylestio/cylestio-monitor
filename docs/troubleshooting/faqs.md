# Frequently Asked Questions

This page answers frequently asked questions about Cylestio Monitor.

## General Questions

### What is Cylestio Monitor?

Cylestio Monitor is a lightweight, drop-in monitoring SDK for AI agents, MCP, and LLM API calls. It provides comprehensive security monitoring, performance tracking, and structured logging capabilities with minimal configuration.

### What frameworks and LLM clients does Cylestio Monitor support?

Currently, Cylestio Monitor supports:

- **MCP**: Version 1.3.0 and above
- **Anthropic Claude**: Via the official `anthropic` Python client
- **Custom frameworks**: Via the flexible patching mechanism

Support for additional LLM clients is planned for future releases.

### Is Cylestio Monitor free to use?

Yes, Cylestio Monitor is open source and free to use under the MIT license. You can find the license details in the [GitHub repository](https://github.com/cylestio/cylestio-monitor).

### Can I use Cylestio Monitor in production?

Yes, Cylestio Monitor is designed for production use. However, as with any monitoring solution, you should thoroughly test it in your specific environment before deploying to production.

## Installation and Setup

### What are the system requirements for Cylestio Monitor?

Cylestio Monitor requires:

- Python 3.11 or higher
- SQLite 3.35.0 or higher (for JSON1 extension support)
- Sufficient disk space for the SQLite database and JSON logs (if enabled)

### Where is the SQLite database stored?

The database file is stored in an OS-specific location determined by the `platformdirs` library:

- **Windows**: `C:\Users\<username>\AppData\Local\cylestio\cylestio-monitor\cylestio_monitor.db`
- **macOS**: `~/Library/Application Support/cylestio-monitor/cylestio_monitor.db`
- **Linux**: `~/.local/share/cylestio-monitor/cylestio_monitor.db`

### Can I change the database location?

Yes, you can change the database location by setting the `CYLESTIO_DB_PATH` environment variable:

```python
import os
os.environ["CYLESTIO_DB_PATH"] = "/path/to/custom/location/cylestio_monitor.db"
```

### How do I enable monitoring for my LLM client?

To enable monitoring for your LLM client, pass the client instance to the `enable_monitoring` function:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_agent",
    llm_client=client
)
```

### How do I enable monitoring for MCP?

To enable monitoring for MCP, call `enable_monitoring` before creating your MCP session:

```python
from cylestio_monitor import enable_monitoring
from mcp import ClientSession

# Enable monitoring
enable_monitoring(agent_id="mcp-project")

# Create and use your MCP client as normal
session = ClientSession(stdio, write)
```

## Configuration

### How do I customize the security keywords?

You can customize the security keywords by editing the global configuration file:

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

### How do I disable security checks?

You can disable security checks by modifying the configuration file:

```yaml
security:
  enabled: false
```

### Can I use a different logging format?

Currently, Cylestio Monitor uses a fixed JSON format for logging. However, you can process the logs in any way you want after they're written to the database or JSON file.

### How do I configure log rotation?

You can configure log rotation in the global configuration file:

```yaml
logging:
  file_rotation: true
  max_file_size_mb: 10
  backup_count: 5
```

## Usage

### How do I query the database for events?

You can query the database using the utility functions in the `db.utils` module:

```python
from cylestio_monitor.db import utils as db_utils

# Get recent events
events = db_utils.get_recent_events(agent_id="my-project", limit=10)

# Get events by type
llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get events from the last 24 hours
recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")
```

### How do I log custom events?

You can log custom events using the `log_event` function:

```python
from cylestio_monitor import log_event

# Log a custom event
log_event(
    event_type="custom_event",
    data={"key": "value"},
    channel="CUSTOM",
    level="info"
)
```

### How do I monitor a custom function?

You can monitor a custom function using the `monitor_call` decorator:

```python
from cylestio_monitor.events_listener import monitor_call

# Original function
def my_function(arg1, arg2):
    return arg1 + arg2

# Patched function
my_function = monitor_call(my_function, "CUSTOM")
```

### How do I clean up old events?

You can clean up old events using the `cleanup_old_events` function:

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 30 days
deleted_count = cleanup_old_events(days=30)
```

## Security

### Is my data secure?

Cylestio Monitor stores data locally on your machine or server. It doesn't send any data to external servers. The security of the data depends on the security of your machine or server.

### Does Cylestio Monitor encrypt the database?

No, Cylestio Monitor doesn't encrypt the database by default. If you need encryption, you should implement it at the file system level or use a database that supports encryption.

### Can Cylestio Monitor prevent all security risks?

No, Cylestio Monitor is designed to help detect and prevent certain types of security risks, but it's not a comprehensive security solution. It should be part of a broader security strategy.

### What types of security risks can Cylestio Monitor detect?

Cylestio Monitor can detect:

- Suspicious or dangerous terms in prompts and tool calls
- Attempts to use dangerous operations or commands
- Unusual patterns of API usage

However, it's not a substitute for proper input validation, authentication, and authorization.

## Performance

### Will Cylestio Monitor slow down my application?

Cylestio Monitor is designed to be lightweight and efficient, but like any monitoring solution, it does add some overhead. In most cases, the overhead is minimal and won't be noticeable in your application.

### How much disk space does Cylestio Monitor use?

The disk space usage depends on the volume of events and how long you keep them. Each event typically uses a few kilobytes of disk space. For high-volume applications, you should implement regular cleanup of old events.

### Can Cylestio Monitor handle high-concurrency scenarios?

Cylestio Monitor uses SQLite as its database, which has limitations in high-concurrency scenarios. If you have a high-concurrency application, you might want to consider using a more robust database solution.

## Troubleshooting

### Why am I not seeing any events in the logs?

If you're not seeing any events in the logs, check:

1. That you've enabled monitoring correctly
2. That you're using the monitored client instance
3. That you have permission to write to the database and log file
4. That you're actually making calls that should be monitored

### Why are my LLM calls being blocked?

LLM calls might be blocked if they contain terms that match the dangerous keywords list. Check the logs for events with the type `LLM_call_blocked` to see what terms triggered the block.

### How do I debug Cylestio Monitor itself?

You can enable debug logging for Cylestio Monitor:

```python
enable_monitoring(
    agent_id="my_agent",
    debug_level="DEBUG"
)
```

This will output detailed debug information to the console.

## Integration

### Can I use Cylestio Monitor with Django?

Yes, you can use Cylestio Monitor with Django. See the [Integration Patterns](../best-practices/integration-patterns.md) guide for an example of integrating with Django.

### Can I use Cylestio Monitor with FastAPI?

Yes, you can use Cylestio Monitor with FastAPI. See the [Integration Patterns](../best-practices/integration-patterns.md) guide for an example of integrating with FastAPI.

### Can I use Cylestio Monitor with AWS Lambda?

Yes, but you'll need to consider the ephemeral nature of Lambda functions. Since Lambda functions are stateless, you might want to use a different database solution that persists between function invocations, such as Amazon RDS or DynamoDB.

### Can I use Cylestio Monitor with Docker?

Yes, you can use Cylestio Monitor with Docker. However, you'll need to ensure that the database directory is persisted between container restarts, either by using a volume or by specifying a different database location.

## Advanced Usage

### Can I extend Cylestio Monitor with custom functionality?

Yes, Cylestio Monitor is designed to be extensible. You can:

- Create custom monitoring channels
- Implement custom security checks
- Add custom event processors
- Integrate with external monitoring systems

### Can I use Cylestio Monitor with a different database?

Currently, Cylestio Monitor is designed to work with SQLite. However, you could potentially modify the `db_manager.py` file to use a different database.

### Can I use Cylestio Monitor in a distributed environment?

Cylestio Monitor is primarily designed for single-machine deployments. For distributed environments, you might want to consider using a centralized logging solution like ELK (Elasticsearch, Logstash, Kibana) or a distributed database.

### How do I visualize the monitoring data?

Cylestio Monitor doesn't include built-in visualization tools. However, since the data is stored in a SQLite database, you can use any SQL-compatible visualization tool, such as:

- Grafana with the SQLite data source
- Metabase
- Custom dashboards using libraries like Plotly or Dash 