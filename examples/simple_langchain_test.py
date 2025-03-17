#!/usr/bin/env python3
"""
Simple LangChain Test for Monitoring

This script tests the Cylestio Monitor integration with LangChain,
specifically to verify the capture of both request and response events.
"""

import os
import sys
import time
import json
from pathlib import Path

try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain_anthropic import ChatAnthropic
except ImportError:
    print("Error: This test requires LangChain and Anthropic. Install with:")
    print("pip install langchain langchain-anthropic")
    sys.exit(1)

# Import Cylestio Monitor
from cylestio_monitor import enable_monitoring

# Create output directory
os.makedirs("output", exist_ok=True)

def get_api_key():
    """Get Anthropic API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        # Try to load from .env file
        env_path = Path(".env")
        if env_path.exists():
            with env_path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip("'").strip('"')
                            break
    
    if not api_key:
        # Try to load from api_key.txt
        try:
            with open("api_key.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            pass
    
    return api_key

def main():
    """Run a simple LangChain test with monitoring."""
    api_key = get_api_key()
    
    if not api_key:
        print("Error: No ANTHROPIC_API_KEY found in environment, .env file, or api_key.txt")
        sys.exit(1)
    
    # Create a log file for this test
    log_file = "output/langchain_test.json"
    
    # Enable monitoring
    print("Enabling monitoring...")
    enable_monitoring(
        agent_id="langchain-test",
        log_file=log_file
    )
    
    # Set up LangChain components
    print("Setting up LangChain...")
    try:
        llm = ChatAnthropic(
            anthropic_api_key=api_key,
            model_name="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.7
        )
        
        # Create a simple prompt template
        template = """You are a helpful assistant.

Please answer the following question concisely:
{question}

Your answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["question"]
        )
        
        # Create the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Run the chain with a simple question
        question = "What is machine learning in simple terms?"
        print(f"\nSending question: {question}")
        
        # Process the question
        start_time = time.time()
        result = chain.invoke({"question": question})
        duration = time.time() - start_time
        
        # Display results
        print(f"Response received in {duration:.2f} seconds.\n")
        print(f"Response: {result['text']}\n")
        
        # Check log file
        try:
            with open(log_file, "r") as f:
                log_lines = f.readlines()
                
            print(f"Log file contains {len(log_lines)} events.")
            print("Event types:")
            
            # Parse JSON and print details
            event_types = []
            for line in log_lines:
                try:
                    event = json.loads(line)
                    event_type = event.get("event_type", "unknown")
                    if event_type not in event_types:
                        event_types.append(event_type)
                except json.JSONDecodeError:
                    continue
            
            for i, event_type in enumerate(event_types):
                print(f"  {i+1}. {event_type}")
                
            # Look for request and response events
            request_count = sum(1 for line in log_lines if '"event_type": "LLM_call_start"' in line)
            response_count = sum(1 for line in log_lines if '"event_type": "LLM_call_finish"' in line)
            
            print(f"\nFound {request_count} request events and {response_count} response events.")
            if response_count == 0:
                print("Warning: No response events found. This may indicate an issue with the monitoring.")
                
        except Exception as e:
            print(f"Error reading log file: {e}")
        
    except Exception as e:
        print(f"Error during test execution: {e}")
    
    print("\nTest complete! Check the log file for details.")

if __name__ == "__main__":
    main() 