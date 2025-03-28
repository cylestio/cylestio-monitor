# Cylestio Monitor Examples

This directory contains examples of integrating Cylestio Monitor into different AI agent architectures.

## Simple Usage Pattern

All examples follow the same basic pattern:

```python
# 1. Import the SDK
import cylestio_monitor

# 2. Start monitoring at the beginning of your application
cylestio_monitor.start_monitoring(
    agent_id="your-agent-id",
    config={"log_file": "path/to/output.json"}  # Optional
)

# 3. Use your AI frameworks as normal
# The SDK automatically detects and patches supported libraries

# 4. Stop monitoring when your application is finished
cylestio_monitor.stop_monitoring()
```

## Available Examples

### Complete Agent Examples

The [agents](./agents) directory contains fully implemented AI agents:

- **[Weather Agent](./agents/weather_agent)**: Uses MCP and Anthropic Claude
- **[RAG Agent](./agents/rag_agent)**: Demonstrates retrieval-augmented generation
- **[Chatbot](./agents/chatbot)**: Simple LLM-based chatbot

### Individual Examples

- **[anthropic_enhanced_monitoring.py](./anthropic_enhanced_monitoring.py)**: Shows advanced monitoring features with Anthropic Claude

## Running Examples

Each example includes its own `requirements.txt` file for dependencies:

```bash
# Navigate to an example directory
cd examples/agents/weather_agent

# Install dependencies
pip install -r requirements.txt

# Run the example
python weather_client.py
```

## Key Integration Patterns

### 1. Anthropic Integration

```python
import cylestio_monitor
from anthropic import Anthropic

# Start monitoring
cylestio_monitor.start_monitoring(agent_id="anthropic-example")

# Create client - will be automatically patched
client = Anthropic()

# Use as normal - all monitoring is automatic
response = client.messages.create(...)
```

### 2. MCP Integration

```python
import cylestio_monitor
from mcp import ClientSession

# Start monitoring
cylestio_monitor.start_monitoring(agent_id="mcp-example")

# Create MCP session - will be automatically patched
session = ClientSession(...)

# All tool calls are automatically monitored
```

### 3. LangChain Integration

```python
import cylestio_monitor
from langchain.chat_models import ChatAnthropic

# Start monitoring
cylestio_monitor.start_monitoring(agent_id="langchain-example")

# Create LangChain components - will be automatically patched
llm = ChatAnthropic(...)

# All chains and agents are automatically monitored
```
