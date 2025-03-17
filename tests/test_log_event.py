"""Unit tests for the DBManager's log_event function using mocking.

This module focuses on testing only the log_event functionality with complete 
mocking to avoid SQLAlchemy initialization issues.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestDBManagerLogEvent:
    """Test for DBManager's log_event function."""

    @patch("cylestio_monitor.db.db_manager.Agent")
    @patch("cylestio_monitor.db.db_manager.Event")
    def test_log_event_basic(self, mock_event, mock_agent):
        """Test that log_event correctly creates and returns an event."""
        # Prepare mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.id = 123
        mock_agent.get_or_create.return_value = mock_agent_instance
        
        mock_event_instance = MagicMock()
        mock_event_instance.id = 456
        mock_event.create_event.return_value = mock_event_instance
        
        # Setup session mock
        mock_session = MagicMock()
        
        # Import the DBManager class with the session mocked
        with patch('cylestio_monitor.db.db_manager.DBManager._get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            from cylestio_monitor.db.db_manager import DBManager
            
            # Create instance and test
            db_manager = DBManager()
            result = db_manager.log_event(
                agent_id="test-agent", 
                event_type="test-event", 
                data={"message": "hello"},
                channel="TEST",
                level="info"
            )
            
            # Assertions
            assert result == 456
            mock_agent.get_or_create.assert_called_once_with(mock_session, "test-agent")
            mock_session.flush.assert_called_once()
            mock_event.create_event.assert_called_once() 