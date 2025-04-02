"""Example of using Cylestio Monitor with OpenAI.

This example demonstrates how to use Cylestio Monitor with OpenAI,
testing all three types of completions:
1. Chat Model: gpt-3.5-turbo
2. Text Completion Model: gpt-3.5-turbo-instruct (replacement for text-ada-001)
3. Code Completion Model: gpt-3.5-turbo-instruct (replacement for code-cushman-001)

Note: Both text-ada-001 and code-cushman-001 have been deprecated by OpenAI.
      We use gpt-3.5-turbo-instruct for both text and code completions as recommended.

Requirements:
    - openai Python package installed
    - cylestio_monitor package installed
"""

import os
import time

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Step 2: Import Cylestio Monitor
import cylestio_monitor

# Step 3: Initialize monitoring
cylestio_monitor.start_monitoring(
    agent_id="openai-example-agent",
    config={
        "debug_level": "INFO",
        "development_mode": True,
        "log_file": "openai_example.json",
    },
)

# Step 4: Import OpenAI
from openai import OpenAI

# Step 5: Create an OpenAI client with API key
# Note: The client will be automatically patched by Cylestio Monitor
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # Using the API key from .env


def main():
    """Run the OpenAI example."""
    print("Starting OpenAI example...")

    # Example 1: Chat Completions API (Chat Model Type)
    try:
        print("\n1. Running Chat Completions example (gpt-3.5-turbo):")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Tell me about AI monitoring in one paragraph.",
            },
        ]

        # This call will be automatically monitored by Cylestio
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, temperature=0.7, max_tokens=150
        )

        print(f"Chat response: {response.choices[0].message.content}")
        print("✅ Chat completion test completed successfully")

    except Exception as e:
        print(f"❌ Error in Chat Completions example: {e}")

    # Example 2: Text Completions API (Text Model Type)
    try:
        print("\n2. Running Text Completions example (gpt-3.5-turbo-instruct):")

        # This call will be automatically monitored by Cylestio
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="Write a short poem about AI monitoring.",
            temperature=0.7,
            max_tokens=100,
        )

        print(f"Text completion response: {response.choices[0].text}")
        print("✅ Text completion test completed successfully")

    except Exception as e:
        print(f"❌ Error in Text Completions example: {e}")

    # Example 3: Code Completions (using gpt-3.5-turbo-instruct as replacement for code-cushman-001)
    try:
        print("\n3. Running Code Completions example (gpt-3.5-turbo-instruct):")

        code_prompt = """
        # Write a Python function that:
        # 1. Takes a list of numbers as input
        # 2. Returns the sum of all even numbers in the list

        def sum_even_numbers(numbers):
        """

        # This call will be automatically monitored by Cylestio
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=code_prompt,
            temperature=0.2,  # Lower temperature for more deterministic code generation
            max_tokens=150,
            stop=["```"],  # Stop generation at code block end
        )

        print(f"Code completion response:\n{response.choices[0].text}")
        print("✅ Code completion test completed successfully")

    except Exception as e:
        print(f"❌ Error in Code Completions example: {e}")

    # Wait for all telemetry to be processed
    print("\nWaiting for telemetry processing...")
    time.sleep(2)

    print("\nExample completed! All three model types tested:")
    print("1. Chat Model: gpt-3.5-turbo")
    print("2. Text Completion Model: gpt-3.5-turbo-instruct")
    print(
        "3. Code Completion Model: gpt-3.5-turbo-instruct (replacement for code-cushman-001)"
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        # Always clean up monitoring when done
        cylestio_monitor.stop_monitoring()
