# Custom Integrations

Cylestio Monitor is designed to work with popular frameworks out of the box, but you can also integrate it with custom systems. This guide explains how to create custom integrations using the v0.1.5 API.

## Logging Custom Events

You can log custom events using the `log_event` function:

```python
from cylestio_monitor.utils.event_logging import log_event

# Log a custom event
log_event(
    name="custom.operation.complete",
    attributes={
        "operation_type": "data_processing",
        "records_processed": 100
    }
)
```

## Creating Custom Spans

For operations that take time, you can create spans to track their duration:

```python
from cylestio_monitor.utils.instrumentation import Span

# Create a span for a custom operation
with Span("data-processing", attributes={"source": "database"}):
    # Your operation code here
    process_data()

    # Additional events within the span
    log_event(
        name="data.processing.step",
        attributes={"step": "validation"}
    )
```

## Instrumenting Custom Functions

You can automatically instrument custom functions:

```python
from cylestio_monitor.utils.instrumentation import instrument_function

# Apply the decorator to any function
@instrument_function
def process_data(data):
    # Function code here
    return transformed_data

# When called, events will be logged automatically
result = process_data(input_data)
```

For class methods:

```python
from cylestio_monitor.utils.instrumentation import instrument_method

class DataProcessor:
    @instrument_method(name_prefix="data_processor")
    def process(self, data):
        # Method code here
        return transformed_data
```

## Custom Error Logging

For error handling, use the specialized `log_error` function:

```python
from cylestio_monitor.utils.event_logging import log_error

try:
    # Your operation
    process_data()
except Exception as e:
    # Log the error with structured information
    log_error(
        name="custom.operation.error",
        error=e,
        attributes={"operation": "data_processing"}
    )
    # Handle or re-raise as needed
    raise
```

## Manually Managing Trace Context

For more control, you can directly manage trace context:

```python
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event

# Start a custom span
span_info = TraceContext.start_span("custom-operation")

try:
    # Your operation code
    log_event(
        name="custom.operation.start",
        attributes={"parameters": "value"}
    )

    result = perform_operation()

    log_event(
        name="custom.operation.complete",
        attributes={"result": "success"}
    )

    return result
except Exception as e:
    log_error(
        name="custom.operation.error",
        error=e
    )
    raise
finally:
    # Always end the span
    TraceContext.end_span()
```

## Best Practices

1. **Consistent Naming**: Use consistent naming for your events, following the pattern `category.operation.action`
2. **Useful Attributes**: Include attributes that provide context about the operation
3. **Proper Nesting**: Nest spans to reflect the hierarchical nature of operations
4. **Error Handling**: Always log errors and ensure spans are properly ended
5. **Security**: Be careful about logging sensitive information in attributes
