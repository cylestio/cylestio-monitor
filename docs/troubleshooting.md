# Troubleshooting Guide

This guide covers common issues and their solutions when using Cylestio Monitor.

## Common Issues

### No Events in Log File

**Problem**: You've configured a log file, but no events are being written.

**Solutions**:

1. Check that the directory for the log file exists:
   ```python
   # Make sure the directory exists
   import os
   os.makedirs("output", exist_ok=True)

   # Then start monitoring
   cylestio_monitor.start_monitoring(
       agent_id="my-agent",
       config={"log_file": "output/monitoring.json"}
   )
   ```

2. Verify that the path is writable:
   ```bash
   # Check permissions
   ls -la output/
   ```

3. Ensure that your application is executing the code that would generate events.

### Events Missing Trace Context

**Problem**: Events in your logs don't have trace_id or span_id fields.

**Solution**: Make sure you're calling `start_monitoring` before any operations that generate events:

```python
# Always initialize monitoring first
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Then create clients and perform operations
client = Anthropic()
response = client.messages.create(...)
```

### API Client Connection Issues

**Problem**: Events aren't being sent to your API endpoint.

**Solutions**:

1. Check that your API endpoint is correctly configured:
   ```python
   cylestio_monitor.start_monitoring(
       agent_id="my-agent",
       config={"api_endpoint": "https://api.example.com/events"}
   )

   # Verify the endpoint
   print(cylestio_monitor.get_api_endpoint())
   ```

2. Verify that your API endpoint is reachable:
   ```bash
   # Test the endpoint
   curl -i https://api.example.com/events
   ```

3. Check your application has network access to the endpoint.

### Debug Mode for Troubleshooting

To enable debug logging for troubleshooting:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "debug_level": "DEBUG",
        "log_file": "output/monitoring.json"
    }
)
```

This will output detailed debugging information to the console.

### Framework Not Being Monitored

**Problem**: A supported framework like LangChain is not being monitored.

**Solutions**:

1. Make sure you import and initialize Cylestio Monitor before importing the framework:
   ```python
   import cylestio_monitor
   cylestio_monitor.start_monitoring(agent_id="my-agent")

   # Then import and use the framework
   from langchain.chat_models import ChatAnthropic
   ```

2. Check that you have a compatible version of the framework:
   - LangChain: ≥ 0.1.0
   - LangGraph: ≥ 0.0.19
   - Anthropic SDK: ≥ 0.18.0
   - MCP: ≥ 1.3.0

## Getting Help

If you continue to experience issues:

1. Check the [GitHub Issues](https://github.com/cylestio/cylestio-monitor/issues) for similar problems and solutions
2. Contact support at support@cylestio.com
3. Join our [Discord community](https://discord.gg/cylestio) for real-time help
