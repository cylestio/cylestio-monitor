# API Client and Event Logging

The API Client module provides functions for sending monitoring events to a remote endpoint and logging them locally.

## Overview

Cylestio Monitor sends monitoring events to a remote REST API endpoint and/or logs them to JSON files. This approach enables centralized collection and analysis of monitoring data from multiple agents and applications.

## Event Logging

### Local JSON Logging

For local development or when a remote API endpoint is not available, Cylestio Monitor logs events to JSON files:

```python
import cylestio_monitor

# Enable monitoring with JSON logging
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "log_file": "output/monitoring.json"
    }
)
```

The log file will contain OpenTelemetry-compliant events in JSON format, one per line:

```json
{"timestamp": "2024-03-27T15:31:40.622017", "trace_id": "2a8ec755032d4e2ab0db888ab84ef595", "span_id": "96d8c2be667e4c78", "name": "llm.call.start", "attributes": {"model": "claude-3-haiku"}, "agent_id": "my-agent"}
{"timestamp": "2024-03-27T15:31:42.891342", "trace_id": "2a8ec755032d4e2ab0db888ab84ef595", "span_id": "a1d8c2be6b7e4c90", "parent_span_id": "96d8c2be667e4c78", "name": "llm.call.finish", "attributes": {"model": "claude-3-haiku", "duration_ms": 2269}, "agent_id": "my-agent"}
```

### Remote API Logging

To send events to a remote API endpoint:

```python
import cylestio_monitor

# Enable monitoring with a remote API endpoint
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "api_endpoint": "https://api.example.com/events"
    }
)
```

You can combine both local and remote logging:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "log_file": "output/monitoring.json",
        "api_endpoint": "https://api.example.com/events"
    }
)
```

## Event Structure

Events follow the OpenTelemetry standard schema:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO-formatted timestamp |
| `trace_id` | string | Trace identifier for distributed tracing |
| `span_id` | string | Span identifier within a trace |
| `parent_span_id` | string | (Optional) Parent span identifier |
| `name` | string | Event name (e.g., "llm.call.start") |
| `attributes` | object | Event attributes/metadata |
| `agent_id` | string | ID of the agent |

## Configuration

### Environment Variables

You can configure the API client using environment variables:

| Variable | Description |
|----------|-------------|
| `CYLESTIO_API_ENDPOINT` | URL of the remote API endpoint |

### Direct Configuration

You can configure both the API endpoint and log file when enabling monitoring:

```python
import cylestio_monitor

# Start monitoring with API endpoint and JSON logging
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "api_endpoint": "https://api.example.com/events",
        "log_file": "output/monitoring.json"
    }
)
```

## Custom Event Logging

You can log custom events using the `log_event` function:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log a custom event
log_event(
    name="custom.operation.complete",
    attributes={
        "records_processed": 100,
        "operation_type": "data_processing"
    }
)
```

For error events, use the `log_error` function:

```python
from cylestio_monitor.utils.event_logging import log_error

try:
    # Your code here
    process_data()
except Exception as e:
    # Log the error
    log_error(
        name="custom.operation.error",
        error=e,
        attributes={"operation_type": "data_processing"}
    )
```

## Best Practices

- Configure a reliable API endpoint with high availability
- Include appropriate authentication in your production API endpoint
- Monitor API client logs for connection issues
- Implement rate limiting in your API endpoint
- Consider adding a local queue or batch processing for high-volume applications
