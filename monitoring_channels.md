# Monitoring Channels

Monitoring channels provide a way to organize and route events in Cylestio Monitor. This allows for flexible event handling and integration with various systems.

## Overview

Channels act as logical groupings for events, allowing you to:

- Filter events by channel
- Apply different processing rules to different channels
- Route events to different destinations
- Configure channel-specific settings

## Built-in Channels

Cylestio Monitor includes several built-in channels:

| Channel | Description |
|---------|-------------|
| `SYSTEM` | System-level events (startup, shutdown, configuration changes) |
| `LLM` | Events related to LLM API calls |
| `SECURITY` | Security-related events (alerts, blocks, warnings) |
| `MCP` | Events related to Model Context Protocol operations |
| `API` | General API call events |
| `DATABASE` | Database-related events |
| `CUSTOM` | Default channel for custom events |

## Using Channels

### Specifying Channels for Events

When emitting events, you can specify the channel:

```python
from cylestio_monitor import emit_event

emit_event(
    event_type="custom",
    agent_id="my_agent",
    data={"action": "user_login"},
    severity="info",
    channel="USER_ACTIVITY"  # Custom channel
)
```

### Filtering Events by Channel

You can filter events by channel when retrieving them:

```python
from cylestio_monitor import get_events

# Get only security events
security_events = get_events(channel="SECURITY")
```

### Channel-specific Handlers

You can register handlers for specific channels:

```python
from cylestio_monitor import register_channel_handler

def security_handler(event):
    # Process security events
    if event.severity == "high":
        send_alert(event)
    return True

register_channel_handler(
    channel="SECURITY",
    handler=security_handler
)
```

## Custom Channels

You can define your own custom channels for specific use cases:

```python
from cylestio_monitor import register_channel

# Register a custom channel
register_channel(
    name="AUDIT",
    description="Audit-related events",
    config={
        "retention_days": 365,  # Keep audit events for a year
        "encryption": True      # Encrypt audit events
    }
)
```

## Channel Configuration

Each channel can have its own configuration:

```python
from cylestio_monitor import configure_channel

# Configure the SECURITY channel
configure_channel(
    name="SECURITY",
    config={
        "alert_threshold": "medium",
        "notify_admin": True,
        "log_level": "debug"
    }
)
```

## Channel Outputs

Channels can be configured to output events to different destinations:

### File Output

```python
from cylestio_monitor import add_channel_output

# Send security events to a dedicated log file
add_channel_output(
    channel="SECURITY",
    output_type="file",
    config={
        "path": "/var/log/cylestio/security.log",
        "format": "json",
        "rotation": "daily"
    }
)
```

### Webhook Output

```python
from cylestio_monitor import add_channel_output

# Send security events to a webhook
add_channel_output(
    channel="SECURITY",
    output_type="webhook",
    config={
        "url": "https://security.example.com/webhook",
        "headers": {"Authorization": "Bearer token123"},
        "retry_count": 3
    }
)
```

### Database Output

All events are stored in the database by default, but you can configure specific database settings per channel:

```python
from cylestio_monitor import configure_channel_database

# Configure database settings for the AUDIT channel
configure_channel_database(
    channel="AUDIT",
    config={
        "table": "audit_events",
        "retention_days": 365,
        "encryption": True
    }
)
```

## Best Practices

- Use channels to logically separate different types of events
- Create custom channels for specific business domains
- Configure appropriate retention policies for each channel
- Use channel-specific handlers for specialized processing
- Consider security and compliance requirements when configuring channels

## Next Steps

- Learn about the [Events System](sdk-reference/events.md)
- Explore [Custom Integrations](advanced-topics/custom-integrations.md)
- See [Security Features](user-guide/security-features.md) for security-related channels 