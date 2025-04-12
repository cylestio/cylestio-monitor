# Cylestio Monitor SDK

Cylestio Monitor is a comprehensive security and monitoring solution for AI agents with OpenTelemetry-compliant telemetry. It provides lightweight, drop-in security monitoring for LLM clients and frameworks with just two lines of code.

## Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **OpenTelemetry compliance**: Generate structured telemetry with trace context
- **Multi-framework support**: Works with popular LLM clients and frameworks
- **Security monitoring**: Detects and flags suspicious or dangerous content
- **Performance tracking**: Monitors call durations and response times
- **Hierarchical operation tracking**: Track relationships between operations
- **Flexible logging**: Send events to API endpoints or store locally

## Simple Integration

```python
# Start monitoring at application initialization
import cylestio_monitor
cylestio_monitor.start_monitoring(agent_id="my-agent")

# Your application code here...
# The SDK automatically detects and monitors supported libraries

# Stop monitoring when done
cylestio_monitor.stop_monitoring()
```

## Automatic Framework Detection

Cylestio Monitor automatically detects and instruments supported libraries:

- **Anthropic Claude SDK** - all versions
- **MCP (Model Context Protocol)**
- **LangChain**
- **LangGraph**

No additional configuration is required to monitor these frameworks.

## Configuration Options

The `start_monitoring` function accepts these optional configuration options:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "debug_level": "INFO",           # Logging level
        "log_file": "output/logs.json",  # Path for local JSON logs
        "api_endpoint": "https://api.example.com/events",  # Remote endpoint
        "development_mode": False        # Extra development features
    }
)
```

## Event Structure

All events follow OpenTelemetry standards with proper trace context:

```json
{
    "timestamp": "2024-03-27T15:31:40.622Z",
    "trace_id": "2a8ec755032d4e2ab0db888ab84ef595",
    "span_id": "96d8c2be667e4c78",
    "parent_span_id": "f1490a668d69d1dc",
    "name": "llm.call.start",
    "attributes": {
        "method": "messages.create",
        "model": "claude-3-haiku-20240307"
    },
    "agent_id": "weather-agent"
}
```

> **Note**: All timestamps use ISO8601 format with UTC timezone and Z suffix. See the [Timestamp Guidelines](developers/timestamps.md) for details.

## Security

Cylestio Monitor includes several security features:

- **Content safety monitoring**: Identify potentially suspicious or dangerous content
- **PII detection**: Detect and redact personally identifiable information
- **Content filtering**: Flag harmful or inappropriate content  
- **Security classification**: Events are automatically classified by security risk level
- **Regulatory compliance**: Designed to help satisfy SOC2, GDPR, and HIPAA monitoring requirements
- **Audit-ready logging**: Generate detailed logs suitable for security audits and compliance verification

## Compliance for Agentic Workforces

Cylestio Monitor enables organizations to maintain regulatory compliance as they transition to agentic workforces:

- **Monitors LLM interactions**: Tracks all agent activities with LLM providers
- **Real-time detection**: Identifies PII, credentials, and regulated information
- **Security vulnerability detection**: Alerts on prompt injections and other attack vectors
- **Comprehensive audit trails**: Maintains detailed logs of all agent operations
- **Built-in data protection**: Automatically masks sensitive data in logs and telemetry

The monitoring system itself is built with compliance in mind—all sensitive data detected in events is properly masked in logs and telemetry. The security detection patterns and rules are fully configurable to match specific regulatory and organizational requirements.

For details about security configuration options, see [Security Configuration](sdk-reference/security-configuration.md).

## Examples

The SDK includes several example agents in the [examples/agents](../examples/agents) directory:

- **Weather Agent**: Demonstrates MCP and Anthropic Claude integration
- **RAG Agent**: Shows retrieval-augmented generation monitoring
- **Chatbot**: Simple LLM-based chatbot with monitoring

## Documentation Sections

- [Getting Started](getting-started/quick-start.md): Setup and configuration
- [SDK Reference](sdk-reference/overview.md): API documentation
  - [Monitor Module](sdk-reference/monitor.md): Core monitoring functionality
  - [Events System](sdk-reference/events.md): Event processing
  - [API Client](sdk-reference/api-client.md): API endpoints and logging
  - [Trace Context](sdk-reference/tracing.md): Distributed tracing
- [Custom Integrations](custom-integrations.md): Extending the SDK
- [Troubleshooting](troubleshooting.md): Common issues and solutions
