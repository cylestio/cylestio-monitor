"""Example of a weather agent using MCP with Anthropic.

This example demonstrates:
1. Setting up an agent with MCP and Anthropic
2. Integrating Cylestio Monitor for monitoring
3. Handling weather queries using Claude
4. Monitoring agent interactions
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from anthropic import Anthropic
from cylestio_monitor import init_monitoring
from cylestio_monitor.patchers import AnthropicPatcher, MCPPatcher

# Load environment variables from .env file
load_dotenv()

# Add parent directory to Python path to import MCP implementation
sys.path.append(str(Path(__file__).parent.parent))
from mcp_implementation.client import ClientSession, Context, Message

class WeatherAgent:
    """Weather agent implementation using MCP and Anthropic."""
    
    def __init__(self):
        """Initialize weather agent."""
        self.mcp_client = ClientSession()
        
        # Initialize Anthropic client with API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.anthropic_client = Anthropic(api_key=api_key)
        
    async def process_query(self, query: str) -> str:
        """Process a weather query.
        
        Args:
            query: User query
            
        Returns:
            Response string
        """
        # Create initial messages
        messages = [{"role": "user", "content": query}]
        
        # Get available tools
        response = await self.mcp_client.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]
        
        # Create MCP context
        context = Context(
            messages=[Message(role="user", content=query)],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "client_id": "weather_demo"
            }
        )
        
        try:
            # Initial Claude API call
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
                system="You are a helpful weather assistant. You can use tools to get weather information. Keep your responses concise and focused on weather information. Do not show your thinking process."
            )
            
            # Process response and handle tool calls
            tool_results = []
            final_text = []
            
            for content in response.content:
                if content.type == 'text':
                    # Remove thinking process
                    text = content.text
                    if "<thinking>" in text:
                        text = text.split("</thinking>")[-1].strip()
                    final_text.append(text)
                elif content.type == 'tool_calls':
                    for tool_call in content.tool_calls:
                        tool_name = tool_call.name
                        tool_args = tool_call.parameters
                        
                        # Execute tool call
                        result = await self.mcp_client.call_tool(tool_name, tool_args)
                        tool_results.append({"call": tool_name, "result": result})
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                        
                        messages.append({
                            "role": "assistant",
                            "content": [{
                                "type": "tool_calls",
                                "tool_calls": [tool_call]
                            }]
                        })
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_call_id": tool_call.id,
                                "content": result.content
                            }]
                        })
                        
                        # Get next response from Claude
                        response = self.anthropic_client.messages.create(
                            model="claude-3-opus-20240229",
                            max_tokens=1000,
                            messages=messages,
                            tools=available_tools,
                            system="You are a helpful weather assistant. You can use tools to get weather information. Keep your responses concise and focused on weather information. Do not show your thinking process."
                        )
                        
                        # Remove thinking process from response
                        text = response.content[0].text
                        if "<thinking>" in text:
                            text = text.split("</thinking>")[-1].strip()
                        final_text.append(text)
            
            # Update MCP context with final response
            context.messages.append(Message(role="assistant", content="\n".join(final_text)))
            await self.mcp_client.get_completion(context)
            
            return "\n".join(final_text)
                
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            context.messages.append(Message(role="assistant", content=error_msg))
            await self.mcp_client.get_completion(context)
            return error_msg

async def main():
    """Run the weather agent example."""
    # Initialize agent
    weather_agent = WeatherAgent()
    
    # Initialize monitoring with both patchers
    monitor = init_monitoring(
        output_file="weather_monitoring.json",
        patchers=[
            AnthropicPatcher(client=weather_agent.anthropic_client),
            MCPPatcher(client=weather_agent.mcp_client)
        ]
    )
    
    # Example queries
    queries = [
        "What's the weather in London?",
        "Tell me the weather in Tokyo",
        "What's the weather like in New York?",
        # Test invalid queries
        "Hello",
        "What's the capital of France?"
    ]
    
    # Process queries
    for query in queries:
        try:
            response = await weather_agent.process_query(query)
            print("\nQuery:", query)
            print("Response:", response)
        except Exception as e:
            print(f"Error processing query '{query}': {str(e)}")
            
    # Stop monitoring
    monitor.stop()

if __name__ == "__main__":
    asyncio.run(main()) 