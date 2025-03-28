# Trace Context and Spans

Cylestio Monitor provides OpenTelemetry-compliant tracing capabilities that allow you to track hierarchical relationships between operations.

## Overview

Trace context enables distributed tracing across different components of your AI agent. It consists of:

- **Trace ID**: A unique identifier for a trace that spans the entire operation
- **Span ID**: An identifier for a specific operation within a trace
- **Parent Span ID**: An identifier linking a span to its parent span

## Trace Context Management

The `TraceContext` class provides methods for managing trace context:

```python
from cylestio_monitor.utils.trace_context import TraceContext

# Start a new span
span_info = TraceContext.start_span("data-processing")

try:
    # Your code here
    process_data()
finally:
    # Always end the span
    TraceContext.end_span()
```

## Using Spans with Context Managers

For more structured code, you can use the `Span` context manager:

```python
from cylestio_monitor.utils.instrumentation import Span

# Create a span using the context manager
with Span("data-processing", attributes={"data_source": "database"}):
    # Code within this block is tracked as part of the span
    process_data()
    # When the block exits, the span is automatically ended
```

## Function and Method Instrumentation

You can automatically instrument functions and methods:

```python
from cylestio_monitor.utils.instrumentation import instrument_function, instrument_method

# Instrument a function
@instrument_function
def process_data():
    # Function will automatically have start and end events logged
    # with proper trace context
    pass

# Instrument a class method with a custom name prefix
class DataProcessor:
    @instrument_method(name_prefix="data_processor")
    def process(self):
        # Method will log events with names like "data_processor.start"
        pass
```

## Hierarchical Spans

Spans can be nested to represent hierarchical relationships:

```python
from cylestio_monitor.utils.instrumentation import Span

# Create a parent span
with Span("data-processing"):
    # Do some initial work
    prepare_data()

    # Create a child span
    with Span("data-transformation"):
        # This operation is tracked as a child of "data-processing"
        transform_data()

    # Create another child span
    with Span("data-validation"):
        # This is also a child of "data-processing"
        validate_data()
```

## Span Attributes

You can add attributes to spans to provide additional context:

```python
from cylestio_monitor.utils.instrumentation import Span

# Create a span with attributes
with Span("database-query", attributes={
    "database.name": "users",
    "database.operation": "select",
    "database.query": "SELECT * FROM users WHERE id = ?",
}):
    # Run the database query
    result = db.execute_query(query, params)
```

## Accessing Current Trace Context

You can access the current trace context to get the trace ID, span ID, etc.:

```python
from cylestio_monitor.utils.trace_context import TraceContext

# Get the current trace context
context = TraceContext.get_current_context()
trace_id = context.get("trace_id")
span_id = context.get("span_id")
agent_id = context.get("agent_id")
```

## Best Practices

1. **Always End Spans**: Use `try/finally` or context managers to ensure spans are always ended
2. **Use Meaningful Names**: Choose descriptive span names that indicate what operation is being performed
3. **Hierarchical Spans**: Structure spans to represent the logical hierarchy of operations
4. **Add Relevant Attributes**: Include attributes that will help with debugging and monitoring
5. **Use Function Instrumentation**: For frequently called functions, use decorators for cleaner code
