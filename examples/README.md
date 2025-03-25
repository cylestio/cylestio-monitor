# Cylestio Monitor Examples

This directory contains examples demonstrating how to use Cylestio Monitor with various LLM frameworks and direct API calls.

## Multi-Framework Monitoring Example

The [`multi_framework_monitoring.py`](./multi_framework_monitoring.py) script demonstrates how Cylestio Monitor can track LLM interactions across different frameworks:

1. **Direct API Calls**: Monitoring Anthropic Claude API calls directly
2. **LangChain**: Monitoring LangChain chains with Anthropic backend  
3. **LangGraph**: Monitoring LangGraph agents with Anthropic backend

### Prerequisites

To run the examples, you'll need:

- Python 3.12+
- An Anthropic API key
- The Cylestio Monitor package installed

```bash
# Install required packages
pip install cylestio-monitor anthropic
# Optional frameworks
pip install langchain langchain-anthropic
pip install langgraph
```

### Running the Example

You can provide your Anthropic API key in two ways:

1. Set the `ANTHROPIC_API_KEY` environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your-api-key-here
   python examples/multi_framework_monitoring.py
   ```

2. Create an `api_key.txt` file in the root directory with just your API key.

### What the Example Demonstrates

The example shows how Cylestio Monitor:

- Intercepts and logs LLM calls across different frameworks
- Extracts prompts and responses consistently
- Detects potential security issues
- Formats data uniformly regardless of the source
- Saves events to both a SQLite database and JSON files

### Output

After running the example, check the `examples/output/` directory for the following log files:

- `anthropic_logs.json`: Logs from direct Anthropic API calls
- `langchain_logs.json`: Logs from LangChain interactions
- `langgraph_logs.json`: Logs from LangGraph agents

You can also query the SQLite database using the Cylestio Monitor CLI:

```bash
cylestio-monitor query --last 10
```

## Understanding the Logs

The logs contain standardized events with the following structure:

```json
{
  "timestamp": "2023-01-01T12:34:56.789012",
  "level": "INFO",
  "agent_id": "example-agent",
  "event_type": "LLM_call_finish",
  "channel": "LLM",
  "data": {
    "duration": 1.23,
    "response": "The AI's response text...",
    "alert": "none",
    "framework": {
      "name": "langchain",
      "version": "0.3.0"
    }
  }
}
```

Key fields to observe:

- **event_type**: Indicates what happened (e.g., `LLM_call_start`, `LLM_call_finish`)
- **channel**: Shows which framework/system generated the event
- **data**: Contains the actual prompt/response and metadata
- **alert**: Indicates if any security concerns were detected

## Customizing Monitoring

You can customize Cylestio Monitor for your specific needs:

### Adding Custom Security Checks

Edit your configuration to add custom keywords to check:

```python
from cylestio_monitor.config import ConfigManager

config = ConfigManager()
config.set("monitoring.suspicious_words", ["keyword1", "keyword2"])
config.set("monitoring.dangerous_words", ["dangerous1", "dangerous2"])
config.save()
```

### Logging Custom Events

Use the `log_to_file_and_db` function to log your own events:

```python
from cylestio_monitor import log_to_file_and_db

log_to_file_and_db(
    event_type="my_custom_event",
    data={
        "key1": "value1",
        "key2": "value2"
    },
    channel="MY_SYSTEM",
    level="info"
)
```

## Additional Resources

- [Cylestio Monitor Documentation](../docs/): Full documentation
- [Advanced Integrations Guide](../docs/advanced-topics/custom-integrations.md): How to integrate with custom systems

## Available Examples

The examples are organized by agent type/functionality rather than by framework. Each agent may use one or more frameworks including Anthropic, MCP, LangChain, or LangGraph.

### Weather Agent

Located in: `examples/agents/weather_agent/`

A demonstration of an AI agent that:
- Uses Anthropic's Claude API for LLM functionality
- Implements Model Context Protocol (MCP) for tool use
- Provides weather forecasts and conditions
- Tracks all API activity with Cylestio Monitor

### RAG Agent

Located in: `examples/agents/rag_agent/`

A Retrieval-Augmented Generation (RAG) agent that:
- Uses LangChain to orchestrate a retrieval workflow
- Integrates LangGraph for complex agent workflows
- Demonstrates how to monitor LLM API calls across a complex pipeline
- Shows how to implement vectorstore integration with monitoring

### Chatbot

Located in: `examples/agents/chatbot/`

A conversational AI assistant that:
- Implements a simple LangChain-based conversational interface
- Uses Anthropic's Claude as the underlying LLM
- Demonstrates memory persistence with monitoring
- Shows basic conversation patterns with security tracking

## Running the Examples

Each example directory contains:
- A README.md with specific setup instructions
- Required code files for the agent
- A requirements.txt file listing dependencies

To run any example:

1. Navigate to the specific example directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment:
   - Windows: `venv\Scripts\activate`
   - MacOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Follow the specific instructions in the example's README.md

## Framework Support

The examples demonstrate integration with various LLM frameworks. Cylestio Monitor supports:

- Anthropic Python SDK
- Model Context Protocol (MCP)
- LangChain
- LangGraph

Each example demonstrates best practices for security monitoring and logging when building AI agents. 