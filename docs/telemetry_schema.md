# Telemetry Schema Documentation

## Overview

This document describes the standardized JSON telemetry output format used by Cylestio Monitor. The schema follows OpenTelemetry conventions and provides comprehensive monitoring data for LLM operations, tool executions, and system events.

## Base Event Structure

Every telemetry event follows this base structure:

```json
{
    "timestamp": "2024-03-27T15:31:40.622017",        # ISO 8601 timestamp
    "trace_id": "2a8ec755032d4e2ab0db888ab84ef595",   # 32-character hex string
    "span_id": "96d8c2be667e4c78",                    # 16-character hex string
    "parent_span_id": "f1490a668d69d1dc",             # 16-character hex string
    "name": "llm.request",                            # Event name following OTel conventions
    "level": "INFO",                                  # Event severity level
    "agent_id": "weather-agent",                      # Agent identifier
    "attributes": {                                   # Event-specific attributes
        // Framework-specific attributes
    }
}
```

## Core Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `timestamp` | string | ISO 8601 formatted timestamp | Yes |
| `trace_id` | string | 32-character hex string for distributed tracing | Yes |
| `span_id` | string | 16-character hex string for operation identification | Yes |
| `parent_span_id` | string | 16-character hex string for parent operation | No |
| `name` | string | Event name following OpenTelemetry conventions | Yes |
| `level` | string | Event severity (INFO, WARNING, ERROR, etc.) | Yes |
| `agent_id` | string | Identifier for the monitored agent | Yes |
| `attributes` | object | Event-specific attributes | Yes |

## Event Categories

### 1. LLM Events

#### LLM Request
```json
{
    "name": "llm.request",
    "attributes": {
        "llm.request.model": "claude-3-haiku-20240307",
        "llm.request.max_tokens": 1000,
        "llm.request.temperature": 0.7,
        "caller.file": "weather_client.py",
        "caller.line": 117,
        "caller.function": "process_query"
    }
}
```

#### LLM Response
```json
{
    "name": "llm.response",
    "attributes": {
        "llm.response.duration_ms": 64152,
        "llm.response.usage.input_tokens": 493,
        "llm.response.usage.output_tokens": 51,
        "llm.response.stop_reason": "end_turn",
        "caller.file": "weather_client.py",
        "caller.line": 117,
        "caller.function": "process_query"
    }
}
```

### 2. Tool Events

#### Tool Execution
```json
{
    "name": "tool.execution",
    "attributes": {
        "tool.name": "get_weather_alerts",
        "tool.duration_ms": 1254,
        "tool.status": "success",
        "caller.file": "weather_client.py",
        "caller.line": 142,
        "caller.function": "process_query"
    }
}
```

### 3. Error Events
```json
{
    "name": "llm.error",
    "level": "ERROR",
    "attributes": {
        "error.type": "APIConnectionError",
        "error.message": "Failed to connect to API: Connection timeout",
        "llm.request.model": "claude-3-haiku-20240307",
        "caller.file": "weather_client.py",
        "caller.line": 180,
        "caller.function": "process_query"
    }
}
```

## Framework-Specific Events

### LangGraph Events

#### Graph Node Start
```json
{
    "name": "graph.node.start",
    "attributes": {
        "graph.id": "weather_graph",
        "node.id": "process_weather",
        "node.type": "llm",
        "run.id": "weather_graph:process_weather:123"
    }
}
```

#### Graph Node End
```json
{
    "name": "graph.node.end",
    "attributes": {
        "graph.id": "weather_graph",
        "node.id": "process_weather",
        "node.type": "llm",
        "run.id": "weather_graph:process_weather:123",
        "output.content": {...},
        "output.estimated_tokens": 150,
        "performance.duration_ms": 1250,
        "performance.nodes_per_second": 0.8
    }
}
```

### LangChain Events

#### Chain Start
```json
{
    "name": "chain.start",
    "attributes": {
        "chain.id": "weather_chain",
        "chain.type": "ConversationChain",
        "components.llm": "ChatAnthropic",
        "components.memory": "ConversationBufferMemory"
    }
}
```

## Common Event Patterns

### 1. Operation Duration Tracking
- Start events have names ending in `.start` (e.g., `llm.request.start`)
- End events have names ending in `.end` (e.g., `llm.response.end`)
- Duration is tracked in milliseconds in the `duration_ms` attribute
- Start and end events share the same `span_id`

### 2. Error Handling
- Error events have `level: "ERROR"`
- Error details are stored in `error.*` attributes
- Original request context is preserved in attributes
- Stack traces and error locations are included when available

### 3. Performance Metrics
- Duration metrics use `duration_ms` attribute
- Rate metrics use `*_per_second` attributes
- Token usage is tracked in `usage.*_tokens` attributes
- Memory usage is tracked in `memory.*` attributes

## Data Relationships

### 1. Trace Context
- `trace_id` links all events in a single operation
- `span_id` identifies specific operations
- `parent_span_id` creates hierarchical relationships
- Example: A tool call within an LLM request would share the LLM's `trace_id` but have its own `span_id`

### 2. Event Sequences
- Operations typically follow a start → end pattern
- Error events can occur at any point
- Framework-specific events (e.g., graph nodes) can be nested
- All events in a sequence share the same `trace_id`

## Future-Proofing Guidelines

1. **Schema Evolution**
   - All schema changes must maintain backward compatibility
   - New fields should be added to the `attributes` object
   - Deprecated fields should be marked as such but not removed immediately

2. **Event Naming**
   - Follow OpenTelemetry naming conventions
   - Use dot notation for hierarchical names (e.g., `llm.request`, `tool.execution`)
   - Keep names concise but descriptive

3. **Attribute Naming**
   - Use namespaced attributes (e.g., `llm.request.model`, `tool.execution.duration`)
   - Follow OpenTelemetry semantic conventions
   - Use consistent units (e.g., milliseconds for durations)

4. **Data Types**
   - Use appropriate data types for attributes
   - Numbers should be used for metrics (not strings)
   - Booleans for flags
   - Arrays for lists of values
   - Objects for complex data structures

5. **Security and Privacy**
   - Never log sensitive data (PII, credentials)
   - Use data masking for sensitive fields
   - Follow security best practices for data transmission

## Integration Guidelines

1. **API Server**
   - Implement rate limiting
   - Validate event schema
   - Handle batch processing
   - Implement retry mechanisms
   - Monitor API health

2. **Data Processing**
   - Implement data validation
   - Handle schema evolution
   - Process events asynchronously
   - Implement error handling
   - Monitor processing latency

3. **Storage**
   - Implement data retention policies
   - Use appropriate indexes
   - Monitor storage usage
   - Implement backup strategies
   - Handle data archival 