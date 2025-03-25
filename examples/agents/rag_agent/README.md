# RAG Agent with Cylestio Monitoring

This example demonstrates a RAG (Retrieval Augmented Generation) agent using LangChain integrated with Cylestio Monitoring for complete visibility into the agent's operations.

## Features

- **LangChain Integration**: Uses LangChain's components for document retrieval and generation
- **Anthropic Claude**: Uses Claude models for high-quality text generation
- **Vector Store**: Implements a Chroma vector store for document retrieval
- **Comprehensive Monitoring**: Full integration with Cylestio Monitor SDK to track all aspects of the RAG process
- **Detailed Logging**: Records all retrieval metrics, token usage, processing times, and more

## Architecture

The RAG agent follows this process:
1. User submits a query
2. The query is logged by Cylestio Monitor
3. Documents are retrieved from the vector store based on the query
4. The retrieval process metrics are logged
5. The LLM generates a response using the retrieved documents as context
6. The complete interaction including performance metrics is logged
7. The response is returned to the user

## Setup

### Prerequisites

- Python 3.12+
- [Anthropic API key](https://console.anthropic.com/)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   This will install all required packages including:
   - LangChain and related components
   - Anthropic API client
   - Chroma vector database
   - Cylestio Monitor SDK

3. Set up your API key:
   - Either edit the `.env` file with your Anthropic API key
   - Or set the environment variable:
     ```bash
     export ANTHROPIC_API_KEY=your-api-key
     ```

## Usage

Run the example:

```bash
python rag.py
```

The agent will:
1. Create or load sample documents
2. Initialize a retriever with these documents
3. Process a set of example queries
4. Log all interactions to the Cylestio Monitor database

## How Monitoring Works

The RAG agent is automatically monitored by the Cylestio Monitor SDK. Basic setup requires:

```python
from cylestio_monitor import enable_monitoring

# Initialize monitoring with your agent ID
enable_monitoring(agent_id="rag-agent")
```

For more detailed control including local JSON log files:

```python
from cylestio_monitor import enable_monitoring

# Initialize monitoring with an agent ID and specify a JSON log file path
log_file_path = os.path.join(os.getcwd(), "output", "cylestio_logs.json")
enable_monitoring(agent_id="rag-agent", log_file=log_file_path)
```

After this initialization, the SDK automatically tracks:
- LLM API calls
- Retrieval operations
- User queries and agent responses
- Error states and performance metrics

All monitored data is accessible through:
- The Cylestio dashboard or API
- Local SQLite database (default location in user's application data directory)
- Local JSON log file (if specified)

## Monitored Events

The RAG agent automatically logs the following events:
- **LLM requests**: Details of each call to the language model
- **Retrieval operations**: Document retrieval metrics
- **User interactions**: All user queries and agent responses
- **Performance metrics**: Processing times, token usage, etc.
- **Errors**: Any exceptions that occur during processing

## Customization

- Modify the example documents in the `_create_sample_documents` method
- Change the model in the agent initialization
- Adjust the retrieval parameters in the `_initialize_retriever` method
- Update the prompt template for specific use cases

## Extending

This example can be extended with:
- Custom document loaders
- Different embedding models
- More sophisticated retrieval mechanisms
- Integration with web search or other data sources
- Custom logging and monitoring for domain-specific metrics 