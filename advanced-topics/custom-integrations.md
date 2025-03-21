# Custom Integrations

Cylestio Monitor is designed to work with popular LLM clients and MCP out of the box, but you can also integrate it with custom frameworks or tools. This guide explains how to create custom integrations.

## Monitoring Custom Functions

You can monitor any function by using the `monitor_call` decorator from the events listener module:

```python
from cylestio_monitor.events_listener import monitor_call

# Original function
def my_function(arg1, arg2):
    return arg1 + arg2

# Patched function
my_function = monitor_call(my_function, "CUSTOM")

# Now, when you call my_function, it will be monitored
result = my_function(1, 2)
```

The `monitor_call` decorator works with both synchronous and asynchronous functions:

```python
from cylestio_monitor.events_listener import monitor_call

# Original async function
async def my_async_function(arg1, arg2):
    return arg1 + arg2

# Patched async function
my_async_function = monitor_call(my_async_function, "CUSTOM")

# Now, when you call my_async_function, it will be monitored
result = await my_async_function(1, 2)
```

## Monitoring Custom LLM Clients

If you're using a custom LLM client that isn't directly supported, you can still monitor it by using the `monitor_llm_call` decorator:

```python
from cylestio_monitor.events_listener import monitor_llm_call

# Original LLM client method
def generate_text(prompt, max_tokens=100):
    # Implementation of the LLM API call
    return "Generated text"

# Patched LLM client method
generate_text = monitor_llm_call(generate_text, "LLM")

# Now, when you call generate_text, it will be monitored
response = generate_text("Hello, AI!", max_tokens=50)
```

Alternatively, you can use the `enable_monitoring` function with a custom method path:

```python
from cylestio_monitor import enable_monitoring
from custom_llm_client import CustomLLMClient

# Create your custom LLM client
client = CustomLLMClient()

# Enable monitoring with a custom method path
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    llm_method_path="generate"  # The method that makes the API call
)

# Use your client as normal
response = client.generate(prompt="Hello, AI!")
```

## Logging Custom Events

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

This is useful for integrating with custom frameworks or tools that don't fit the standard LLM or MCP patterns.

## Creating a Custom Channel

You can create a custom channel to categorize your events:

1. Add the channel to the configuration file:
   ```yaml
   monitoring:
     channels:
       - "SYSTEM"
       - "LLM"
       - "API"
       - "MCP"
       - "MY_CUSTOM_CHANNEL"
   ```

2. Use the channel in your logging:
   ```python
   from cylestio_monitor import log_event
   
   log_event("custom_event", {"key": "value"}, channel="MY_CUSTOM_CHANNEL")
   ```

## Integrating with a Custom Framework

Here's a more complete example of integrating Cylestio Monitor with a custom framework:

```python
from cylestio_monitor import enable_monitoring, log_event
from cylestio_monitor.events_listener import monitor_call

# Enable monitoring
enable_monitoring(agent_id="my_custom_framework")

# Define a custom channel
CUSTOM_CHANNEL = "MY_FRAMEWORK"

# Patch key functions in the framework
def patch_framework(framework):
    # Patch the main entry point
    framework.process = monitor_call(framework.process, CUSTOM_CHANNEL)
    
    # Patch other important functions
    framework.analyze = monitor_call(framework.analyze, CUSTOM_CHANNEL)
    framework.generate = monitor_call(framework.generate, CUSTOM_CHANNEL)
    
    # Log that the framework was patched
    log_event(
        "framework_patch",
        {"framework": framework.__class__.__name__},
        CUSTOM_CHANNEL
    )
    
    return framework

# Use the patched framework
my_framework = patch_framework(MyFramework())
result = my_framework.process(input_data)
```

## Custom Security Checks

You can implement custom security checks by extending the events processor:

```python
from cylestio_monitor.events_processor import contains_suspicious, contains_dangerous
from cylestio_monitor import log_event

def custom_security_check(data):
    # Check if the data contains suspicious content
    if contains_suspicious(str(data)):
        log_event(
            "custom_security_warning",
            {"data": data, "alert": "suspicious"},
            "SECURITY",
            "warning"
        )
        return "suspicious"
    
    # Check if the data contains dangerous content
    if contains_dangerous(str(data)):
        log_event(
            "custom_security_error",
            {"data": data, "alert": "dangerous"},
            "SECURITY",
            "error"
        )
        return "dangerous"
    
    return "none"

# Use the custom security check
def process_input(input_data):
    # Check the input data for security issues
    alert_level = custom_security_check(input_data)
    
    # If the input is dangerous, block it
    if alert_level == "dangerous":
        raise SecurityException("Dangerous input detected")
    
    # Process the input
    result = do_processing(input_data)
    
    return result
```

## Integration with External Monitoring Systems

You can integrate Cylestio Monitor with external monitoring systems by implementing a custom event handler:

```python
from cylestio_monitor.db import utils as db_utils
import requests
import json
import time

def send_events_to_external_system(external_api_url, api_key, interval_seconds=60):
    """
    Periodically sends events to an external monitoring system.
    
    Args:
        external_api_url: URL of the external API
        api_key: API key for authentication
        interval_seconds: How often to send events (in seconds)
    """
    last_event_id = 0
    
    while True:
        # Get new events since the last check
        conn = sqlite3.connect(db_utils.get_db_path())
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT * FROM events
            WHERE id > ?
            ORDER BY id ASC
        """, (last_event_id,))
        
        events = []
        for row in cursor:
            event = dict(row)
            events.append(event)
            last_event_id = max(last_event_id, event["id"])
        
        conn.close()
        
        # Send events to the external system
        if events:
            response = requests.post(
                external_api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                data=json.dumps({"events": events})
            )
            
            if response.status_code != 200:
                print(f"Error sending events: {response.text}")
        
        # Wait for the next interval
        time.sleep(interval_seconds)

# Start the event forwarder in a background thread
import threading
threading.Thread(
    target=send_events_to_external_system,
    args=("https://api.example.com/events", "your_api_key"),
    daemon=True
).start()
```

## Best Practices for Custom Integrations

1. **Use appropriate channels**: Create custom channels that make sense for your integration.

2. **Follow the event structure**: Make sure your custom events follow the same structure as the built-in events.

3. **Include security checks**: Implement security checks for your custom integrations to detect and block dangerous operations.

4. **Document your integration**: Document how your custom integration works, what events it generates, and what security checks it performs.

5. **Test thoroughly**: Test your custom integration thoroughly to ensure it works as expected and doesn't interfere with the normal operation of your code. 