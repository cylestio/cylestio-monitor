"""Pytest configuration file."""

import logging
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_mock_imports():
    """Set up simplified mock imports for missing modules."""
    # Only create minimal mocks for modules that are absolutely essential
    if "langchain" not in sys.modules:
        # For MVP, we only need a basic mock of langchain
        sys.modules["langchain"] = MagicMock()

    if "langchain_core" not in sys.modules:
        # For MVP, we only need a basic mock of langchain_core
        sys.modules["langchain_core"] = MagicMock()

    yield


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
