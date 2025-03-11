# Framework Support

Cylestio Monitor provides comprehensive monitoring across multiple AI frameworks and LLM providers. This flexibility allows you to monitor your AI systems regardless of the specific technologies you're using.

## Supported LLM Providers

### OpenAI

```python
from openai import OpenAI
from cylestio_monitor import enable_monitoring

client = OpenAI()
enable_monitoring(agent_id="openai-project", llm_client=client)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, world!"}]
)
```

### Anthropic

```python
from anthropic import Anthropic
from cylestio_monitor import enable_monitoring

client = Anthropic()
enable_monitoring(agent_id="anthropic-project", llm_client=client)

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

### Mistral AI

```python
from mistralai.client import MistralClient
from cylestio_monitor import enable_monitoring

client = MistralClient(api_key="your_api_key")
enable_monitoring(agent_id="mistral-project", llm_client=client)

response = client.chat(
    model="mistral-medium",
    messages=[{"role": "user", "content": "Hello, Mistral!"}]
)
```

## Supported Frameworks

### Model Context Protocol (MCP)

Cylestio Monitor provides integration with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), an open standard for AI agents to interact with tools and capabilities.

```python
from mcp import ClientSession
from cylestio_monitor import enable_monitoring

enable_monitoring(agent_id="mcp-project")
session = ClientSession(stdio, write)
result = await session.call_tool("weather", {"location": "New York"})
```

For detailed information, see [MCP Integration](mcp.md).

### LangChain

```python
from langchain.chat_models import ChatOpenAI
from cylestio_monitor import enable_monitoring

llm = ChatOpenAI()
enable_monitoring(agent_id="langchain-project", llm_client=llm)

result = llm.predict("Hello, LangChain!")
```

### Custom Frameworks

For custom frameworks or in-house AI systems, you can use our event logging system directly:

```python
from cylestio_monitor import enable_monitoring
from cylestio_monitor.events_processor import log_event

# Enable monitoring without a specific client
enable_monitoring(agent_id="custom-project")

# Log custom events
log_event(
    event_type="custom_llm_call",
    data={
        "prompt": "Hello, custom model!",
        "parameters": {"temperature": 0.7, "model": "custom-model"}
    },
    channel="CUSTOM_LLM"
)

# Log response events
log_event(
    event_type="custom_llm_response",
    data={
        "response": "Hello, human!",
        "duration_ms": 350,
        "token_count": 5
    },
    channel="CUSTOM_LLM"
)
```

## Upcoming Framework Support

We're constantly expanding our framework support. The following integrations are currently in development:

- **AI Agents**: Support for autonomous agent frameworks
- **LlamaIndex**: Integration with LlamaIndex for RAG applications
- **HuggingFace**: Direct integration with Transformers and other HF libraries

If you need support for a specific framework not listed here, please [contact us](https://cylestio.com/contact) or submit a feature request on our [GitHub repository](https://github.com/cylestio/cylestio-monitor/issues). 