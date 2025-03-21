# Framework Compatibility

This document outlines the frameworks and versions that are compatible with Cylestio Monitor.

## Supported Frameworks and Versions

Cylestio Monitor is designed to work with the following frameworks and versions:

### LLM Provider SDKs

| Framework | Supported Versions | Notes |
|-----------|-------------------|-------|
| Anthropic | ≥ 0.18.0 | Full support for Claude 3 models (Opus, Sonnet, Haiku) with complete request and response tracking |
| OpenAI | Coming soon | Support for OpenAI's SDK is planned for a future release |

### Agent Frameworks

| Framework | Supported Versions | Notes |
|-----------|-------------------|-------|
| MCP (Model Context Protocol) | ≥ 1.3.0 | Full support for tool calls and responses with bidirectional tracking |
| LangChain | ≥ 0.1.0 | Complete request-response tracking for the latest LangChain architecture |
| LangChain Core | ≥ 0.1.33 | Core components of LangChain supported with enhanced response tracking |
| LangChain Community | ≥ 0.0.16 | Community components supported with response tracking |
| LangChain Anthropic | ≥ 0.1.5 | Anthropic integration with LangChain fully supported with bidirectional monitoring |
| LangGraph | ≥ 0.0.19 | Full support for graph-based agent workflows including response tracking |

## Event Tracking Capabilities

Cylestio Monitor captures the following event types for each framework:

| Framework | Request Events | Response Events | Error Events | Performance Metrics |
|-----------|---------------|----------------|--------------|-------------------|
| Anthropic | ✅ | ✅ | ✅ | ✅ |
| LangChain | ✅ | ✅ | ✅ | ✅ |
| LangGraph | ✅ | ✅ | ✅ | ✅ |
| MCP | ✅ | ✅ | ✅ | ✅ |

## Dependencies

Cylestio Monitor also depends on the following libraries:

| Library | Required Version | Purpose |
|---------|-----------------|---------|
| pydantic | ≥ 2.0.0 | Data validation and settings management |
| python-dotenv | ≥ 1.0.0 | Environment variable management |
| structlog | ≥ 24.1.0 | Structured logging |
| platformdirs | ≥ 4.0.0 | Platform-specific directory handling |
| pyyaml | ≥ 6.0.0 | YAML configuration parsing |
| requests | ≥ 2.31.0 | HTTP requests for API client |

## Compatibility Testing

Each release of Cylestio Monitor is tested against the minimum supported versions of each framework to ensure backward compatibility, as well as with the latest versions to ensure forward compatibility.

If you encounter compatibility issues with any of the supported frameworks, please report them in our [GitHub issue tracker](https://github.com/cylestio/cylestio-monitor/issues).

## Upcoming Support

We are actively working on expanding support for additional frameworks and providers:

- OpenAI SDK
- Azure OpenAI
- LiteLLM
- More LangChain integrations
- Custom framework adapters

Stay updated with our [changelog](https://github.com/cylestio/cylestio-monitor/blob/main/CHANGELOG.md) for the latest compatibility information. 