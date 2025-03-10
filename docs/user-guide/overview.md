# User Guide Overview

Cylestio Monitor provides three main capabilities:

1. **Security Monitoring**: Detect and block dangerous prompts, flag suspicious activity
2. **Performance Tracking**: Monitor call durations and response times
3. **Structured Logging**: Store events in SQLite with flexible output options

## How It Works

The SDK uses a patching mechanism to intercept calls to LLM APIs and MCP tools. When a call is made, the SDK:

1. Logs the call parameters and timestamp
2. Checks for suspicious or dangerous content
3. Allows or blocks the call based on security checks
4. Logs the response and performance metrics
5. Stores all events in a structured format

## Monitoring Channels

- **SYSTEM**: Events related to the SDK itself
- **LLM**: Events related to LLM API calls
- **API**: Events related to general API calls
- **MCP**: Events related to MCP tool calls

## Security Levels

- **None**: Normal events with no security concerns
- **Suspicious**: Events that contain potentially suspicious content
- **Dangerous**: Events that contain dangerous content that could lead to harmful actions

## Data Storage

All events are stored in a global SQLite database, ensuring that all instances of the SDK write to the same database regardless of the virtual environment in which they're installed.

## Next Steps

- [Monitoring LLM Calls](monitoring-llm.md): How to monitor LLM API calls
- [Monitoring MCP](monitoring-mcp.md): How to monitor MCP tool calls
- [Security Features](security-features.md): How to use the security features
- [Logging Options](logging-options.md): How to configure logging 