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

- Python 3.12 or higher
- Requests library for API communication
- Sufficient disk space for JSON logs (if enabled)

### Where are monitoring events sent?

Events are sent to a remote API endpoint specified in your configuration. This allows for centralized collection and analysis of monitoring data from multiple agents and applications.

### Can I change the API endpoint?

Yes, you can change the API endpoint in several ways:

```python
# Method 1: Using environment variables
import os
os.environ["CYLESTIO_API_ENDPOINT"] = "https://api.example.com/events"

# Method 2: Using configuration when enabling monitoring
from cylestio_monitor import enable_monitoring
enable_monitoring(
    agent_id="my_agent",
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)
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
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)
```

### How do I enable monitoring for MCP?

To enable monitoring for MCP, call `enable_monitoring` before creating your MCP session:

```python
from cylestio_monitor import enable_monitoring
from mcp import ClientSession

# Enable monitoring
enable_monitoring(
    agent_id="mcp-project",
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)

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

Currently, Cylestio Monitor uses a fixed JSON format for logging. However, you can process the logs in any way you want after they're sent to the API endpoint or written to the JSON file.

### How do I configure log rotation?

You can configure log rotation in the global configuration file:

```yaml
logging:
  file_rotation: true
  max_file_size_mb: 10
  backup_count: 5
```

## Usage

### What happens if the API endpoint is unavailable?

Cylestio Monitor is designed to handle API endpoint failures gracefully. If the API endpoint is unavailable:

1. The error is logged to your application logs
2. If file logging is enabled, events will still be written to the JSON log file
3. Your application continues to run without interruption

### How do I manually send events to the API?

You can manually send events using the API client:

```python
from cylestio_monitor.api_client import send_event_to_api

# Send a custom event
send_event_to_api(
    agent_id="my-agent",
    event_type="custom-event",
    data={
        "message": "Something interesting happened",
        "custom_field": "custom value"
    },
    channel="CUSTOM",
    level="info"
)
```

### How do I check if events are being sent successfully?

You can check the status of event transmission in your application logs. Look for log entries from the `cylestio_monitor.api_client` logger:

```
2023-03-20 12:34:56 - cylestio_monitor.api_client - DEBUG - Event sent to API endpoint: https://api.example.com/events
```

Or errors, if there are any:

```
2023-03-20 12:34:56 - cylestio_monitor.api_client - ERROR - Failed to send event to API: 500 - Internal Server Error
```

### Does Cylestio Monitor handle sensitive data securely?

Cylestio Monitor includes a data masking system that can automatically redact sensitive information like credit card numbers, social security numbers, and other PII before sending the data to the API endpoint. You can configure data masking patterns in the configuration file.

### Can I implement custom API authentication?

The current version of Cylestio Monitor does not include built-in authentication for the API endpoint. If your API requires authentication, consider:

1. Setting up a service that accepts unauthenticated requests from Cylestio Monitor and then forwards them to your authenticated API
2. Using an API endpoint that supports IP-based restrictions
3. Using an API gateway with API keys
4. Implementing a custom client by extending the `ApiClient` class

### How do I handle high-volume monitoring?

For high-volume applications, consider:

1. Setting up a scalable API endpoint that can handle the load
2. Using a queue or buffer service
3. Sampling or filtering events before sending them
4. Setting up local JSON file logging as a backup

## Technical Details

### What is the format of the events sent to the API?

Events are sent as JSON objects with the following structure:

```json
{
  "timestamp": "2023-03-20T12:34:56.789Z",
  "agent_id": "my-agent",
  "event_type": "llm_request",
  "channel": "LLM",
  "level": "INFO",
  "data": {
    "prompt": "Tell me about AI monitoring",
    "model": "claude-3-opus-20240229"
  },
  "direction": "outgoing"
}
```

### Can I use Cylestio Monitor with serverless functions?

Yes, Cylestio Monitor can be used with serverless functions. However, keep in mind:

1. Cold starts might introduce delays in the first event transmission
2. API endpoint configuration should be done with each function invocation
3. You may want to increase the timeout for API requests in high-latency environments

### Can I use Cylestio Monitor with Docker?

Yes, you can use Cylestio Monitor with Docker. Make sure your Dockerfile includes the necessary dependencies:

```dockerfile
FROM python:3.12

# Install Cylestio Monitor
RUN pip install cylestio-monitor requests

# Set API endpoint
ENV CYLESTIO_API_ENDPOINT="https://api.example.com/events"

# ... rest of your Dockerfile
```

### How does Cylestio Monitor handle request failures?

Cylestio Monitor handles request failures by:

1. Logging the error for debugging
2. Returning control to your application without blocking
3. Ensuring your application's performance isn't affected by monitoring issues
4. Attempting to log to file if API endpoint is unavailable and file logging is enabled

### What's the overhead of using Cylestio Monitor?

Cylestio Monitor is designed to be lightweight. The overhead includes:

1. HTTP request time to the API endpoint (async, non-blocking)
2. JSON serialization of event data
3. Basic security scanning of prompts and responses
4. Optional file I/O for JSON logging

Most operations complete in milliseconds and shouldn't noticeably impact your application's performance.

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