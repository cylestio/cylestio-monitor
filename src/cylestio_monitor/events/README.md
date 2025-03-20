# Cylestio Event Conversion System

This package provides a modular, extensible system for converting framework-specific telemetry events into a standardized format based on OpenTelemetry trace and span concepts.

## Overview

The event conversion system is designed to:

1. Extract common fields from all events (timestamp, level, agent_id, etc.)
2. Identify and properly extract trace/span IDs to enable contextual linking of events
3. Structure dynamic, framework-specific data into dedicated fields
4. Preserve all original data by capturing any unmapped fields in an "extra" field
5. Provide a consistent event categorization system (LLM requests, LLM responses, etc.)

## Architecture

The system is built around these core components:

- **StandardizedEvent**: The unified event schema that all converters produce
- **BaseEventConverter**: Abstract base class defining the interface for all converters
- **Framework-specific converters**: Modules that handle conversion for each supported framework
- **EventConverterFactory**: Factory class for selecting the appropriate converter
- **Event Processor**: Integration point with the existing logging system

## Using the System

### Converting a Raw Event

```python
from cylestio_monitor.events.registry import converter_factory

# Raw event from any source
raw_event = {
    "timestamp": "2025-03-17T14:08:09",
    "level": "INFO",
    "agent_id": "chatbot-agent",
    "event_type": "model_request",
    "channel": "LANGCHAIN",
    "data": {
        # Framework-specific data
    }
}

# Convert to standardized event
standardized_event = converter_factory.convert_event(raw_event)

# Access standardized fields
print(standardized_event.event_category)  # "llm_request"
print(standardized_event.trace_id)        # Extracted trace ID
```

### Creating a Standardized Event from Components

```python
from cylestio_monitor.events.processor import create_standardized_event

# Create a standardized event directly
standardized_event = create_standardized_event(
    agent_id="chatbot-agent",
    event_type="model_request",
    data={
        "llm_type": "ChatAnthropic",
        "prompts": ["User message"],
        "run_id": "12345"
    },
    channel="LANGCHAIN",
    level="info",
    direction="outgoing",
    session_id="session-123"
)
```

### Processing and Logging an Event

```python
from cylestio_monitor.events_processor import process_standardized_event

# Process and log a standardized event
process_standardized_event(
    agent_id="chatbot-agent",
    event_type="model_request",
    data={
        "llm_type": "ChatAnthropic",
        "prompts": ["User message"],
        "run_id": "12345"
    },
    channel="LANGCHAIN",
    level="info",
    direction="outgoing",
    session_id="session-123"
)
```

## Adding Support for a New Framework

To add support for a new framework:

1. Create a new converter class that inherits from `BaseEventConverter`
2. Implement the `convert` method to extract framework-specific fields
3. Register the converter with the `EventConverterFactory`

Example:

```python
# 1. Create a new converter class
from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent

class NewFrameworkConverter(BaseEventConverter):
    def convert(self, event):
        # Start with common fields
        common_fields = self._copy_common_fields(event)
        
        # Extract data field
        data = event.get("data", {})
        
        # Extract trace/span IDs
        trace_span_ids = self._extract_trace_span_ids(event)
        
        # Extract framework-specific fields
        # ...
        
        # Return the standardized event
        return StandardizedEvent(
            # Common fields
            timestamp=common_fields["timestamp"],
            level=common_fields["level"],
            agent_id=common_fields["agent_id"],
            event_type=common_fields["event_type"],
            channel=common_fields["channel"],
            # Trace/span IDs
            trace_id=trace_span_ids.get("trace_id"),
            # Other fields
            # ...
        )

# 2. Register the converter
from cylestio_monitor.events.registry import converter_factory

converter_factory.register_converter("NEW_FRAMEWORK", NewFrameworkConverter())
```

## Event Categories

Events are categorized into the following types:

- **user_interaction**: Events related to user inputs/requests
- **llm_request**: Events where an LLM is being prompted
- **llm_response**: Events where an LLM is responding
- **tool_interaction**: Events related to tool usage
- **system**: System-level events (default)

## Field Descriptions

### Common Fields

- **timestamp**: When the event occurred (ISO format)
- **level**: Log level (INFO, WARNING, ERROR, etc.)
- **agent_id**: Identifier for the agent
- **event_type**: The type of event
- **channel**: Source channel/framework
- **event_category**: Categorization of the event

### OpenTelemetry-Inspired Fields

- **trace_id**: Trace identifier (equivalent to run_id, chain_id, etc.)
- **span_id**: Span identifier for events part of a larger operation
- **parent_span_id**: Parent span identifier for nested operations

### Direction and Session

- **direction**: Direction of event ("incoming" or "outgoing")
- **session_id**: Session identifier

### Structured Data Fields

- **call_stack**: Call stack information
- **security**: Security assessment data
- **performance**: Performance metrics
- **model**: Model details
- **framework**: Framework information
- **request**: Structured request data
- **response**: Structured response data
- **extra**: Any unmapped data 