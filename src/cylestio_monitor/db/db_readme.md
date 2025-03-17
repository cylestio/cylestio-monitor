# Cylestio Monitor Database Schema

## Overview

This document outlines the optimized relational database schema for Cylestio Monitor's monitoring system. The schema is designed to efficiently store and query data related to AI agent monitoring, including LLM interactions, tool usage, security alerts, and performance metrics.

## Schema Design

The database schema follows a normalized approach with specialized tables for different types of events, while maintaining flexibility through strategic use of JSON fields for variable data.

### Entity Relationship Diagram

```
+----------------+        +-------------------+        +----------------------+
|    agents      |        |     sessions      |        |    conversations     |
+----------------+        +-------------------+        +----------------------+
| id (PK)        |<---+   | id (PK)           |<---+   | id (PK)              |
| agent_id       |    |   | agent_id (FK)     |    |   | session_id (FK)      |
| name           |    |   | start_time        |    |   | start_time           |
| description    |    |   | end_time          |    |   | end_time             |
| created_at     |    |   | metadata (JSON)   |    |   | metadata (JSON)      |
| last_seen      |    |   +-------------------+    |   +----------------------+
| metadata (JSON)|                                 |
+----------------+                                 |
       ^                                           |
       |                                           |
       |                                           |
+------+---------+  +------------------+   +-------+------+  +-------------------+
|    events      |  | event_security   |   |    llm_calls  |  |   tool_calls      |
+----------------+  +------------------+   +--------------+  +-------------------+
| id (PK)        |  | id (PK)          |   | id (PK)      |  | id (PK)           |
| agent_id (FK)  |  | event_id (FK)    |   | event_id (FK)|  | event_id (FK)     |
| session_id (FK)|  | alert_level      |   | model        |  | tool_name         |
| conv_id (FK)   |  | matched_terms    |   | prompt       |  | input_params      |
| event_type     |  | reason           |   | response     |  | output_result     |
| channel        |  | source_field     |   | tokens_in    |  | success           |
| level          |  +------------------+   | tokens_out   |  | error_message     |
| timestamp      |                         | duration_ms  |  | duration_ms       |
| direction      |  +------------------+   | is_stream    |  | blocking          |
| data (JSON)    |  | performance_metrics| | temperature  |  +-------------------+
+----------------+  +------------------+   | cost         |
                    | id (PK)          |   +--------------+
                    | event_id (FK)    |                     +-------------------+
                    | memory_usage     |                     |  security_alerts  |
                    | cpu_usage        |                     +-------------------+
                    | duration_ms      |                     | id (PK)           |
                    | tokens_processed |                     | event_id (FK)     |
                    | cost             |                     | alert_type        |
                    +------------------+                     | severity          |
                                                             | description       |
                                                             | matched_terms     |
                                                             | action_taken      |
                                                             | timestamp         |
                                                             +-------------------+
```

### Table Descriptions

#### agents

Stores information about the AI agents being monitored.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agent_id | TEXT | Unique identifier from the SDK |
| name | TEXT | Optional agent name |
| description | TEXT | Optional agent description |
| created_at | TIMESTAMP | When the agent was first created |
| last_seen | TIMESTAMP | When the agent was last active |
| metadata | JSON | Flexible agent metadata (framework info, version, etc.) |

#### sessions

Tracks individual execution sessions of an agent.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agent_id | INTEGER | Foreign key to the agents table |
| start_time | TIMESTAMP | Session start timestamp |
| end_time | TIMESTAMP | Session end timestamp (null if active) |
| metadata | JSON | Flexible session metadata |

#### conversations

Tracks conversations within sessions.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | INTEGER | Foreign key to the sessions table |
| start_time | TIMESTAMP | Conversation start timestamp |
| end_time | TIMESTAMP | Conversation end timestamp (null if active) |
| metadata | JSON | Flexible conversation metadata |

#### events

