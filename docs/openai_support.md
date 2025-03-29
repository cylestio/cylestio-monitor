# OpenAI Support in Cylestio Monitor

Cylestio Monitor now supports automatic monitoring of OpenAI API calls. This guide explains how to use this feature and how it works.

## Overview

The OpenAI integration provides the following capabilities:

- Automatic monitoring of **ChatCompletions** API calls
- Automatic monitoring of **Completions** API calls (legacy)
- Telemetry collection for request and response data
- Token usage tracking
- Security scanning of prompts and responses
- Automatic tracing of API call execution

## Getting Started

Using the OpenAI monitoring feature is simple - it works automatically once you've initialized Cylestio Monitor.

### Basic Usage

```python
# Import Cylestio Monitor
from cylestio_monitor import start_monitoring

# Initialize monitoring BEFORE importing OpenAI
start_monitoring(agent_id="my-agent")

# Import OpenAI
from openai import OpenAI

# Create a client - it will be automatically monitored
client = OpenAI(api_key="your-api-key")

# Use the client normally - all calls will be monitored
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## How It Works

The OpenAI integration uses a technique called "monkey patching" to intercept API calls without changing your code. When you initialize Cylestio Monitor, it:

1. Detects if OpenAI is installed
2. Patches the OpenAI client constructor to automatically monitor all new instances
3. Intercepts API calls to collect telemetry and security data
4. Logs the data for analysis

The monitoring is non-intrusive and doesn't change the behavior of the OpenAI API.

## Monitored API Methods

The following OpenAI API methods are monitored:

| API Method | Status | Description |
|------------|--------|-------------|
| `chat.completions.create` | ✅ Supported | Modern chat completion API |
| `completions.create` | ✅ Supported | Legacy text completion API |

## Collected Telemetry

For each API call, Cylestio Monitor collects the following telemetry:

### Request Data
- Model name
- Request type (chat_completion or completion)
- Request parameters (temperature, max_tokens, etc.)
- Timestamp
- Messages/prompt content

### Response Data
- Response ID
- Model name
- Response content
- Finish reason
- Duration (ms)
- Token usage (input, output, total)

### Security Scanning

The integration automatically scans messages for potentially sensitive content, such as:
- API keys
- Credentials
- System command patterns
- Security-relevant keywords

If detected, an additional security event is logged with appropriate details.

## Advanced Configuration

You can configure the OpenAI monitoring behavior by passing configuration parameters to `start_monitoring`:

```python
start_monitoring(
    agent_id="my-agent",
    config={
        "debug_level": "DEBUG",  # Set to DEBUG for detailed logs
        "development_mode": True  # Enable development features
    }
)
```

## Example

Here's a complete example of using Cylestio Monitor with OpenAI:

```python
import os
from cylestio_monitor import start_monitoring, stop_monitoring
from openai import OpenAI

# Initialize monitoring
start_monitoring(agent_id="openai-example-agent")

# Create an OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

try:
    # Use the client normally
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about AI monitoring."}
        ]
    )

    print(response.choices[0].message.content)

finally:
    # Always stop monitoring when done
    stop_monitoring()
```

## Troubleshooting

If you encounter issues with OpenAI monitoring:

1. Make sure you call `start_monitoring()` before importing OpenAI
2. Enable debug logging by setting `debug_level` to `"DEBUG"`
3. Check if your OpenAI package version is supported (requires openai>=1.0.0)
4. Verify that your API key is valid and correctly configured

## Best Practices

- Initialize monitoring at the earliest point in your application
- Always call `stop_monitoring()` at application shutdown
- Use try/finally blocks to ensure monitoring is stopped
- For Lambda or serverless environments, initialize monitoring in the handler function
