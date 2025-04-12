# Timestamp Guidelines

## Overview

This document provides guidelines for handling timestamps in the Cylestio Monitor system. All events must use UTC timezone with the "Z" suffix in ISO8601 format.

## Timestamp Format

All timestamps in the Cylestio Monitor system must:

1. Use ISO8601 format (`YYYY-MM-DDTHH:MM:SS.sssZ`)
2. Include the UTC timezone with "Z" suffix
3. Maintain millisecond precision when available

Example of a valid timestamp:
```
2023-09-15T14:30:45.123Z
```

## Timestamp Utilities

Always use the timestamp utilities provided in `cylestio_monitor.utils.event_utils` instead of directly generating timestamps:

```python
from cylestio_monitor.utils.event_utils import get_utc_timestamp, format_timestamp

# Get current UTC timestamp as a datetime object
current_time = get_utc_timestamp()

# Format a timestamp with UTC timezone and Z suffix
formatted_time = format_timestamp()  # Current time
formatted_custom = format_timestamp(datetime(2023, 9, 15, 14, 30, 45))  # Custom time
```

## Event Creation

When creating events, always use the factory functions which handle proper timestamp formatting:

```python
from cylestio_monitor.events.factories import create_system_event

event = create_system_event(
    agent_id="my-agent",
    event_type="system.startup",
    data={"version": "1.0.0"},
    # Timestamp will be set to current UTC time if not provided
)
```

## Common Issues and Solutions

1. **Missing Z suffix**: Always use `format_timestamp()` instead of direct `.isoformat()` calls

   ```python
   # Incorrect
   timestamp = datetime.now().isoformat()  # No timezone info, no Z suffix
   
   # Correct
   timestamp = format_timestamp()  # Has UTC timezone and Z suffix
   ```

2. **Timezone inconsistencies**: Always use UTC for consistent event sequencing

   ```python
   # Incorrect
   timestamp = datetime.now()  # Uses local timezone
   
   # Correct
   timestamp = get_utc_timestamp()  # Uses UTC timezone
   ```

3. **Parsing timestamps**: When parsing timestamps from strings, ensure timezone handling

   ```python
   # When parsing timestamps from external sources, convert to UTC
   from cylestio_monitor.utils.event_utils import parse_timestamp
   
   utc_dt = parse_timestamp(external_timestamp)
   ```

## Why UTC with Z Suffix?

- **Consistency**: All events have the same timezone reference
- **Sorting**: Events can be chronologically ordered without timezone conversion
- **Interoperability**: Compatible with most timestamp parsing libraries
- **Clarity**: "Z" suffix clearly indicates UTC timezone 