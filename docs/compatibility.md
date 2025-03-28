# Framework Compatibility

Cylestio Monitor v0.1.5 supports the following frameworks and libraries:

## LLM Provider SDKs

| Provider | Support | Notes |
|----------|---------|-------|
| Anthropic | ✅ | All Claude models (Opus, Sonnet, Haiku) with auto-detection |
| OpenAI | Planned | Coming in a future release |

## Agent Frameworks

| Framework | Support | Notes |
|-----------|---------|-------|
| MCP (Model Context Protocol) | ✅ | Tool calls and responses |
| LangChain | ✅ | Chains, agents, callbacks |
| LangGraph | ✅ | Graph-based agent workflows |

## Monitoring Features

All monitored frameworks capture:
- Request events
- Response events
- Error events
- Performance metrics

## Dependencies

Core dependencies:
- pydantic ≥ 2.0.0
- python-dotenv ≥ 1.0.0
- structlog ≥ 24.1.0
- platformdirs ≥ 4.0.0
- pyyaml ≥ 6.0.0
- requests ≥ 2.31.0

## Coming Soon

- OpenAI SDK support
- Azure OpenAI support
- LiteLLM support
