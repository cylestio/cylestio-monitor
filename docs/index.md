# Secure and Monitor Your AI Agents

<div class="hero">
  <h1>Comprehensive Security and Monitoring for AI Agents</h1>
  <p>Protect your AI systems, track performance, and ensure compliance with enterprise-grade monitoring.</p>
  <div class="cta-buttons">
    <a href="getting-started/quick-start/" class="md-button">Get Started</a>
    <a href="user-guide/overview/" class="md-button md-button--secondary">Learn More</a>
  </div>
</div>

<div class="grid-container">
  <div class="feature-card">
    <div class="feature-icon">
      <span class="twemoji">
        🛡️
      </span>
    </div>
    <div class="feature-content">
      <h3>Security First</h3>
      <p>Real-time threat detection and prevention for your AI systems</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <span class="twemoji">
        📈
      </span>
    </div>
    <div class="feature-content">
      <h3>Performance Insights</h3>
      <p>Track response times, costs, and system health metrics</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <span class="twemoji">
        🧩
      </span>
    </div>
    <div class="feature-content">
      <h3>Easy Integration</h3>
      <p>Drop-in monitoring for popular LLM frameworks and MCP</p>
    </div>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">
      <span class="twemoji">
        📊
      </span>
    </div>
    <div class="feature-content">
      <h3>Visual Analytics</h3>
      <p>Beautiful dashboards for monitoring and analysis</p>
    </div>
  </div>
</div>

## Start Monitoring in Minutes

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Enable monitoring with one line
enable_monitoring(agent_id="my_agent", llm_client=Anthropic())

# Use your client as normal - we'll handle the rest
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Why Choose Cylestio Monitor?

### Enterprise-Grade Security

- **Threat Detection**: Identify and block dangerous prompts in real-time
- **Compliance Ready**: Built-in support for SOC2, HIPAA, and GDPR requirements
- **Access Control**: Fine-grained permissions and audit logging

### Comprehensive Monitoring

- **Performance Metrics**: Track latency, token usage, and costs
- **Error Tracking**: Identify and debug issues quickly
- **Usage Analytics**: Understand how your agents are being used

### Seamless Integration

- **Framework Support**: Works with Anthropic, OpenAI, and other major providers
- **MCP Compatible**: Native support for Model Context Protocol
- **Zero Config**: Get started with minimal setup required

## Ready to Get Started?

1. [Quick Start Guide](getting-started/quick-start.md) - Get up and running in minutes
2. [Installation Guide](getting-started/installation.md) - Detailed setup instructions
3. [User Guide](user-guide/overview.md) - Learn about all features

## Resources

- [GitHub Repository](https://github.com/cylestio/cylestio-monitor)
- [Dashboard Demo](https://demo.cylestio.com)
- [API Reference](sdk-reference/overview.md)
- [Support](troubleshooting/faqs.md) 