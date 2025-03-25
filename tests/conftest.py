"""Pytest configuration file."""

import logging
import os
import sys
import types
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Delay this import to give opportunity to set up sys.modules mock first
# from cylestio_monitor.api_client import ApiClient


@pytest.fixture(scope="session", autouse=True)
def setup_mock_imports():
    """Set up mock imports for missing modules."""
    # Set up mocks before any real imports happen
    
    # Mock DB-related modules that might be imported indirectly
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlite3'] = MagicMock()
    
    # Add more comprehensive langchain mocks
    if 'langchain' not in sys.modules:
        mock_langchain = types.ModuleType('langchain')
        
        # Create submodules
        mock_callbacks = types.ModuleType('langchain.callbacks')
        mock_base = types.ModuleType('langchain.callbacks.base')
        mock_manager = types.ModuleType('langchain.callbacks.manager')
        mock_chains = types.ModuleType('langchain.chains')
        mock_chain_base = types.ModuleType('langchain.chains.base')
        mock_llms = types.ModuleType('langchain.llms')
        mock_llm_base = types.ModuleType('langchain.llms.base')
        mock_chat_models = types.ModuleType('langchain.chat_models')
        mock_schema = types.ModuleType('langchain.schema')

        # Create mock classes
        class MockBaseCallbackHandler:
            pass
            
        class MockCallbackManager:
            def __init__(self, *args, **kwargs):
                pass
            
        class MockChain:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockBaseLLM:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockBaseChatModel:
            def __init__(self, *args, **kwargs):
                pass
        
        # Set up the module structure
        mock_base.BaseCallbackHandler = MockBaseCallbackHandler
        mock_callbacks.base = mock_base
        
        mock_manager.CallbackManager = MockCallbackManager
        mock_callbacks.manager = mock_manager
        
        mock_chain_base.Chain = MockChain
        mock_chains.base = mock_chain_base
        
        mock_llm_base.BaseLLM = MockBaseLLM
        mock_llms.base = mock_llm_base
        
        mock_chat_models.base = types.ModuleType('langchain.chat_models.base')
        mock_chat_models.base.BaseChatModel = MockBaseChatModel
        
        # Assign to main module
        mock_langchain.callbacks = mock_callbacks
        mock_langchain.chains = mock_chains
        mock_langchain.llms = mock_llms
        mock_langchain.chat_models = mock_chat_models
        mock_langchain.schema = mock_schema
        
        # Register in sys.modules
        sys.modules['langchain'] = mock_langchain
        sys.modules['langchain.callbacks'] = mock_callbacks
        sys.modules['langchain.callbacks.base'] = mock_base
        sys.modules['langchain.callbacks.manager'] = mock_manager
        sys.modules['langchain.chains'] = mock_chains
        sys.modules['langchain.chains.base'] = mock_chain_base
        sys.modules['langchain.llms'] = mock_llms
        sys.modules['langchain.llms.base'] = mock_llm_base
        sys.modules['langchain.chat_models'] = mock_chat_models
        sys.modules['langchain.chat_models.base'] = mock_chat_models.base
        sys.modules['langchain.schema'] = mock_schema
    
    # Similarly comprehensive mocks for langchain_core
    if 'langchain_core' not in sys.modules:
        mock_langchain_core = types.ModuleType('langchain_core')
        
        # Create submodules
        mock_callbacks = types.ModuleType('langchain_core.callbacks')
        mock_base = types.ModuleType('langchain_core.callbacks.base')
        mock_manager = types.ModuleType('langchain_core.callbacks.manager')
        mock_messages = types.ModuleType('langchain_core.messages')
        mock_outputs = types.ModuleType('langchain_core.outputs')
        mock_runnables = types.ModuleType('langchain_core.runnables')
        mock_prompts = types.ModuleType('langchain_core.prompts')
        mock_chains = types.ModuleType('langchain_core.chains')
        mock_language_models = types.ModuleType('langchain_core.language_models')
        mock_llms = types.ModuleType('langchain_core.language_models.llms')
        mock_chat_models = types.ModuleType('langchain_core.language_models.chat_models')
        mock_globals = types.ModuleType('langchain_core.globals')
        
        # Create mock classes
        class MockBaseCallbackHandler:
            pass
            
        class MockCallbackManager:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockBaseMessage:
            def __init__(self, content):
                self.content = content
                
        class MockLLMResult:
            pass
            
        class MockRunnable:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockChain:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockBaseLLM:
            def __init__(self, *args, **kwargs):
                pass
                
        class MockBaseChatModel:
            def __init__(self, *args, **kwargs):
                pass
        
        # Set up the module structure
        mock_base.BaseCallbackHandler = MockBaseCallbackHandler
        mock_callbacks.base = mock_base
        
        mock_manager.CallbackManager = MockCallbackManager
        mock_callbacks.manager = mock_manager
        
        mock_messages.BaseMessage = MockBaseMessage
        mock_outputs.LLMResult = MockLLMResult
        
        mock_runnables.base = types.ModuleType('langchain_core.runnables.base')
        mock_runnables.base.Runnable = MockRunnable
        
        mock_chains.Chain = MockChain
        
        mock_llms.BaseLLM = MockBaseLLM
        mock_language_models.llms = mock_llms
        
        mock_chat_models.BaseChatModel = MockBaseChatModel
        mock_language_models.chat_models = mock_chat_models
        
        # Mocks for global callback manager
        mock_globals.get_callback_manager = MagicMock(return_value=MockCallbackManager())
        mock_globals.set_callback_manager = MagicMock()
        
        # Assign to main module
        mock_langchain_core.callbacks = mock_callbacks
        mock_langchain_core.messages = mock_messages
        mock_langchain_core.outputs = mock_outputs
        mock_langchain_core.runnables = mock_runnables
        mock_langchain_core.prompts = mock_prompts
        mock_langchain_core.chains = mock_chains
        mock_langchain_core.language_models = mock_language_models
        mock_langchain_core.globals = mock_globals
        
        # Register in sys.modules
        sys.modules['langchain_core'] = mock_langchain_core
        sys.modules['langchain_core.callbacks'] = mock_callbacks
        sys.modules['langchain_core.callbacks.base'] = mock_base
        sys.modules['langchain_core.callbacks.manager'] = mock_manager
        sys.modules['langchain_core.messages'] = mock_messages
        sys.modules['langchain_core.outputs'] = mock_outputs
        sys.modules['langchain_core.runnables'] = mock_runnables
        sys.modules['langchain_core.runnables.base'] = mock_runnables.base
        sys.modules['langchain_core.prompts'] = mock_prompts
        sys.modules['langchain_core.chains'] = mock_chains
        sys.modules['langchain_core.language_models'] = mock_language_models
        sys.modules['langchain_core.language_models.llms'] = mock_llms
        sys.modules['langchain_core.language_models.chat_models'] = mock_chat_models
        sys.modules['langchain_core.globals'] = mock_globals
    
    # Now we can safely import without dependency issues
    yield
    
    # No cleanup needed


