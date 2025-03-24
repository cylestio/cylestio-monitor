"""Pytest configuration file."""

import logging
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from cylestio_monitor.api_client import ApiClient


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


@pytest.fixture(autouse=True)
def mock_db_utils():
    """Mock db_utils for tests since it's been removed from the project."""
    mock = MagicMock()
    mock.log_to_db = MagicMock(return_value=None)
    
    with patch("cylestio_monitor.db.db_manager.DBManager", MagicMock()):
        with patch.dict("sys.modules", {"cylestio_monitor.db": MagicMock(), 
                                        "cylestio_monitor.db.db_manager": MagicMock(),
                                        "cylestio_monitor.db.utils": mock}):
            yield mock
