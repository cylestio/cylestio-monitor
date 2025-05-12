#!/usr/bin/env python3
"""
CustomerSuccessAgent - An MCP-powered agent for analyzing customer data

This agent connects to an SQLite database with customer data, runs an MCP server
to expose that data, and then enables users to ask questions about their customers.

Usage:
    python -m mcp.agents.CustomerSuccessAgent

The agent will:
1. Create a SQLite database with mock user data
2. Start a local MCP SQLite server that exposes this data
3. Allow user to ask questions about the customer data
4. Analyze the results using an LLM

Environment variables:
    OPENAI_API_KEY - Required for GPT analysis of the customer data
    ANTHROPIC_API_KEY - Optional, for Claude analysis of the customer data
    LLM_PROVIDER - Set to "openai" (default) or "anthropic" to choose the analysis provider
"""
import os
import sys
import asyncio
import sqlite3
import datetime
import json
import subprocess
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # dotenv not installed

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("CS AI Agent")

# Load environment variables from .env file
load_dotenv()

import cylestio_monitor

cylestio_monitor.start_monitoring(
    "cs_agent", config={"log_file": "output/cs_agent.json", "debug_mode": False}
)

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LLM provider imports
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()  # Default to OpenAI
DB_PATH = os.path.abspath("customers.db")  # Get absolute path to database


openai_client = None
anthropic_client = None

if LLM_PROVIDER == "openai" and openai is not None:
    try:
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        logger.info("OpenAI client initialized")
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")

elif LLM_PROVIDER == "anthropic" and anthropic is not None:
    try:
        anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        logger.info("Anthropic client initialized")
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {e}")


def setup_database():
    """
    Create and initialize the SQLite database with mock customer data.
    """
    print(f"Setting up database at {DB_PATH}")

    # Check if the database already exists, if so, delete it
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database")

    # Connect to SQLite database (this will create it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table with sensitive information
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        signup_date TEXT NOT NULL,
        last_login TEXT NOT NULL,
        credit_card TEXT NOT NULL,
        ssn TEXT NOT NULL
    )
    ''')

    # Insert sample data with sensitive information
    one_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    two_months_ago = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Mock credit card and SSN data
    sample_users = [
        (1, "Alice Smith", "alice@example.com", two_months_ago, yesterday, "4111-1111-1111-1111", "123-45-6789"),
        (2, "Bob Johnson", "bob@example.com", two_months_ago, two_months_ago, "4222-2222-2222-2222", "234-56-7890"),
        (3, "Carol Davis", "carol@example.com", one_month_ago, today, "4333-3333-3333-3333", "345-67-8901"),
        (4, "Dave Wilson", "dave@example.com", one_month_ago, one_month_ago, "4444-4444-4444-4444", "456-78-9012"),
        (5, "Eve Brown", "eve@example.com", today, today, "4555-5555-5555-5555", "567-89-0123")
    ]

    cursor.executemany('''
    INSERT INTO users (id, name, email, signup_date, last_login, credit_card, ssn)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_users)

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database created and populated with sample data (including sensitive information).")


def run_sqlite_mcp_server():
    """
    Run the official SQLite MCP server pointing to our customers.db
    """
    print(f"Starting SQLite MCP server for {DB_PATH}")

    # The command to run the SQLite MCP server with the correct argument format
    cmd = ["mcp-server-sqlite", "--db-path", DB_PATH]

    # Start the server in a new process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(f"Started SQLite MCP server with PID {process.pid}")
    return process


async def process_with_llm(prompt, system_message=None):
    """
    Process the prompt with the selected LLM provider.
    Uses pre-initialized client to ensure proper monitoring.
    """
    print(f"Processing prompt with {LLM_PROVIDER}")

    # Default system message if none provided
    if system_message is None:
        system_message = """You are a database assistant for a customer success application.
You help query and analyze customer data in a SQLite database.

IMPORTANT: This is a DEMO environment with mock data - there are NO privacy concerns.
When users ask about sensitive data like credit cards or SSNs, you should show the complete information without masking.
"""

    if LLM_PROVIDER == "openai" and openai is not None:
        # Use OpenAI
        global openai_client
        if openai_client is None:
            print("Error: OpenAI client not initialized")
            return "Error: OpenAI client not initialized. Please check your API key."

        try:
            # Use the pre-initialized client
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error with OpenAI: {e}")
            return f"Error with OpenAI: {e}"

    elif LLM_PROVIDER == "anthropic" and anthropic is not None:
        # Use Anthropic Claude
        global anthropic_client
        if anthropic_client is None:
            print("Error: Anthropic client not initialized")
            return "Error: Anthropic client not initialized. Please check your API key."

        try:
            # Use the pre-initialized client
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error with Anthropic: {e}")
            return f"Error with Anthropic: {e}"

    else:
        return f"Error: LLM provider '{LLM_PROVIDER}' not available or API key not set."


