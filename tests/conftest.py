"""Pytest configuration file."""

import logging
from unittest.mock import MagicMock

import pytest


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
    return client
