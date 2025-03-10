# Weather AI Agent Example

This example demonstrates how to use the Cylestio Monitor SDK with a weather AI agent that uses the Model Context Protocol (MCP) and Anthropic's Claude API.

## Overview

The example consists of two main components:

1. **Weather MCP Server** (`weather_server.py`): Provides weather data through MCP tools
2. **Weather AI Agent Client** (`weather_client.py`): Connects to the server and uses Claude to process weather queries

The Cylestio Monitor SDK is used to monitor both the MCP tool calls and the LLM API calls, providing insights into the agent's operation.

## Prerequisites

- Python 3.11 or higher
- An Anthropic API key (set in your environment or `.env` file)
- Required Python packages (see below)

## Installation

1. Install the required packages:

```bash
pip install mcp anthropic httpx python-dotenv cylestio-monitor
```

2. Create a `.env` file in the examples directory with your Anthropic API key:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

Run the Weather AI Agent:

```bash
cd examples
python weather_client.py
```

The agent will:
1. Start the Weather MCP Server
2. Enable monitoring with the Cylestio Monitor SDK
3. Start an interactive chat loop where you can ask weather-related questions

Example queries:
- "What are the current weather alerts in CA?"
- "What's the forecast for New York City?"
- "Should I bring an umbrella in Seattle today?"

Type `quit` to exit the chat loop.

## Monitoring

The Cylestio Monitor SDK logs all MCP and LLM API calls to `weather_monitoring.json`. This includes:

- Tool calls to the Weather MCP Server
- API calls to Anthropic's Claude
- Execution times and responses
- Security alerts for suspicious or dangerous content

You can view the monitoring logs to gain insights into the agent's operation and performance.

## How It Works

1. The Weather MCP Server provides two tools:
   - `get_alerts`: Get weather alerts for a US state
   - `get_forecast`: Get weather forecast for a location

2. The Weather AI Agent Client:
   - Connects to the Weather MCP Server
   - Enables monitoring with the Cylestio Monitor SDK
   - Processes user queries using Claude
   - Calls the appropriate weather tools based on Claude's decisions
   - Returns the results to the user

3. The Cylestio Monitor SDK:
   - Intercepts and logs all MCP tool calls
   - Intercepts and logs all LLM API calls
   - Checks for suspicious or dangerous content
   - Provides timing and performance data

## Customization

You can modify this example to:
- Add more weather tools to the server
- Use a different LLM provider (requires modifying the client)
- Customize the monitoring configuration
- Add additional security checks

## Troubleshooting

If you encounter issues:
- Ensure your Anthropic API key is correctly set
- Check that all required packages are installed
- Verify that the National Weather Service API is accessible
- Check the logs for error messages 