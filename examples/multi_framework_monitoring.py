#!/usr/bin/env python3
"""
Multi-Framework Monitoring Example

This example demonstrates how Cylestio Monitor can track and log responses
from different LLM frameworks:
1. Direct Anthropic API calls
2. LangChain chains
3. LangGraph agents

All these are handled by the same monitoring infrastructure.
"""

import json
import os
import time
from typing import Dict, Any, List

# Import Cylestio Monitor - core SDK
from cylestio_monitor import start_monitoring, log_to_file_and_db

# Import optional LLM frameworks (check availability)
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Anthropic SDK not installed. Skipping direct API examples.")

try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain_anthropic import ChatAnthropic
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not installed. Skipping LangChain examples.")

try:
    from langgraph.graph import StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("LangGraph not installed. Skipping LangGraph examples.")


def create_output_dir():
    """Create output directory for logs."""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def test_direct_anthropic(api_key: str):
    """Test direct Anthropic API calls."""
    if not ANTHROPIC_AVAILABLE:
        return

    print("\n=== Testing Direct Anthropic API ===")
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Enable monitoring with this client
    start_monitoring(
        agent_id="direct-anthropic-example",
        log_file=os.path.join(create_output_dir(), "anthropic_logs"),
    )
    
    # Make a direct API call
    prompt = "Write a short poem about monitoring AI systems."
    
    print(f"Sending prompt: {prompt}")
    start_time = time.time()
    
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        duration = time.time() - start_time
        print(f"Response received in {duration:.2f} seconds")
        print(f"Response: {message.content}")
        
        # Also log a custom event
        log_to_file_and_db(
            event_type="direct_anthropic_complete",
            data={
                "prompt": prompt,
                "response": message.content,
                "model": "claude-3-haiku-20240307",
                "duration": duration
            },
            channel="EXAMPLE"
        )
    except Exception as e:
        print(f"Error during Anthropic API call: {e}")


def test_langchain(api_key: str):
    """Test LangChain with Anthropic backend."""
    if not LANGCHAIN_AVAILABLE:
        return

    print("\n=== Testing LangChain with Anthropic ===")
    
    # Create Anthropic LLM via LangChain
    llm = ChatAnthropic(
        anthropic_api_key=api_key,
        model_name="claude-3-haiku-20240307",
        max_tokens=300
    )
    
    # Create LangChain prompt template
    template = """You are a helpful AI assistant.

Question: {question}

Your answer:"""
    
    prompt = PromptTemplate(
        input_variables=["question"],
        template=template
    )
    
    # Create LangChain chain
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Enable monitoring
    start_monitoring(
        agent_id="langchain-example",
        log_file=os.path.join(create_output_dir(), "langchain_logs"),
    )
    
    # Run the chain
    question = "List three benefits of monitoring AI systems."
    print(f"Sending question: {question}")
    
    try:
        start_time = time.time()
        result = chain.invoke({"question": question})
        duration = time.time() - start_time
        
        print(f"Response received in {duration:.2f} seconds")
        print(f"Response: {result['text']}")
    except Exception as e:
        print(f"Error during LangChain execution: {e}")


def test_langgraph(api_key: str):
    """Test LangGraph with Anthropic backend."""
    if not LANGGRAPH_AVAILABLE:
        return

    print("\n=== Testing LangGraph with Anthropic ===")
    
    # Define a simple state for LangGraph
    class GraphState(dict):
        """Simple state dictionary for the graph."""
        def __init__(self, question=""):
            self.question = question
            self.answer = ""
        
        @property
        def question(self) -> str:
            return self.get("question", "")
        
        @question.setter
        def question(self, value: str):
            self["question"] = value
        
        @property
        def answer(self) -> str:
            return self.get("answer", "")
        
        @answer.setter
        def answer(self, value: str):
            self["answer"] = value
    
    # Create LangChain LLM (for use in LangGraph)
    llm = ChatAnthropic(
        anthropic_api_key=api_key,
        model_name="claude-3-haiku-20240307",
        max_tokens=300
    )
    
    # Define the LLM node function
    def llm_node(state: GraphState) -> Dict[str, Any]:
        """Use LLM to generate an answer to the question."""
        question = state.question
        
        prompt = f"""You are a helpful AI assistant.

Question: {question}

Your answer:"""
        
        messages = [{"role": "user", "content": prompt}]
        result = llm.invoke(messages)
        
        # Extract response
        if hasattr(result, "content"):
            answer = result.content
        else:
            answer = str(result)
        
        # Return updated state
        return {"answer": answer}
    
    # Create the graph
    graph = StateGraph(GraphState)
    
    # Add nodes to the graph
    graph.add_node("llm", llm_node)
    
    # Connect nodes
    graph.set_entry_point("llm")
    graph.add_edge("llm", "END")
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    # Enable monitoring
    start_monitoring(
        agent_id="langgraph-example",
        log_file=os.path.join(create_output_dir(), "langgraph_logs"),
    )
    
    # Run the graph
    question = "What patterns should we monitor in AI systems for safety?"
    print(f"Sending question: {question}")
    
    try:
        start_time = time.time()
        result = compiled_graph.invoke({"question": question})
        duration = time.time() - start_time
        
        print(f"Response received in {duration:.2f} seconds")
        print(f"Response: {result['answer']}")
    except Exception as e:
        print(f"Error during LangGraph execution: {e}")


def main():
    """Main function to run the examples."""
    # Get API key from environment or example file
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        try:
            with open("api_key.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            print("Error: ANTHROPIC_API_KEY not found in environment or api_key.txt file.")
            print("Please set your API key using one of these methods.")
            return
    
    # Run examples for available frameworks
    if ANTHROPIC_AVAILABLE:
        test_direct_anthropic(api_key)
    
    if LANGCHAIN_AVAILABLE:
        test_langchain(api_key)
    
    if LANGGRAPH_AVAILABLE:
        test_langgraph(api_key)
    
    print("\nAll examples completed. Check the output directory for logs.")
    print("Tip: Compare the logs to see how different frameworks are monitored.")


if __name__ == "__main__":
    main() 