# Monitoring LLM Calls

Cylestio Monitor provides comprehensive visibility into Large Language Model API interactions, helping you secure your AI systems, track performance, and maintain compliance.

## Supported LLM Providers

Cylestio Monitor automatically detects and monitors calls to these popular LLM clients:

- **Anthropic** (Claude models)
- **OpenAI** (GPT models)
- **Azure OpenAI** (Hosted GPT models)
- **Google Gemini** (Gemini models)
- **Cohere** (Cohere models)
- **Mistral AI** (Mistral models)

## Basic Setup

Monitoring LLM calls requires just a few lines of code. Pass your LLM client to the `enable_monitoring` function:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_customer_service_agent",
    llm_client=client
)

# Use your client as normal - monitoring happens automatically
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

## What Gets Monitored

For each LLM call, Cylestio Monitor captures:

- **Request details**: Prompt text, model, parameters
- **Response content**: The full LLM response
- **Performance metrics**: Latency, tokens used, request duration
- **Security alerts**: Any suspicious or dangerous content
- **Metadata**: Timestamps, agent ID, request ID

## Event Types

The monitor tracks multiple event types for comprehensive visibility:

1. **LLM_call_start**: When an LLM request begins
2. **LLM_call_end**: When an LLM response is received
3. **LLM_call_error**: When an LLM request fails
4. **security_alert**: When security issues are detected

## Advanced Configuration

### Monitoring Specific Methods

By default, the monitor patches the standard message creation method. For custom integration:

```python
# Monitor a different method path
enable_monitoring(
    agent_id="custom_integration",
    llm_client=client,
    llm_method_path="custom.method.path"
)
```

### Multiple Client Monitoring

Monitor multiple LLM clients simultaneously:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic
from openai import OpenAI

# Create clients
anthropic_client = Anthropic()
openai_client = OpenAI()

# Enable monitoring for both
enable_monitoring(
    agent_id="multi_llm_agent",
    llm_client=anthropic_client
)
enable_monitoring(
    agent_id="multi_llm_agent",
    llm_client=openai_client
)
```

## Security Features

For LLM calls, security monitoring provides:

- **Prompt injection detection**: Prevent attempts to override instructions
- **Content filtering**: Block requests with dangerous keywords
- **Alert flagging**: Mark suspicious content for review
- **PII/PHI protection**: Mask sensitive data in logs

## Performance Tracking

Measure and optimize your LLM usage:

- **Response times**: Track how long calls take
- **Token counts**: Monitor usage against quotas
- **Error rates**: Identify problematic prompts
- **Cost analytics**: Calculate spending by model

## Visualization and Analysis

Use the [Cylestio Dashboard](https://github.com/cylestio/cylestio-dashboard) to visualize your LLM interactions:

- Real-time monitoring dashboard
- Historical trend analysis
- Security alert views
- Performance metrics

## Best Practices

For effective LLM monitoring:

1. Use descriptive agent IDs for easy identification
2. Configure security keywords for your specific use case
3. Review logs regularly to identify issues
4. Set up alerting for critical security events
5. Use the dashboard for trend analysis 