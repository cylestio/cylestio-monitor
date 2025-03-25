# Weather Agent Example

This example demonstrates how to build a Weather AI Agent that uses both Anthropic Claude for natural language processing and Model Context Protocol (MCP) for tool integration, with Cylestio Monitor providing comprehensive tracking and security.

## Overview

The Weather Agent consists of:

1. **Weather Client** - A client application that connects to Claude and the MCP server
2. **Weather Server** - An MCP server that provides weather-related tools

The agent allows users to have natural conversations about weather conditions and forecasts, while all interactions are monitored by Cylestio Monitor for security and performance tracking.

## Features

- **Interactive Weather Queries**: Ask about weather in natural language
- **Tool Integration**: Weather data lookup tools via MCP
- **Security Monitoring**: All API calls are tracked and monitored
- **Conversation History**: Maintains context within conversations

## Requirements

- Python 3.12+
- Anthropic API key
- Cylestio Monitor

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

## Usage

1. Start the agent:
   ```bash
   python weather_client.py
   ```

2. Interact with the agent by asking weather-related questions:
   - "What's the weather like in New York?"
   - "Are there any weather alerts in California?"
   - "Should I bring an umbrella in Seattle today?"

3. Type `quit` to exit the agent.

## Monitoring

Cylestio Monitor is enabled in this example to track:
- All Claude API calls
- Tool usage patterns and timing
- Agent performance metrics

The monitoring data is stored in:
- An SQLite database at the default location
- JSON logs in the `output/` directory

## Code Structure

- `weather_client.py`: The main client application that connects to both Claude and the MCP server
- `weather_server.py`: The MCP server that implements weather-related tools
- `requirements.txt`: Dependencies for running the example
- `output/`: Directory where monitoring logs are saved

## Frameworks Used

- **Anthropic SDK**: For Claude API integration (v0.18.0+)
- **MCP**: For tool integration (v1.3.0+)
- **Cylestio Monitor**: For security and performance monitoring 