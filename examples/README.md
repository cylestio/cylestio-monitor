# Cylestio Monitor Examples

This directory contains example implementations of AI agents that use Cylestio Monitor for tracking and security. Each example demonstrates how to integrate Cylestio Monitor with different agent architectures and frameworks.

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