Core table for all monitoring events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| agent_id | INTEGER | Foreign key to the agents table |
| session_id | INTEGER | Foreign key to the sessions table (optional) |
| conv_id | INTEGER | Foreign key to the conversations table (optional) |
| event_type | TEXT | Type of event (llm_request, llm_response, tool_call, etc.) |
| channel | TEXT | Event channel (SYSTEM, LLM, LANGCHAIN, etc.) |
| level | TEXT | Event level (info, warning, error, etc.) |
| timestamp | TIMESTAMP | Event timestamp |
| direction | TEXT | Direction for chat events (incoming/outgoing) |
| data | JSON | Additional event data not captured in specialized tables |

#### llm_calls

Detailed information about LLM API calls.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key to the events table |
| model | TEXT | LLM model used |
| prompt | TEXT | The prompt sent to the LLM |
| response | TEXT | The response received from the LLM |
| tokens_in | INTEGER | Number of input tokens |
| tokens_out | INTEGER | Number of output tokens |
| duration_ms | INTEGER | Duration of the call in milliseconds |
| is_stream | BOOLEAN | Whether streaming was used |
| temperature | REAL | Temperature setting used for generation |
| cost | REAL | Estimated cost of the call |

#### tool_calls

Detailed information about tool/function calls.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key to the events table |
| tool_name | TEXT | Name of the tool |
| input_params | JSON | Input parameters to the tool |
| output_result | JSON | Output result of the tool call |
| success | BOOLEAN | Whether the call was successful |
| error_message | TEXT | Error message if the call failed |
| duration_ms | INTEGER | Duration of the call in milliseconds |
| blocking | BOOLEAN | Whether the call was blocking |

#### event_security

Security-related information for events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key to the events table |
| alert_level | TEXT | Alert level (none, suspicious, dangerous) |
| matched_terms | JSON | Terms that triggered the alert |
| reason | TEXT | Reason for the alert |
| source_field | TEXT | Field that triggered the alert |

#### performance_metrics

Performance-related metrics for events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key to the events table |
| memory_usage | INTEGER | Memory usage in bytes |
| cpu_usage | REAL | CPU usage percentage |
| duration_ms | INTEGER | Duration in milliseconds |
| tokens_processed | INTEGER | Number of tokens processed |
| cost | REAL | Estimated cost |

#### security_alerts

High-level security alerts requiring attention.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key to the events table |
| alert_type | TEXT | Type of security alert |
| severity | TEXT | Severity level (low, medium, high, critical) |
| description | TEXT | Description of the alert |
| matched_terms | JSON | Terms that triggered the alert |
| action_taken | TEXT | Action taken in response to the alert |
| timestamp | TIMESTAMP | Timestamp of the alert |

## Design Rationale

### Normalized Structure
The schema is normalized to separate different types of information into dedicated tables, allowing more efficient storage and querying while reducing redundancy.

### Relationship Hierarchy
The schema establishes a clear hierarchy:
- Agents can have multiple sessions
- Sessions can have multiple conversations
- Conversations and sessions can have multiple events
- Events can have associated specialized data (LLM calls, tool calls, security alerts, etc.)

### Specialized Event Tables
Rather than storing all event data in JSON blobs, specialized tables are created for common event types (LLM calls, tool calls, security alerts, etc.) to allow for better querying and analysis.

### Performance Metrics
A dedicated table for performance metrics allows tracking resource usage over time for optimization and capacity planning.

### Security Analysis
The event_security and security_alerts tables provide structured storage for security-related information, enabling better analysis and alerting.

### Strategic Use of JSON Fields
JSON fields are retained for:
- Metadata fields: These contain varied, unstructured information that doesn't need frequent querying
- Specialized fields like tool inputs/outputs: These vary too much to normalize completely
- The data field in events: For any custom data not captured in specialized tables

### Indexing Strategy
The schema includes indexes on:
- Foreign keys for relationships
- Timestamp fields for time-range queries
- Event types, channels, and levels for filtering
- Text fields that will be frequently searched

## Use Cases Supported

### Agent Activity Overview
- Query agents table to see all registered agents
- Join with events to see activity levels over time
- Use session information to track active/inactive periods

### LLM Usage Analytics
- Query llm_calls table for comprehensive LLM usage statistics
- Calculate costs, average response times, token usage by model
- Track patterns in prompt/response pairs

### Security Monitoring
- Query security_alerts and event_security tables for suspicious/dangerous activities
- Filter alerts by severity for prioritization
- Track common security issues over time

