"""LangChain chatbot example with Cylestio monitoring.

This example demonstrates a conversational chatbot using LangChain with:
- Anthropic Claude as the LLM
- Conversation memory
- Cylestio monitoring integration to track all LLM calls and chain executions
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationChain
from langchain_core.messages import HumanMessage, AIMessage

# Import the Cylestio Monitor functions
from cylestio_monitor import start_monitoring

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if not env_path.exists():
        return {}
    
    env_vars = {}
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip("'").strip('"')
    return env_vars

def validate_environment():
    """Validate that all required environment variables are set.
    
    First checks environment variables, then falls back to .env file.
    """
    # Check environment first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # If not in environment, try .env file
    if not api_key:
        env_vars = load_env_file()
        api_key = env_vars.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment or .env file.")
        print("Please either:")
        print("1. Set it in your environment with: export ANTHROPIC_API_KEY='your-api-key'")
        print("2. Add it to your .env file as: ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)
    
    return api_key

class MonitoredChatbot:
    """A monitored chatbot implementation using LangChain and Anthropic."""
    
    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        """Initialize the chatbot with specified model.
        
        Args:
            model_name: The Anthropic model to use
        """
        # Validate environment variables
        api_key = validate_environment()
        
        # Enable monitoring with minimal parameters
        start_monitoring(agent_id="chatbot-agent", config={"log_file":"output/chatbot_monitoring-new.json"})
        
        # Initialize the LLM
        self.llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=api_key,
            temperature=0.7
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Create conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant engaged in a conversation."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        # Create conversation chain
        self.chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=True
        )
    
    def chat(self, message: str) -> str:
        """Process a chat message and return the response.
        
        Args:
            message: The user's input message
            
        Returns:
            The AI assistant's response
        """
        try:
            # Invoke the chain - no need to explicitly set callbacks as our patching should handle it
            response = self.chain.invoke({"input": message})
                
            return response["response"]
            
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp
        """
        return datetime.now().isoformat()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        This is a simple approximation. For production use, consider using a tokenizer.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple approximation: 4 characters per token on average
        return len(text) // 4
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the current chat history.
        
        Returns:
            List of message dictionaries with role and content
        """
        messages = self.memory.chat_memory.messages
        return [
            {"role": "human" if isinstance(m, HumanMessage) else "ai", 
             "content": m.content}
            for m in messages
        ]

def main():
    """Run an example conversation with the monitored chatbot."""
    
    print("Initializing the chatbot with monitoring...")
    # Create chatbot
    chatbot = MonitoredChatbot()
    print("Chatbot initialized. Monitoring enabled.")
    
    log_file_path = "output/chatbot_monitoring.json"
    
    # Helper function to check log file
    def check_log_file_growth():
        try:
            # Get the current log file size
            import os
            if os.path.exists(log_file_path):
                size = os.path.getsize(log_file_path)
                print(f"Current log file size: {size} bytes")
                
                # Print the number of lines in the log file
                with open(log_file_path, 'r') as f:
                    line_count = len(f.readlines())
                    print(f"Log file contains {line_count} events")
            else:
                print("Log file does not exist yet")
        except Exception as e:
            print(f"Error checking log file: {e}")
    
    # Example conversation
    messages = [
        "Hi! Can you help me learn about artificial intelligence?",
        "What are some key concepts I should understand?",
        "Can you explain machine learning in simple terms?",
        "Thank you for the explanation!"
    ]
    
    print("\nStarting conversation with the chatbot...")
    print("=" * 50)
    
    # Initial log file state
    print("\nChecking initial log file state:")
    check_log_file_growth()
    
    # Process messages
    for i, msg in enumerate(messages):
        print(f"\n[Turn {i+1}] Human: {msg}")
        response = chatbot.chat(msg)
        print(f"[Turn {i+1}] Assistant: {response}")
        
        # Check log file after each interaction
        print(f"\nChecking log file after turn {i+1}:")
        check_log_file_growth()
    
    print("\n" + "=" * 50)
    print("Conversation completed.")
    
    # Final log file check
    print("\nFinal log file state:")
    check_log_file_growth()
    
    # Print chat history
    print("\nChat History:")
    for msg in chatbot.get_chat_history():
        print(f"{msg['role'].title()}: {msg['content']}")
    
    print("\nMonitoring logs saved to output/chatbot_monitoring.json")
    print("Check the logs to see the detailed monitoring information.")

if __name__ == "__main__":
    main() 