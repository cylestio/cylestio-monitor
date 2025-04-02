#!/usr/bin/env python
"""
Run script for the customer support bot
"""

import argparse

from langchain_core.messages import HumanMessage
from main import part1_agent, part2_agent, part3_agent, part4_agent


def main():
    parser = argparse.ArgumentParser(description="Run the customer support bot")
    parser.add_argument(
        "--agent",
        type=int,
        choices=[1, 2, 3, 4],
        default=4,
        help="Which agent version to run (1-4, default=4)",
    )
    args = parser.parse_args()

    # Select the agent based on the argument
    if args.agent == 1:
        agent = part1_agent
        print("Running Part 1: Zero-shot Agent")
    elif args.agent == 2:
        agent = part2_agent
        print("Running Part 2: Confirmation Agent")
    elif args.agent == 3:
        agent = part3_agent
        print("Running Part 3: Conditional Interrupt Agent")
    else:
        agent = part4_agent
        print("Running Part 4: Specialized Workflows Agent")

    # Simple chat loop
    messages = []

    print("Customer Support Bot (type 'exit' to quit)")
    print("-------------------------------------------")

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        # Add the user message to the conversation
        user_message = HumanMessage(content=user_input)
        messages.append(user_message)

        # Invoke the agent
        if args.agent in [1, 2, 3, 4]:
            result = agent.invoke({"messages": messages, "sender": "human"})

            # Update the messages
            messages = result["messages"]

            # Print the agent's response
            for message in messages:
                if (
                    message.type == "ai"
                    and messages.index(message) >= len(messages) - 2
                ):
                    print(f"Agent: {message.content}")
        else:
            print("Invalid agent selection")
            break


if __name__ == "__main__":
    main()
