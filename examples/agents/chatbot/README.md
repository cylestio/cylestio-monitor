# Monitored LangChain Chatbot

This example demonstrates how to build a conversational chatbot using LangChain with Cylestio monitoring integration. The chatbot uses Anthropic's Claude model and maintains conversation history.

## Features

- Uses Anthropic's Claude model for high-quality responses
- Maintains conversation history with ConversationBufferMemory
- Monitors all LLM calls and chain executions using Cylestio Monitor's `enable_monitoring` function
- Logs detailed information about chatbot operations including:
  - Framework components used (LLM, memory, chain, prompt)
  - Performance metrics (processing time, token usage)
  - Model configuration details
  - Memory state
  - Error handling
- Includes example conversation to demonstrate functionality

## Requirements

- Python 3.12+
- Anthropic API key
- Cylestio Monitor package
- LangChain and related packages

## Setup

### Option 1: Install from PyPI (for users)

1. Install dependencies:
```bash
pip install langchain langchain-anthropic anthropic cylestio-monitor
```

### Option 2: Install from Local Source (for developers)

1. From the root of the Cylestio Monitor repository:
```bash
pip install -e .
```

2. Or from this example directory:
```bash
pip install -e ../../../
```

### Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Create Output Directory

Output directory will be created automatically when running the chatbot, or you can create it manually:
```bash
mkdir -p output
```

## Usage

Run the chatbot:
```bash
python chatbot.py
```

The script includes an example conversation that demonstrates the chatbot's capabilities and monitoring features.

## Monitoring Integration

The chatbot is integrated with Cylestio Monitor using the `enable_monitoring` function, which automatically patches LangChain components to track:
- LLM calls
- Chain executions
- Memory operations
- Error states

Additionally, the chatbot implements custom monitoring to track:
- Processing time for each interaction
- Token usage estimation
- Memory state changes
- Component usage details

This comprehensive monitoring approach provides detailed insights into the chatbot's operations and performance.

## Monitoring Data Format

Monitoring data is stored in `output/chatbot_monitoring.json` using the following format:

### Normal Interaction
```json
{
  "timestamp": "2025-03-12T14:30:45.123456",
  "event_type": "chat_exchange",
  "framework": "langchain",
  "model": {
    "provider": "anthropic",
    "name": "claude-3-haiku-20240307",
    "temperature": 0.7
  },
  "input": {
    "message": "User message here",
    "estimated_tokens": 5
  },
  "output": {
    "message": "Assistant response here",
    "estimated_tokens": 25
  },
  "memory": {
    "type": "conversation_buffer",
    "message_count": 4
  },
  "performance": {
    "processing_time_seconds": 1.25,
    "tokens_per_second": 24.0
  },
  "components": {
    "llm": "ChatAnthropic",
    "memory": "ConversationBufferMemory",
    "chain": "ConversationChain",
    "prompt_template": "ChatPromptTemplate"
  },
  "agent_id": "chatbot-agent"
}
```

### Error Event
```json
{
  "timestamp": "2025-03-12T14:35:12.654321",
  "event_type": "error",
  "framework": "langchain",
  "error": {
    "type": "ValueError",
    "message": "Error description here",
    "time_to_error_seconds": 0.35
  },
  "input": {
    "message": "User message that caused error"
  },
  "agent_id": "chatbot-agent"
}
```

## Example Output

```
Human: Hi! Can you help me learn about artificial intelligence?
Assistant: Certainly! I'd be happy to help you learn more about artificial intelligence (AI). AI is a broad and fascinating field that encompasses the development of computer systems and software capable of performing tasks that would typically require human intelligence... 