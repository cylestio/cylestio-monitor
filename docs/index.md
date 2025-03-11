# Cylestio Monitor

<div class="grid-container">
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Security Monitoring</h3>
      <p>Detect and block dangerous prompts, flag suspicious activity</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Performance Tracking</h3>
      <p>Monitor call durations and response times</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <rect x="2" y="3" width="20" height="18" rx="2" ry="2" />
        <line x1="7" y1="7" x2="7" y2="7" />
        <line x1="7" y1="11" x2="7" y2="11" />
        <line x1="7" y1="15" x2="7" y2="15" />
        <line x1="11" y1="7" x2="17" y2="7" />
        <line x1="11" y1="11" x2="17" y2="11" />
        <line x1="11" y1="15" x2="17" y2="15" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Structured Logging</h3>
      <p>Store events in SQLite with flexible output options</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    </div>
    <div class="feature-content">
      <h3>Zero Configuration</h3>
      <p>Drop-in monitoring for AI agents across multiple frameworks</p>
    </div>
  </div>
</div>

## For AI Agent Developers

### Why Cylestio Monitor?

Cylestio Monitor provides comprehensive security and monitoring for AI agents throughout their lifecycle, from development to production. Our solution intercepts and analyzes AI interactions, logging critical parameters and detecting security threats. Cylestio Monitor helps you:

- **Secure your AI systems** by detecting and blocking dangerous prompts
- **Track performance metrics** with detailed call duration and response time data
- **Meet compliance requirements** with structured, audit-ready logging
- **Debug interactions** with comprehensive event data

All with minimal configuration and zero code changes to your existing agents.

### Key Features

- **Zero-configuration setup**: Import and enable with just two lines of code
- **Multi-framework support**: Works with popular LLM clients and frameworks including Model Context Protocol (MCP)
- **Security monitoring**: Detects and blocks dangerous prompts
- **Performance tracking**: Monitors call durations and response times
- **Structured logging**: Events stored in SQLite with optional JSON output
- **Dashboard integration**: View your monitoring data with our open source dashboard

## Security and Compliance

Cylestio Monitor is built with security and compliance in mind. We implement rigorous security practices and testing protocols to help you meet regulatory requirements including:

- **SOC2**: Our development and release processes follow SOC2 security principles
- **HIPAA**: Built-in safeguards help protect sensitive healthcare information
- **GDPR**: Configurable data handling options to support privacy requirements
- **Security Scanning**: Every release undergoes comprehensive security scanning

Each version of Cylestio Monitor includes detailed security reports documenting our testing protocols and scan results. These reports are available in our [Security Documentation](security/compliance-reports.md).

### Quick Installation

```bash
pip install cylestio-monitor
```

### Basic Usage

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_agent",
    llm_client=client
)

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

### Visualization Dashboard

For an interactive visualization of your monitoring data, check out our separate [Cylestio Dashboard](https://github.com/cylestio/cylestio-dashboard) repository. This open source dashboard provides real-time metrics, alert views, and detailed event analysis.

## For Contributors

We welcome contributions to the Cylestio Monitor project! Whether you're fixing bugs, improving documentation, or adding new features, your help is appreciated.

### How You Can Help

- **Bug Fixes**: Help identify and fix bugs in the codebase
- **Documentation**: Improve our docs, tutorials, and examples
- **Feature Development**: Add new features and integrations
- **Testing**: Create and enhance test coverage
- **Security**: Identify and address security concerns

See our [Contribution Guidelines](development/contributing.md) for details on how to get started.

## Getting Started

Ready to start monitoring your AI agents? Check out the [Installation Guide](getting-started/installation.md) and [Quick Start Guide](getting-started/quick-start.md) to get up and running in minutes.

For the official Cylestio Monitor documentation, visit [docs.cylestio.com](https://docs.cylestio.com/). 