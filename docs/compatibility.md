# Framework Compatibility

Cylestio Monitor v0.1.6 supports the following frameworks and libraries:

## LLM Provider SDKs

| Provider | Support | Notes |
|----------|---------|-------|
| Anthropic | ✅ | All Claude models (Opus, Sonnet, Haiku) with auto-detection |
| OpenAI | ✅ | Chat Completions and Completions APIs |

## Agent Frameworks

| Framework | Support | Notes |
|-----------|---------|-------|
| MCP (Model Context Protocol) | ✅ | Tool calls and responses |
| LangChain | ✅ | Chains, agents, callbacks, tools (v0.1.0+) |
| LangChain Core | ✅ | Core components and runnables |
| LangChain Community | ✅ | Community components and tools |
| LangGraph | ✅ | Graph-based agent workflows |

## Monitoring Features

All monitored frameworks capture:
- Request events
- Response events
- Error events
- Performance metrics
- Token usage (where available)
- Tool execution details
- Chain execution details

## Dependencies

Core dependencies:
- pydantic ≥ 2.0.0
- python-dotenv ≥ 1.0.0
- structlog ≥ 24.1.0
- platformdirs ≥ 4.0.0
- pyyaml ≥ 6.0.0
- requests ≥ 2.31.0
- langchain ≥ 0.1.0
- langchain-core ≥ 0.1.0
- langchain-community ≥ 0.0.10