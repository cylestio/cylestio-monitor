"""Pytest configuration file."""

import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from cylestio_monitor.db.db_manager import DBManager


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
def mock_db_manager():
    """Fixture that provides a mocked DBManager instance."""
    with patch("cylestio_monitor.db.db_manager.DBManager._get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Create a DBManager instance with mocked session
        db_manager = DBManager()
        
        # Mock the _get_agent method to return a mock agent
        mock_agent = MagicMock()
        mock_agent.id = 123
        db_manager._get_agent = MagicMock(return_value=mock_agent)
        
        # Add helper method for tests that call create_agent
        db_manager.create_agent = MagicMock(return_value="test_agent")
        
        return db_manager


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
def mock_session():
    """Fixture that provides a mocked SQLAlchemy session."""
    session = MagicMock()
    session.query = MagicMock(return_value=session)
    session.filter = MagicMock(return_value=session)
    session.all = MagicMock(return_value=[])
    session.first = MagicMock(return_value=None)
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_engine():
    """Fixture that provides a mocked SQLAlchemy engine."""
    engine = MagicMock()
    engine.execute = MagicMock()
    engine.dispose = MagicMock()
    return engine


@pytest.fixture
def mock_platformdirs():
    """Mock platformdirs to use a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(temp_dir, exist_ok=True)
        with patch("platformdirs.user_data_dir", return_value=temp_dir):
            yield temp_dir
