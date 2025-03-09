"""Simple example using Anthropic with Cylestio Monitor."""

import os
from dotenv import load_dotenv
from anthropic import Anthropic
from cylestio_monitor import init_monitoring
from cylestio_monitor.patchers import AnthropicPatcher

# Load environment variables
load_dotenv()

def main():
    # Initialize Anthropic client
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    
    # Initialize monitoring with Anthropic patcher
    monitor = init_monitoring(
        output_file="simple_monitoring.json",
        patchers=[
            AnthropicPatcher(client=client)
        ]
    )
    
    # Example queries
    queries = [
        "What's the weather in London?",
        "Tell me about Tokyo",
        "What's 2+2?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        
        # Create message
        message = client.messages.create(
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model="claude-3-haiku-latest",
        )
        
        # Print response
        print(f"Response: {message.content[0].text}")
    
    # Stop monitoring
    monitor.stop()

if __name__ == "__main__":
    main() 