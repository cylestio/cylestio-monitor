"""Pytest configuration file."""

import logging
import os
import sys
import types
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from cylestio_monitor.api_client import ApiClient


@pytest.fixture(scope="session", autouse=True)
def setup_mock_imports():
    """Set up mock imports for missing modules."""
    # Add langchain mocks
    if 'langchain' not in sys.modules:
        mock_langchain = types.ModuleType('langchain')
        mock_callbacks = types.ModuleType('langchain.callbacks')
        mock_base = types.ModuleType('langchain.callbacks.base')
        
        class MockBaseCallbackHandler:
            pass
        
        mock_base.BaseCallbackHandler = MockBaseCallbackHandler
        mock_callbacks.base = mock_base
        mock_langchain.callbacks = mock_callbacks
        
        sys.modules['langchain'] = mock_langchain
        sys.modules['langchain.callbacks'] = mock_callbacks
        sys.modules['langchain.callbacks.base'] = mock_base
    
    if 'langchain_core' not in sys.modules:
        mock_langchain_core = types.ModuleType('langchain_core')
        mock_callbacks = types.ModuleType('langchain_core.callbacks')
        mock_base = types.ModuleType('langchain_core.callbacks.base')
        
        class MockBaseCallbackHandler:
            pass
        
        mock_base.BaseCallbackHandler = MockBaseCallbackHandler
        mock_callbacks.base = mock_base
        mock_langchain_core.callbacks = mock_callbacks
        
        sys.modules['langchain_core'] = mock_langchain_core
        sys.modules['langchain_core.callbacks'] = mock_callbacks
        sys.modules['langchain_core.callbacks.base'] = mock_base
    
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