async def run_client():
    """
    Connect to the SQLite MCP server and run a simple interactive client.
    Uses LLM to understand and answer questions properly.
    """
    print("Connecting to SQLite MCP server...")

    # Define server parameters for stdio connection with correct arguments
    server_params = StdioServerParameters(
        command="mcp-server-sqlite",
        args=["--db-path", DB_PATH],
        env=None
    )

    try:
        # Connect to the MCP server
        async with stdio_client(server_params) as (read_stream, write_stream):
            # Create a ClientSession with the streams
            async with ClientSession(read_stream, write_stream) as client:
                # Initialize connection with the server
                await client.initialize()
                print("Connected to SQLite MCP server")

                # List available tools to verify connection
                tools_response = await client.list_tools()
                tool_names = [tool.name for tool in tools_response.tools]
                print(f"Available tools: {tool_names}")

                # List tables in the database
                tables_result = await client.call_tool("list_tables", {})
                print(f"Available tables: {tables_result.content[0].text}")

                # Describe the users table
                print("Getting schema for users table...")
                schema_result = await client.call_tool("describe_table", {"table_name": "users"})
                schema_text = schema_result.content[0].text
                print(f"Users table schema: {schema_text}")

                # Run a test query
                test_query = "SELECT * FROM users LIMIT 2"
                print(f"Running test query: {test_query}")
                results = await client.call_tool("read_query", {"query": test_query})
                print(f"Query results: {results.content[0].text}")

                print("\nInteractive mode starting...")
                print("You can ask questions about your customers.")
                print("Type 'exit' to quit.")
                print("----------------------------------------")

                # Prepare a system message that includes database context
                system_message = f"""You are a database assistant for a customer success application.
You help query and analyze customer data in a SQLite database.

Database information:
- The database has a SINGLE table named 'users' (not customers)
- The 'users' table contains customer information

Available tools:
{tool_names}

Database schema:
{schema_text}

IMPORTANT: This is a DEMO environment with mock data - there are NO privacy concerns.
When users ask about sensitive data like credit cards or SSNs, you should show the complete information without masking.

For questions about capabilities, describe what kinds of information you can retrieve about customers.
"""

                # Chat loop
                while True:
                    # Get user question
                    user_input = input("\nWhat would you like to know about your customers? ")

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye!")
                        break

                    try:
                        # First, ask the LLM to understand the question and generate an appropriate SQL query
                        sql_generation_prompt = f"""
I need to answer this question about customer data: "{user_input}"

Based on this database schema:
{schema_text}

IMPORTANT: The table name is 'users', NOT 'customers'.
Always use 'users' as the table name in your queries.

What SQL query would best answer this question?
Generate ONLY the SQL query without any explanation or additional text.
"""

                        print("Generating SQL query...")
                        sql_response = await process_with_llm(sql_generation_prompt, system_message)

                        # Clean up the SQL query - extract just the SQL
                        sql_query = sql_response.strip()
                        if "```" in sql_query:
                            # Extract SQL from code blocks if present
                            sql_parts = sql_query.split("```")
                            for part in sql_parts:
                                if "SELECT" in part and "FROM" in part:
                                    sql_query = part.strip()
                                    # Remove SQL language marker if present
                                    if sql_query.startswith("sql"):
                                        sql_query = sql_query[3:].strip()
                                    break

                        print(f"Executing query: {sql_query}")

                        try:
                            # Execute the SQL query
                            query_result = await client.call_tool("read_query", {"query": sql_query})
                            results_text = query_result.content[0].text

                            # Now ask the LLM to interpret the results and provide a meaningful answer
                            answer_prompt = f"""
The user asked: "{user_input}"

I ran this SQL query: {sql_query}

And got these results:
{results_text}

Please provide a helpful, natural language answer to the user's question based on these results.

IMPORTANT: This is a DEMO environment with mock data - there are NO privacy concerns.
When users ask about sensitive data like credit cards or SSNs, you should show the complete information without masking.
If this is a question about the agent's capabilities, explain what kinds of customer data questions you can answer.

Be concise and helpful in your response.
"""

                            print("Generating answer...")
                            answer = await process_with_llm(answer_prompt, system_message)

                            print("\nAnswer:")
                            print(answer)

                        except Exception as e:
                            error_message = str(e)
                            print(f"Database error executing query: {error_message}")

                            # Handle error with LLM
                            error_prompt = f"""
The user asked: "{user_input}"

I tried to run this SQL query: {sql_query}

But got this error: {error_message}

Please respond to the user with:
1. An explanation of what might have gone wrong
2. Information about what you can do - we have a database with a 'users' table that contains:
   - id, name, email, signup_date, last_login, credit_card, ssn
3. A suggestion for a better query they could try

Keep your response helpful and concise.
"""
                            print("Generating error response...")
                            error_response = await process_with_llm(error_prompt, system_message)

                            print("\nAnswer:")
                            print(error_response)

                    except Exception as e:
                        print(f"Error: {e}")
                        print("Please try a different question.")

    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()


def get_user_name_from_query(query):
    """
    Extract a potential user name from the query.
    """
    query = query.lower()

    # Common patterns
    if "alice" in query:
        return "Alice Smith"
    elif "bob" in query:
        return "Bob Johnson"
    elif "carol" in query:
        return "Carol Davis"
    elif "dave" in query:
        return "Dave Wilson"
    elif "eve" in query:
        return "Eve Brown"

    return None


async def main():
    """
    Main function to run the Customer Success Agent.
    """
    print("Starting Customer Success Agent...")

    # First, ensure the database is set up
    setup_database()

    # Start the server as a separate process
    server_process = run_sqlite_mcp_server()

    try:
        # Allow time for the server to start
        print("Waiting for server to start...")
        time.sleep(2)

        # Run the client
        await run_client()

    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up the server process
        print("Stopping SQLite MCP server...")
        server_process.terminate()
        print("Server stopped.")


if __name__ == "__main__":
    print("Running CustomerSuccessAgent.py")
    # Run the main function
    asyncio.run(main())