@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging during tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    client.__class__.__module__ = "anthropic"
    client.__class__.__name__ = "Anthropic"
    client.messages.create = MagicMock()
    client.messages.create.__name__ = "create"
    client.messages.create.__annotations__ = {}
    return client


@pytest.fixture
def mock_api_client():
    """Fixture that provides a mocked ApiClient instance."""
    # Import here after mocks are set up
    from cylestio_monitor.api_client import ApiClient
    
    client = MagicMock(spec=ApiClient)
    client.endpoint = "https://example.com/api/events"
    client.send_event = MagicMock(return_value=True)

    with patch("cylestio_monitor.api_client.get_api_client", return_value=client):
        yield client


@pytest.fixture
def mock_logger():
    """Fixture that provides a mocked logger instance."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.log = MagicMock()
    return logger


@pytest.fixture
def mock_platformdirs():
    """Mock platformdirs to use a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(temp_dir, exist_ok=True)
        with patch("platformdirs.user_data_dir", return_value=temp_dir):
            yield temp_dir


@pytest.fixture
def mock_requests():
    """Mock requests library for API client tests."""
    with patch("cylestio_monitor.api_client.requests") as mock_requests:
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = "Success"

        # Setup the mock post method
        mock_requests.post.return_value = mock_response

        yield mock_requests
