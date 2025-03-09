"""Example of Model Context Protocol integration with Cylestio Monitor."""

import asyncio
import os
from cylestio_monitor.mcp.client import MCPClient
from cylestio_monitor.mcp.server import MCPServer

async def main():
    """Run MCP example."""
    # Start server
    server = MCPServer(
        api_key="test-key",
        host="localhost",
        port=8000
    )
    
    # Start server in background
    server_task = asyncio.create_task(
        asyncio.to_thread(server.run)
    )
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    try:
        # Initialize client
        client = MCPClient(
            base_url="http://localhost:8000",
            api_key="test-key"
        )
        
        # Create context
        context = client.create_context({
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "What is the capital of France?"
                }
            ],
            "metadata": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        })
        
        # Get completion
        response = client.get_completion(context)
        print("\nInitial Response:")
        print(f"Assistant: {response['message']['content']}")
        print(f"Token Usage: {response['usage']}")
        
        # Update context and get another completion
        context = client.update_context(context, {
            "messages": [
                {
                    "role": "user",
                    "content": "What is its population?"
                }
            ]
        })
        
        response = client.get_completion(context)
        print("\nFollow-up Response:")
        print(f"Assistant: {response['message']['content']}")
        print(f"Token Usage: {response['usage']}")
        
    finally:
        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 