### Performance Monitoring
- Use performance_metrics table to track resource usage
- Identify inefficient operations or memory leaks
- Set up alerts for performance thresholds

### Tool Usage Analysis
- Query tool_calls table to understand which tools are most used
- Track success rates and error patterns
- Identify slow or problematic tools

### Conversation Flow Analysis
- Use the conversations table to track complete conversation flows
- Analyze conversation lengths, patterns, and outcomes
- Link related events within a conversation

### System Health Monitoring
- Track error-level events across all agents
- Monitor system-wide performance metrics
- Identify patterns in failures or degradations

## Implementation Guidelines

### Schema Creation

When implementing this schema, it's recommended to:

1. Create tables in the order that respects foreign key relationships (agents → sessions → conversations → events → specialized tables)
2. Add appropriate indexes for query optimization
3. Implement proper foreign key constraints with cascading deletes where appropriate

Example SQL for creating the agents table:

```sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE NOT NULL,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

CREATE INDEX idx_agents_agent_id ON agents(agent_id);
```

### Event Logging

When logging events:

1. First check if an agent exists, creating one if necessary
2. Check if a session exists for this agent, creating one if necessary
3. Check if a conversation exists (if relevant), creating one if necessary
4. Create the base event record
5. Add specialized event data to the appropriate tables

Example pseudocode for logging an LLM call:

```python
def log_llm_call(agent_id, model, prompt, response, ...):
    # Get or create agent
    agent_db_id = get_or_create_agent(agent_id)
    
    # Get or create session (if session_id is provided)
    if session_id:
        session_db_id = get_or_create_session(agent_db_id, session_id)
    
    # Create base event
    event_data = {...}  # Any data not captured in specialized tables
    event_id = create_event(agent_db_id, session_db_id, "llm_call", "LLM", "info", event_data)
    
    # Create LLM call record
    create_llm_call(event_id, model, prompt, response, tokens_in, tokens_out, duration_ms, ...)
    
    # If applicable, create security check records
    if contains_suspicious_or_dangerous(prompt, response):
        create_event_security(event_id, alert_level, matched_terms, reason, ...)
```

### Query Optimization

For dashboard queries, consider:

1. Creating materialized views for common aggregations
2. Using appropriate indexes for filter conditions
3. Limiting TEXT field sizes where possible
4. Adding timestamp-based partitioning for large deployments

## Example Queries

### Get recent LLM calls for an agent

```sql
SELECT 
    e.timestamp, 
    l.model, 
    l.prompt, 
    l.response, 
    l.tokens_in, 
    l.tokens_out, 
    l.duration_ms, 
    l.cost
FROM events e
JOIN llm_calls l ON e.id = l.event_id
JOIN agents a ON e.agent_id = a.id
WHERE a.agent_id = 'my-agent-id'
ORDER BY e.timestamp DESC
LIMIT 100;
```

### Get security alerts by severity

```sql
SELECT 
    a.agent_id, 
    e.timestamp, 
    s.alert_type, 
    s.severity, 
    s.description, 
    s.matched_terms
FROM security_alerts s
JOIN events e ON s.event_id = e.id
JOIN agents a ON e.agent_id = a.id
WHERE s.severity IN ('high', 'critical')
ORDER BY e.timestamp DESC;
```

### Get tool usage statistics

```sql
SELECT 
    t.tool_name, 
    COUNT(*) as call_count, 
    AVG(t.duration_ms) as avg_duration,
    SUM(CASE WHEN t.success = 1 THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN t.success = 0 THEN 1 ELSE 0 END) as failure_count
FROM tool_calls t
JOIN events e ON t.event_id = e.id
JOIN agents a ON e.agent_id = a.id
WHERE a.agent_id = 'my-agent-id'
GROUP BY t.tool_name
ORDER BY call_count DESC;
```

## Conclusion

This database schema provides a comprehensive foundation for monitoring AI agent behavior, security issues, performance metrics, and more, while maintaining the flexibility to capture varied data from different frameworks and agent types. The schema is designed to support a wide range of analytics, alerting, and visualization use cases for security and development teams.

By following this design, you can implement a robust monitoring system that provides deep insights into agent operations while ensuring efficient data storage and retrieval. 