"""LangChain RAG (Retrieval Augmented Generation) agent with Cylestio monitoring.

This example demonstrates a RAG agent using LangChain with:
- Anthropic Claude as the LLM 
- Document retrieval from an embedded vector store
- Chat history support for conversational retrieval
- Cylestio monitoring integration to track all retrieval and generation operations
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# For state management in the conversational chain
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Import Cylestio Monitor for automatic monitoring
# Install via: pip install cylestio-monitor
from cylestio_monitor import start_monitoring

# Create output directories if they don't exist
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

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
    env_vars = {}
    
    # Check for Anthropic API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        env_vars = load_env_file()
        anthropic_key = env_vars.get("ANTHROPIC_API_KEY")
    
    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY not found in environment or .env file.")
        print("Please either:")
        print("1. Set it in your environment with: export ANTHROPIC_API_KEY='your-api-key'")
        print("2. Add it to your .env file as: ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)
    
    return anthropic_key

class InMemoryHistory(BaseChatMessageHistory):
    """Simple in-memory chat message history storage."""
    
    def __init__(self):
        self._messages = []
    
    def add_user_message(self, message: str) -> None:
        self._messages.append(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        self._messages.append(AIMessage(content=message))
    
    def clear(self) -> None:
        self._messages = []
    
    @property
    def messages(self) -> List:
        return self._messages
    
    @messages.setter
    def messages(self, messages: List) -> None:
        self._messages = messages

class MonitoredRAGAgent:
    """A monitored RAG agent implementation using LangChain and Anthropic with chat history."""
    
    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        """Initialize the RAG agent with the specified model.
        
        Args:
            model_name: The Anthropic model to use
        """
        # Enable monitoring with the agent ID - this is all that's needed for monitoring
        # Cylestio Monitor will automatically detect and patch:
        # 1. LangChain components (through framework detection)
        # 2. The underlying Anthropic client (through auto-patching)
        log_file_path = os.path.join(os.getcwd(), "output", "cylestio_logs.json")
        start_monitoring(agent_id="rag-agent", config={"log_file": "output/rag_monitoring.json"})
        
        # Validate environment variables
        anthropic_key = validate_environment()
        
        # Initialize the LLM
        # Note: The underlying Anthropic client is automatically patched by Cylestio Monitor
        self.llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=anthropic_key,
            temperature=0.7
        )
        
        # Create sample documents if none exist
        self._create_sample_documents()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Initialize embeddings
        self.embeddings = FakeEmbeddings(size=1536)
        
        # Initialize the retriever
        self._initialize_retriever()
        
        # Initialize the chat histories dictionary
        self.chat_histories = {}
        
        # Set up the conversational RAG chain
        self._setup_rag_chain()
    
    def _create_sample_documents(self):
        """Create sample documents for the RAG agent if they don't exist."""
        sample_docs_file = "data/sample_docs.json"
        
        if not os.path.exists(sample_docs_file):
            # Create sample documents
            docs = [
                Document(
                    page_content="Cylestio is a comprehensive security and monitoring solution for AI agents. "
                               "It provides advanced features for tracking LLM API calls, agent actions, and "
                               "potential security vulnerabilities.",
                    metadata={"source": "cylestio_info.txt", "topic": "security"}
                ),
                Document(
                    page_content="The Cylestio Monitor SDK enables organizations to log and track all AI agent "
                               "operations, ensuring compliance with security policies and helping to detect "
                               "potential unauthorized access or misuse of AI systems.",
                    metadata={"source": "cylestio_monitor.txt", "topic": "monitoring"}
                ),
                Document(
                    page_content="RAG (Retrieval Augmented Generation) is a technique that combines retrieval-based "
                               "methods with generative AI to enhance the quality and factual accuracy of generated "
                               "content. It retrieves relevant documents from a knowledge base and uses them as "
                               "additional context for the LLM.",
                    metadata={"source": "rag_overview.txt", "topic": "rag"}
                ),
                Document(
                    page_content="LangChain is a framework for developing applications powered by language models. "
                               "It provides tools and components for creating complex AI workflows, including "
                               "agents, chains, retrievers, and more.",
                    metadata={"source": "langchain_overview.txt", "topic": "langchain"}
                ),
                Document(
                    page_content="When working with RAG systems, it's important to consider retrieval quality, "
                               "context length, and how the retrieved information is integrated into prompts. "
                               "These factors directly impact the quality of generated responses.",
                    metadata={"source": "rag_best_practices.txt", "topic": "rag"}
                ),
                Document(
                    page_content="Conversational RAG systems maintain chat history and context across multiple "
                               "interactions. This allows the system to provide more relevant and personalized "
                               "responses based on the full conversation context.",
                    metadata={"source": "conversational_rag.txt", "topic": "rag"}
                ),
                Document(
                    page_content="Monitoring AI systems is crucial for ensuring their safe and effective operation. "
                               "Key metrics to track include token usage, response latency, retrieval quality, and "
                               "response appropriateness.",
                    metadata={"source": "monitoring_best_practices.txt", "topic": "monitoring"}
                ),
                Document(
                    page_content="Security considerations for AI systems include preventing prompt injection, "
                               "avoiding data leakage, ensuring proper authentication and authorization, and "
                               "implementing rate limiting to prevent abuse.",
                    metadata={"source": "ai_security.txt", "topic": "security"}
                ),
            ]
            
            # Save sample documents to JSON
            with open(sample_docs_file, "w") as f:
                json.dump([{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs], f, indent=2)
            
            self.documents = docs
            
            print(f"Created {len(docs)} sample documents")
        else:
            # Load existing documents
            with open(sample_docs_file, "r") as f:
                loaded_docs = json.load(f)
                self.documents = [
                    Document(page_content=doc["page_content"], metadata=doc["metadata"])
                    for doc in loaded_docs
                ]
            
            print(f"Loaded {len(self.documents)} existing documents")
    
    def _initialize_retriever(self):
        """Initialize the retriever with documents."""
        # Split documents
        splits = self.text_splitter.split_documents(self.documents)
        
        # Create vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="data/chroma_db"
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        
        print(f"Initialized retriever with {len(splits)} document chunks")
    
    def _setup_rag_chain(self):
        """Set up the conversational RAG chain."""
        # Create a system message for the RAG chain
        system_message = """You are an AI assistant for answering questions based on the provided documents. 
        Use the retrieved context to formulate your answers. If you don't know the answer based on the context, 
        say that you don't know. Always maintain a helpful, informative tone.
        
        For follow-up questions, use the conversation history to provide context-aware responses.
        """
        
        # Create the conversational RAG prompt
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
                ("human", "Context: {context}"),
            ]
        )
        
        # Create retrieval function that incorporates chat history for context
        def _get_context(inputs):
            chat_history = inputs.get("chat_history", [])
            
            question = inputs["question"]
            context_docs = []
            
            # Execute retrieval
            retrieved_docs = self.retriever.invoke(question)
            
            # Process the retrieved documents
            if retrieved_docs:
                context_docs = retrieved_docs
            
            # Format context string
            formatted_context = "\n\n".join([doc.page_content for doc in context_docs])
            return formatted_context
        
        # Base chain with retrieval
        _retrieval_chain = RunnablePassthrough.assign(
            context=RunnableLambda(_get_context)
        )
        
        # Combine with prompt and LLM
        _response_chain = self.prompt | self.llm | StrOutputParser()
        
        # Build the chain
        self.chain = _retrieval_chain | _response_chain
        
        # Wrap with conversation history
        self.conversational_chain = RunnableWithMessageHistory(
            self.chain,
            lambda session_id: self._get_chat_history(session_id),
            input_messages_key="question",
            history_messages_key="chat_history",
        )
    
    def _get_chat_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create a chat history for the given session ID."""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = InMemoryHistory()
        return self.chat_histories[session_id]
    
    def query(self, question: str, session_id: str = "default") -> str:
        """Process a user query and return the RAG agent's response.
        
        Args:
            question: The user's input question
            session_id: Unique identifier for the conversation
            
        Returns:
            The RAG agent's response
        """
        try:
            # Process the query with the conversational chain
            response = self.conversational_chain.invoke(
                {"question": question},
                config={"configurable": {"session_id": session_id}}
            )
            
            return response
            
        except Exception as e:
            print(f"Error in RAG query: {str(e)}")
            raise
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        This is a simple approximation. For production use, consider using a tokenizer.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple approximation: 4 characters per token on average
        return len(str(text)) // 4

def main():
    """Run an example conversation with the monitored RAG agent."""
    
    # Create RAG agent
    print("Initializing the RAG agent with monitoring...")
    rag_agent = MonitoredRAGAgent()
    
    # Example conversations
    conversations = [
        {
            "session_id": "session-1",
            "queries": [
                "What is Cylestio Monitor?",
                "What key features does it provide?",
                "How does it ensure security?",
            ]
        },
        {
            "session_id": "session-2",
            "queries": [
                "Explain RAG in simple terms",
                "Why is retrieval important in RAG systems?",
                "What are some best practices for RAG implementations?",
            ]
        },
        {
            "session_id": "session-3",
            "queries": [
                "Tell me about LangChain",
                "How does LangChain support RAG applications?",
                "What monitoring capabilities can be integrated with LangChain?",
            ]
        }
    ]
    
    # Process conversations
    for conversation in conversations:
        session_id = conversation["session_id"]
        queries = conversation["queries"]
        
        print(f"\n\n{'=' * 80}")
        print(f"Starting conversation: {session_id}")
        print(f"{'=' * 80}")
        
        for i, query in enumerate(queries):
            print(f"\n[Turn {i+1}] User: {query}")
            response = rag_agent.query(query, session_id=session_id)
            print(f"[Turn {i+1}] Assistant: {response}")
    
    print("\nMonitoring logs saved to the database and to the JSON file at: output/cylestio_logs.json")

if __name__ == "__main__":
    main() 