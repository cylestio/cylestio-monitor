# API Client

The API Client module provides functions for sending monitoring events to a remote endpoint.

## Overview

Cylestio Monitor sends all monitoring events to a remote REST API endpoint. The endpoint URL can be configured through environment variables or directly in code. This approach enables centralized collection and analysis of monitoring data from multiple agents and applications.

## API Client

The `ApiClient` class provides a simple interface for sending telemetry events to a remote endpoint.

### Initialization

```python
from cylestio_monitor.api_client import ApiClient, get_api_client

# Create an ApiClient instance with an explicit endpoint
client = ApiClient("https://api.example.com/events")

# Or use environment variables
import os
os.environ["CYLESTIO_API_ENDPOINT"] = "https://api.example.com/events"
client = ApiClient()  # Will use the environment variable

# Get a singleton instance (recommended approach)
client = get_api_client()
```

### Sending Events

```python
from cylestio_monitor.api_client import get_api_client

# Get the API client
client = get_api_client()

# Send an event
success = client.send_event({
    "event_type": "custom_event",
    "timestamp": "2023-03-20T12:34:56.789Z",
    "agent_id": "my-agent",
    "level": "INFO",
    "channel": "CUSTOM",
    "data": {
        "message": "This is a custom event",
        "custom_field": "custom value"
    }
})

if success:
    print("Event sent successfully")
else:
    print("Failed to send event")
```

### High-Level API

For most use cases, you should use the high-level `send_event_to_api` function, which handles the details of creating and formatting the event:

```python
from cylestio_monitor.api_client import send_event_to_api

# Send an event
success = send_event_to_api(
    agent_id="my-agent",
    event_type="custom_event",
    data={"message": "This is a custom event"},
    channel="CUSTOM",
    level="info"
)
```

## Event Schema

Events sent to the remote API follow this schema:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO-formatted timestamp |
| `agent_id` | string | ID of the agent |
| `event_type` | string | Type of event |
| `channel` | string | Event channel (e.g., "SYSTEM", "LLM") |
| `level` | string | Event level (e.g., "INFO", "WARNING") |
| `data` | object | Event data |
| `direction` | string | (Optional) Event direction ("incoming" or "outgoing") |
| `session_id` | string | (Optional) Session ID |
| `conversation_id` | string | (Optional) Conversation ID |

## Configuration

### Environment Variables

You can configure the API client using environment variables:

| Variable | Description |
|----------|-------------|
| `CYLESTIO_API_ENDPOINT` | URL of the remote API endpoint |

### Direct Configuration

You can also configure the API endpoint directly when enabling monitoring:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring with API endpoint
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)
```

## Error Handling

The API client handles errors gracefully to ensure monitoring doesn't impact your application's performance:

- If the API endpoint is unavailable, the error is logged but doesn't affect your application
- If the API returns an error response, it's logged for debugging
- If no API endpoint is configured, events are only logged to file (if configured)

## Best Practices

- Configure a reliable API endpoint with high availability
- Include appropriate authentication in your production API endpoint
- Monitor API client logs for connection issues
- Implement rate limiting in your API endpoint
- Consider adding a local queue or batch processing for high-volume applications 