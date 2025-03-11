# User Guide Overview

## Why Monitor Your AI Agents?

Modern AI agents are powerful tools, but they also come with inherent risks:

- **Security vulnerabilities** through prompt injection or data exfiltration
- **Performance inconsistencies** that impact user experience
- **Compliance gaps** that could result in regulatory issues
- **Debugging challenges** with complex AI interactions

Cylestio Monitor gives you full visibility into your AI agents' operations, providing real-time security monitoring, performance tracking, and comprehensive logging in a single package.

## Core Capabilities

### 1. Security Monitoring

Cylestio Monitor actively scans all incoming and outgoing messages for security threats:

- **Prompt injection detection** identifies attempts to manipulate your AI
- **Dangerous content blocking** prevents harmful instructions from being processed
- **Suspicious activity flagging** marks potential threats for review
- **PII/PHI detection** identifies sensitive data in prompts and responses

### 2. Performance Tracking

Monitor the operational health of your AI systems:

- **Response timing** for every LLM and tool call
- **Token usage** tracking to manage costs
- **Error rate** monitoring to detect issues
- **Latency trends** to identify performance degradation

### 3. Comprehensive Logging

Keep detailed records of all AI interactions:

- **Structured event logs** with standardized formats
- **Request/response archiving** for auditing and analysis
- **Security alert records** with threat classification
- **Centralized storage** in a queryable SQLite database

## Key Benefits

- **Risk reduction** through proactive security monitoring
- **Cost optimization** with performance and usage insights
- **Debugging support** with detailed interaction history
- **Compliance readiness** for audit and regulatory requirements
- **Easy integration** with minimal code changes

## Integration Patterns

Cylestio Monitor can be integrated in multiple ways:

1. **Direct client integration** - Patch LLM clients automatically
2. **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) monitoring** - Monitor Model Context Protocol operations
3. **Custom integrations** - Use our API to monitor any system

## Next Steps

Continue reading to explore detailed guides on:

- [Monitoring LLM](monitoring-llm.md) interactions
- [Monitoring MCP](monitoring-mcp.md) operations
- [Security Features](security-features.md) and configuration
- [Logging Options](logging-options.md) for different environments 