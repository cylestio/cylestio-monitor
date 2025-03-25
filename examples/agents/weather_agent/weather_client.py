#!/usr/bin/env python3
"""
Weather AI Agent Client

This client connects to the Weather MCP Server and uses the Cylestio Monitor SDK
to monitor both MCP and LLM API calls. It provides an interactive chat interface
for querying weather information.
"""

import asyncio
import logging
import os
from contextlib import AsyncExitStack
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import our monitoring SDK
from cylestio_monitor import stop_monitoring, start_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Weather AI Agent")

# Load environment variables from .env file
load_dotenv()


class WeatherAIAgent:
    """Weather AI Agent that uses MCP and LLM with monitoring."""

    def __init__(self):
        """Initialize the Weather AI Agent."""
        logger.info("Initializing Weather AI Agent")
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        # Enable monitoring with our SDK - no need to pass llm_client anymore
        # The SDK will automatically detect and patch Anthropic instances
        start_monitoring(
            agent_id="weather-agent", 
            config={
                "log_file": "output/weather_monitoring.json"
            }
        )
        logger.info("Monitoring enabled for Weather AI Agent")
        
        # Create Anthropic client - it will be automatically patched
        self.anthropic = Anthropic()
        logger.info("Created Anthropic client instance")

    async def connect_to_server(self, server_script_path: str):
        """Connect to the Weather MCP server.

        Args:
            server_script_path: Path to the server script
        """
        logger.info(f"Connecting to Weather MCP server: {server_script_path}")

        # Validate script path
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        # Set up server parameters
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
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
        """Process a user query using Claude and available weather tools.

        Args:
            query: User's query about weather

        Returns:
            Response text with weather information
        """
        # Don't log the query as it may contain sensitive information
        logger.info("Processing user query")

        # Initial message
        messages = [{"role": "user", "content": query}]

        # Get available tools
        response = await self.session.list_tools()
        available_tools = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
            for tool in response.tools
        ]

        try:
            # Initial Claude API call
            logger.info("Calling Claude API")
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
            )
            
            # Debug the response type
            logger.info(f"Claude API response type: {type(response)}")
            
            # Process response and handle tool calls
            tool_results = []
            final_text = []

            # Check if response has content attribute
            if not hasattr(response, "content"):
                # Handle the case where the response might be a dict or string
                logger.warning(f"Unexpected response type: {type(response)}")
                if isinstance(response, dict) and "content" in response:
                    assistant_message_content = response["content"]
                    if isinstance(assistant_message_content, list):
                        for content in assistant_message_content:
                            if isinstance(content, dict) and content.get("type") == "text":
                                final_text.append(content.get("text", ""))
                    else:
                        # Treat content as text if it's not a list
                        final_text.append(str(assistant_message_content))
                else:
                    # Fallback to string representation
                    final_text.append(str(response))
                return "\n".join(final_text)
                
            # Process content items from the Anthropic response
            assistant_message_content = []
            for content in response.content:
                # Debug each content item
                logger.info(f"Processing content item type: {getattr(content, 'type', 'unknown')}")
                
                if hasattr(content, "type") and content.type == "text":
                    final_text.append(content.text)
                    assistant_message_content.append(content)
                elif hasattr(content, "type") and content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input

                    # Don't log tool arguments as they may contain sensitive information
                    logger.info(f"Calling tool: {tool_name}")
                    
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    tool_results.append({"call": tool_name, "result": result})
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Add the tool call and result to the conversation
                    assistant_message_content.append(content)
                    messages.append({"role": "assistant", "content": assistant_message_content})
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )

                    # Get next response from Claude
                    response = self.anthropic.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=messages,
                        tools=available_tools,
                    )

                    final_text.append(response.content[0].text)
                else:
                    # Handle unknown content type
                    logger.warning(f"Unknown content type: {getattr(content, 'type', 'unknown')}")
                    if isinstance(content, dict):
                        # Try to extract text from dict
                        if "text" in content:
                            final_text.append(content["text"])
                    else:
                        # Fallback to string representation
                        final_text.append(str(content))

            logger.info("Query processing completed")
            return "\n".join(final_text)
            
        except Exception as e:
            # Log the error details (safely)
            logger.error(f"Error in process_query: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
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
                # Don't log the exception directly as it might contain sensitive data
                logger.error(f"Error processing query: {type(e).__name__}")
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources and disable monitoring."""
        logger.info("Cleaning up resources")
        await self.exit_stack.aclose()
        stop_monitoring()
        logger.info("Monitoring stopped")


async def main():
    """Main function to run the Weather AI Agent."""
    # Get the path to the weather server script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script_path = os.path.join(script_dir, "weather_server.py")

    # Create and run the agent
    agent = WeatherAIAgent()
    try:
        # Connect to the weather server
        await agent.connect_to_server(server_script_path)

        # Start the interactive chat loop
        await agent.chat_loop()
    finally:
        # Clean up resources
        await agent.cleanup()


if __name__ == "__main__":
    print("Starting Weather AI Agent")
    asyncio.run(main())
