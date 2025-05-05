#!/usr/bin/env python3
"""
Weather AI Agent Client

This client demonstrates how to use the Cylestio Monitor SDK
to monitor both MCP and LLM API calls in a simple weather agent.
"""

import asyncio
import logging
import os
from contextlib import AsyncExitStack
from typing import Optional
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import our monitoring SDK
import cylestio_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Weather AI Agent")

# Load environment variables from .env file
load_dotenv()

# Create output directory if it doesn't exist
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Configure Cylestio monitoring with simplified configuration
cylestio_monitor.start_monitoring(
    agent_id="weather-agent",
    config={
        # Event data output file
        "events_output_file": "output/weather_monitoring.json",
        
        # Debug configuration
        "debug_mode": True,
        "debug_log_file": "output/cylestio_debug.log",
        
        # Custom telemetry endpoint (optional, defaults to http://127.0.0.1:8000)
        "telemetry_endpoint": "http://127.0.0.1:9000", 
    }
)

# Note: As of v0.1.9, the SDK automatically handles MCP patching
# with proper versioning and robust error handling

class WeatherAIAgent:
    """Weather AI Agent that uses MCP and LLM with monitoring."""

    def __init__(self):
        """Initialize the Weather AI Agent."""
        logger.info("Initializing Weather AI Agent")
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        # Create Anthropic client - it will be automatically patched by the SDK
        self.anthropic = Anthropic()
        logger.info("Created Anthropic client instance")

    async def connect_to_server(self, server_script_path: str):
        """Connect to the Weather MCP server."""
        logger.info(f"Connecting to Weather MCP server: {server_script_path}")

        # Set up server parameters
        command = "python" if server_script_path.endswith(".py") else "node" 
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the session
        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
        print(f"\nConnected to Weather MCP server with tools: {[tool.name for tool in tools]}")

    async def process_query(self, query: str) -> str:
        """Process a user query using Claude and available weather tools."""
        logger.info("Processing user query")

        # Get available tools 
        response = await self.session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        try:
            # Simple, straightforward call to Claude with tools
            # The SDK will automatically monitor this call
            messages = [{"role": "user", "content": query}]
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
            )
            
            # If Claude wants to use a tool, let it do so and continue the conversation
            if hasattr(response, "content") and any(
                getattr(content, "type", None) == "tool_use" for content in response.content
            ):
                for content in response.content:
                    if getattr(content, "type", None) == "tool_use":
                        # Execute the tool call - the SDK will monitor this automatically
                        tool_name = content.name
                        tool_args = content.input
                        logger.info(f"Claude is calling tool: {tool_name}")
                        
                        # Call the tool - the SDK's MCP patching handles monitoring
                        result = await self.session.call_tool(tool_name, tool_args)
                        
                        # Continue conversation with tool results
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user", 
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": result.content,
                            }]
                        })
                        
                        # Get the final response with tool results
                        response = self.anthropic.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1000,
                            messages=messages,
                        )
                        break
                
            # Return the response text - just the first text content for simplicity
            for content in response.content:
                if getattr(content, "type", None) == "text":
                    return content.text
                    
            # Fallback case
            return "No response text found"
                
        except Exception as e:
            logger.error(f"Error: {type(e).__name__}: {str(e)}")
            raise

    async def chat_loop(self):
        """Run an interactive chat loop for weather queries."""
        print("\nWeather AI Agent Started!")
        print("Ask about weather alerts or forecasts. Type 'quit' to exit.")
        print("Example queries:")
        print("  - What are the current weather alerts in CA?")
        print("  - What's the forecast for New York City?")
        print("  - Should I bring an umbrella in Seattle today?")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() in ("quit", "exit"):
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources and disable monitoring."""
        logger.info("Cleaning up resources")
        await self.exit_stack.aclose()
        cylestio_monitor.stop_monitoring()
        logger.info("Monitoring stopped")


async def main():
    """Main function to run the Weather AI Agent."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script_path = os.path.join(script_dir, "weather_server.py")

    agent = WeatherAIAgent()
    try:
        await agent.connect_to_server(server_script_path)
        await agent.chat_loop()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    print("Starting Weather AI Agent")
    asyncio.run(main())
