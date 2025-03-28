# SDK Reference Overview

The Cylestio Monitor SDK provides a comprehensive API for monitoring and securing AI agents. This reference section documents the core modules and functions available in the SDK.

## Core Modules

The SDK is organized into several core modules:

- **Monitor Module**: Core functionality for enabling and configuring monitoring
- **Events System**: Event processing and handling with OpenTelemetry standards
- **API Client**: Communication with remote endpoints for event collection
- **Trace Context**: Span and trace management for distributed tracing

## Basic Usage

```python
import cylestio_monitor

# Start monitoring
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Stop monitoring when done
cylestio_monitor.stop_monitoring()
```

## Advanced Usage

For more advanced usage, you can interact directly with the lower-level APIs:

```python
from cylestio_monitor.utils.event_logging import log_event
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.instrumentation import Span

# Start a custom span
with Span("custom-operation", attributes={"operation_type": "data_processing"}):
    # Log a custom event within the span
    log_event(
        name="custom.event",
        attributes={"key": "value"}
    )

    # Your code here
    process_data()
```

## Next Steps

Explore the specific module documentation for detailed information:

- [Monitor Module](monitor.md): Main monitoring functionality
- [Events System](events.md): Event processing and handling
- [API Client](api-client.md): Remote API communication and local logging
- [Trace Context](tracing.md): Distributed tracing and span management
