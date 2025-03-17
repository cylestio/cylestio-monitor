"""Integration test for the relational database schema implementation.

This test verifies that the updated monitoring system correctly uses the relational
database schema while maintaining dual logging to JSON files.
"""

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from cylestio_monitor import enable_monitoring, disable_monitoring
from cylestio_monitor.db.database_manager import DatabaseManager
from cylestio_monitor.db.models import (
    Agent, Event, LLMCall, ToolCall, SecurityAlert, 
    Session as DBSession, Conversation
)
from cylestio_monitor.events_processor import log_event


class TestRelationalSchema:
    """Test class for the relational schema implementation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def db_path(self, temp_dir):
        """Create a test database path."""
        return os.path.join(temp_dir, "test_db.sqlite")

    @pytest.fixture
    def log_path(self, temp_dir):
        """Create a test log file path."""
        return os.path.join(temp_dir, "test_log.json")

    def test_relational_schema_and_dual_logging(self, temp_dir, db_path, log_path):
        """Test relational schema implementation with dual logging."""
        try:
            # Enable monitoring with our test paths
            enable_monitoring(
                agent_id="test_agent",
                config={
                    "db_path": db_path,
                    "log_file": log_path,
                    "sql_debug": True,
                    "development_mode": True
                }
            )

            # 1. Test basic event logging
            log_event("test_event", {"message": "Test message"}, "TEST", "info")
            
            # Wait a moment for async operations to complete
            time.sleep(0.1)
            
            # Verify event was written to the JSON file
            assert os.path.exists(log_path), "Log file was not created"
            with open(log_path, "r") as f:
                log_lines = f.readlines()
                assert len(log_lines) >= 1, "No events were logged to the JSON file"
                # Parse the JSON to verify content
                event_data = json.loads(log_lines[-1])
                assert event_data["event_type"] == "test_event", "Event type mismatch in JSON log"
                assert event_data["channel"] == "TEST", "Channel mismatch in JSON log"
            
            # Verify event was stored in the database
            db_manager = DatabaseManager()
            with db_manager.get_session() as session:
                events = session.query(Event).all()
                assert len(events) >= 1, "No events were stored in the database"
                # Find our test event
                test_event = next((e for e in events if e.event_type == "test_event"), None)
                assert test_event is not None, "Test event not found in database"
                assert test_event.channel == "test", "Channel mismatch in database (should be lowercase)"
            
            # 2. Test session tracking
            session_id = f"test_session_{datetime.now().timestamp()}"
            
            # Log events with session tracking
            log_event("session_start", {"session_id": session_id}, "TEST", "info")
            log_event("user_message", {
                "session_id": session_id,
                "message": "Hello, AI!"
            }, "TEST", "info", "incoming")
            
            # 3. Test LLM call logging
            log_event("llm_request", {
                "session_id": session_id,
                "provider": "test_provider",
                "model": "test_model",
                "messages": [{"role": "user", "content": "Hello, AI!"}],
                "tokens_prompt": 10
            }, "LLM", "info", "outgoing")
            
            log_event("llm_response", {
                "session_id": session_id,
                "provider": "test_provider",
                "model": "test_model",
                "completion": "Hello, human!",
                "tokens_completion": 5,
                "latency_ms": 100
            }, "LLM", "info", "incoming")
            
            # 4. Test tool call logging
            log_event("tool_call", {
                "session_id": session_id,
                "tool_name": "test_tool",
                "input": {"query": "test query"},
                "output": {"result": "test result"},
                "status": "success",
                "latency_ms": 50
            }, "TOOL", "info")
            
            # 5. Test security alert logging
            log_event("security_alert", {
                "session_id": session_id,
                "alert_type": "suspicious_input",
                "severity": "medium",
                "description": "Potentially suspicious input detected",
                "source": "input_filter"
            }, "SECURITY", "warning")
            
            # Wait for all events to be processed
            time.sleep(0.1)
            
            # Verify in database
            with db_manager.get_session() as session:
                # Verify session was created
                db_session = session.query(DBSession).filter(
                    DBSession.id == session_id
                ).first()
                assert db_session is not None, "Session not created in database"
                
                # Verify events are linked to the session
                session_events = session.query(Event).filter(
                    Event.session_id == db_session.id
                ).all()
                assert len(session_events) >= 5, "Not all session events were stored"
                
                # Verify LLM call was stored properly
                llm_event = session.query(Event).filter(
                    Event.event_type == "llm_request"
                ).first()
                assert llm_event is not None, "LLM request event not found"
                
                llm_call = session.query(LLMCall).filter(
                    LLMCall.event_id == llm_event.id
                ).first()
                assert llm_call is not None, "LLM call record not found"
                assert llm_call.provider == "test_provider", "LLM provider mismatch"
                assert llm_call.model == "test_model", "LLM model mismatch"
                
                # Verify tool call was stored properly
                tool_event = session.query(Event).filter(
                    Event.event_type == "tool_call"
                ).first()
                assert tool_event is not None, "Tool call event not found"
                
                tool_call = session.query(ToolCall).filter(
                    ToolCall.event_id == tool_event.id
                ).first()
                assert tool_call is not None, "Tool call record not found"
                assert tool_call.tool_name == "test_tool", "Tool name mismatch"
                assert tool_call.status == "success", "Tool status mismatch"
                
                # Verify security alert was stored properly
                security_event = session.query(Event).filter(
                    Event.event_type == "security_alert"
                ).first()
                assert security_event is not None, "Security alert event not found"
                
                security_alert = session.query(SecurityAlert).filter(
                    SecurityAlert.event_id == security_event.id
                ).first()
                assert security_alert is not None, "Security alert record not found"
                assert security_alert.severity == "medium", "Security severity mismatch"
            
            # 6. Test conversation tracking
            conversation_id = f"test_conversation_{datetime.now().timestamp()}"
            
            # Log events with conversation tracking
            log_event("conversation_start", {
                "session_id": session_id,
                "conversation_id": conversation_id
            }, "TEST", "info")
            
            log_event("user_message", {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "message": "Tell me about quantum physics"
            }, "TEST", "info", "incoming")
            
            # Wait for events to be processed
            time.sleep(0.1)
            
            # Verify conversation linking in database
            with db_manager.get_session() as session:
                conversation = session.query(Conversation).filter(
                    Conversation.conversation_id == conversation_id
                ).first()
                assert conversation is not None, "Conversation not created in database"
                
                # Verify the conversation is linked to the correct session
                assert conversation.session_id == db_session.id, "Conversation not linked to session"
                
                # Verify events are linked to the conversation
                conversation_events = session.query(Event).filter(
                    Event.conversation_id == conversation.id
                ).all()
                assert len(conversation_events) >= 2, "Not all conversation events were stored"
            
            # 7. Test error handling with transaction rollback
            try:
                # Create a direct engine and session to test manual transactions
                engine = create_engine(f"sqlite:///{db_path}")
                with Session(engine) as test_session, test_session.begin():
                    # Add an agent that already exists to trigger an error
                    duplicate_agent = Agent(agent_id="test_agent", name="Test Agent")
                    test_session.add(duplicate_agent)
                    test_session.flush()  # This should fail with an integrity error
                
                # If we get here, the duplicate insert didn't fail as expected
                assert False, "Transaction should have failed with integrity error"
            except Exception:
                # Expected exception, verify transaction was rolled back
                with Session(engine) as verify_session:
                    # Check that we only have one agent with this ID
                    agent_count = verify_session.query(Agent).filter(
                        Agent.agent_id == "test_agent"
                    ).count()
                    assert agent_count == 1, "Transaction wasn't rolled back properly"
            
            # Disable monitoring to clean up
            disable_monitoring()
            
            print("All relational schema tests passed successfully!")
            
        except Exception as e:
            # Ensure monitoring is disabled even if tests fail
            disable_monitoring()
            raise e

    def test_event_relationships(self):
        """Test that events are properly related to sessions and conversations."""
        session_id = "test_session"
        conv_id = "test_conversation"
        
        # Enable monitoring
        enable_monitoring({
            "agent_id": "test_agent",
            "db_path": self.db_path,
            "log_file": self.log_path
        })
        
        # Log a session start event
        log_event(
            "session_start",
            {"session_id": session_id},
            session_id=session_id
        )
        
        # Log a message in the conversation
        log_event(
            "user_message",
            {
                "session_id": session_id,
                "conversation_id": conv_id,
                "content": "Hello, world!"
            },
            session_id=session_id,
            conversation_id=conv_id
        )
        
        # Query the database to check relationships
        DBSession = get_model("Session")
        Event = get_model("Event")
        
        with get_db_session() as session:
            # Get the session
            db_session = session.query(DBSession).filter(
                DBSession.id == session_id
            ).first()
            
            # Check that events are linked to the session
            events = session.query(Event).filter(
                Event.session_id == session_id
            ).all()
            
            # Assert that we found events
            self.assertTrue(len(events) > 0)
            
            # Check that at least one event has the conversation ID
            conv_events = [e for e in events if e.conversation_id == conv_id]
            self.assertTrue(len(conv_events) > 0)


def test_schema_migration():
    """Test schema migration and update functionality."""
    try:
        # Create a temporary directory for the test
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "migration_test.db")
        
        # Initialize the database manager
        db_manager = DatabaseManager()
        db_result = db_manager.initialize_database(Path(db_path))
        assert db_result["success"], f"Failed to initialize database: {db_result.get('error')}"
        
        # Verify the schema is correct
        verify_result = db_manager.verify_schema()
        assert verify_result["success"], f"Schema verification failed: {verify_result.get('error')}"
        assert verify_result["matches"], "Initial schema doesn't match models"
        
        # Test schema update functionality (should be a no-op since schema is correct)
        update_result = db_manager.update_schema()
        assert update_result["success"], f"Schema update failed: {update_result.get('error')}"
        assert not update_result["tables_added"], "No tables should have been added"
        assert not update_result["tables_modified"], "No tables should have been modified"
        
        print("Schema migration test passed successfully!")
        
    finally:
        # Clean up
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run the tests directly when the script is executed
    test_instance = TestRelationalSchema()
    test_instance.test_relational_schema_and_dual_logging(
        tempfile.mkdtemp(),
        os.path.join(tempfile.mkdtemp(), "test_db.sqlite"),
        os.path.join(tempfile.mkdtemp(), "test_log.json")
    )
    test_schema_migration() 