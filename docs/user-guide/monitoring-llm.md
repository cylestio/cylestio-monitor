# Monitoring LLM Calls

## Supported LLM Providers

- **Anthropic Claude**: Via the official `anthropic` Python client
- **Custom LLM clients**: Via the flexible patching mechanism

## Basic Setup

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

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

## What Gets Monitored

### Request Data
- Prompt content
- Model
- Parameters
- Timestamp
- Security check results

### Response Data
- Response content
- Duration
- Token usage
- Error information

## Security Checks

- **Suspicious Content**: Flagged but allowed to proceed
- **Dangerous Content**: Blocked by default

## Example Events

### LLM Call Start Event

```json
{
  "event": "LLM_call_start",
  "data": {
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "messages": [
      {
        "role": "user",
        "content": "Hello, Claude!"
      }
    ],
    "alert": "none"
  },
  "timestamp": "2024-03-10T22:15:30.123456",
  "channel": "LLM"
}
```

### LLM Call Finish Event

```json
{
  "event": "LLM_call_finish",
  "data": {
    "duration_ms": 1234,
    "response": {
      "id": "msg_01ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Hello! I'm Claude, an AI assistant created by Anthropic. How can I help you today?"
        }
      ],
      "model": "claude-3-sonnet-20240229",
      "stop_reason": "end_turn",
      "stop_sequence": null,
      "usage": {
        "input_tokens": 10,
        "output_tokens": 25
      }
    }
  },
  "timestamp": "2024-03-10T22:15:31.456789",
  "channel": "LLM"
}
```

## Accessing LLM Events

```python
from cylestio_monitor.db import utils as db_utils

# Get all LLM events for a specific agent
llm_events = db_utils.get_events_by_channel("LLM", agent_id="my-project")

# Get LLM call start events
start_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

# Get LLM call finish events
finish_events = db_utils.get_events_by_type("LLM_call_finish", agent_id="my-project")

# Get blocked LLM calls
blocked_events = db_utils.get_events_by_type("LLM_call_blocked", agent_id="my-project")
```

## Next Steps

Now that you understand how to monitor LLM calls, you can:

1. Learn about [monitoring MCP](monitoring-mcp.md)
2. Explore the [security features](security-features.md) in more detail
3. Check out the [logging options](logging-options.md) 