# Event Guidelines

## Event Schema

All events in the Cylestio Monitor system follow a standardized schema based on OpenTelemetry concepts:

```json
{
  "timestamp": "2023-09-15T14:30:45.123Z",  // ISO8601 with UTC timezone (Z suffix)
  "level": "INFO",
  "agent_id": "my-agent",
  "name": "event.name",
  "attributes": {
    // Event-specific attributes
  }
}
```

## Timestamp Requirements

All event timestamps MUST:
- Use ISO8601 format
- Include UTC timezone with "Z" suffix
- Be generated using the timestamp utilities in `cylestio_monitor.utils.event_utils`

Example:
```python
from cylestio_monitor.utils.event_utils import format_timestamp

event = {
    "timestamp": format_timestamp(),
    "level": "INFO",
    "agent_id": "my-agent",
    "name": "event.name",
    "attributes": {}
}
```

## Creating Events

Always use the factory functions to create events to ensure proper timestamp formatting:

```python
from cylestio_monitor.events.factories import create_system_event, create_llm_request_event

# System event
system_event = create_system_event(
    agent_id="my-agent",
    event_type="system.startup",
    data={"version": "1.0.0"}
)

# LLM request event
llm_event = create_llm_request_event(
    agent_id="my-agent",
    provider="openai",
    model="gpt-4",
    prompt="Hello, world!"
)
```

## Event Validation

The `StandardizedEvent` class automatically validates timestamps to ensure they follow the required format. When creating custom events, you should either:

1. Use the factory functions mentioned above, or
2. Use the `format_timestamp()` function to generate proper timestamps

Example of validation:

```python
from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.utils.event_utils import format_timestamp

# This will pass validation
valid_event = StandardizedEvent(
    timestamp=format_timestamp(),
    agent_id="my-agent",
    name="custom.event",
    attributes={}
)

# This would fail validation (incorrect timestamp format)
# invalid_event = StandardizedEvent(
#     timestamp="2023-09-15 14:30:45",  # Missing T, no Z suffix
#     agent_id="my-agent",
#     name="custom.event",
#     attributes={}
# )
```

## Timezone Considerations

When working with external systems or user inputs, always convert timestamps to UTC with the Z suffix before storing or processing them:

```python
from cylestio_monitor.utils.event_utils import parse_timestamp, format_timestamp

# Convert an external timestamp to proper format
external_time = "2023-09-15 14:30:45 PDT"
utc_time = parse_timestamp(external_time)
formatted_time = format_timestamp(utc_time)
```

For more detailed information about timestamp handling, see the [Timestamp Guidelines](timestamps.md). 