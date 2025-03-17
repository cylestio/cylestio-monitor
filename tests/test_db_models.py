"""Tests for the SQLAlchemy models in the Cylestio Monitor database.

This module contains tests for all the SQLAlchemy models defined in
cylestio_monitor.db.models, ensuring they behave as expected.
"""
import datetime
import unittest
from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cylestio_monitor.db.models import (
    Base, Agent, Session as DbSession, Conversation, Event, EventType,
    EventLevel, EventChannel, EventDirection, LLMCall, ToolCall,
    EventSecurity, AlertLevel, SecurityAlert, AlertSeverity, PerformanceMetric
)


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def create_tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, create_tables):
    """Create a database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


class TestAgent:
    """Tests for the Agent model."""

    def test_create_agent(self, db_session):
        """Test creating an agent."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            description="A test agent",
            metadata={"framework": "langchain", "version": "1.0.0"}
        )
        db_session.add(agent)
        db_session.commit()

        # Query the agent back from the database
        queried_agent = db_session.query(Agent).filter_by(agent_id="test-agent").first()
        assert queried_agent is not None
        assert queried_agent.agent_id == "test-agent"
        assert queried_agent.name == "Test Agent"
        assert queried_agent.description == "A test agent"
        assert queried_agent.metadata["framework"] == "langchain"
        assert queried_agent.metadata["version"] == "1.0.0"

    def test_get_or_create_agent(self, db_session):
        """Test get_or_create functionality."""
        # Create a new agent
        agent1 = Agent.get_or_create(db_session, "test-agent", name="Test Agent")
        db_session.commit()
        
        # Get the same agent
        agent2 = Agent.get_or_create(db_session, "test-agent", description="Updated description")
        db_session.commit()
        
        # Verify
        assert agent1.id == agent2.id
        assert agent2.description == "Updated description"
        
        # Query to confirm
        agents = db_session.query(Agent).filter_by(agent_id="test-agent").all()
        assert len(agents) == 1
        assert agents[0].name == "Test Agent"
        assert agents[0].description == "Updated description"

    def test_update_last_seen(self, db_session):
        """Test updating the last_seen timestamp."""
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        # Record the last_seen time
        initial_last_seen = agent.last_seen
        
        # Wait a small amount of time
        import time
        time.sleep(0.01)
        
        # Update last_seen
        agent.update_last_seen()
        db_session.commit()
        
        # Query the agent again
        updated_agent = db_session.query(Agent).filter_by(agent_id="test-agent").first()
        assert updated_agent.last_seen > initial_last_seen


class TestSession:
    """Tests for the Session model."""

    def test_create_session(self, db_session):
        """Test creating a session."""
        # Create an agent first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        # Create a session for the agent
        session = DbSession(
            agent_id=agent.id,
            metadata={"client_info": "test-client"}
        )
        db_session.add(session)
        db_session.commit()
        
        # Query the session back
        queried_session = db_session.query(DbSession).filter_by(agent_id=agent.id).first()
        assert queried_session is not None
        assert queried_session.agent_id == agent.id
        assert queried_session.is_active == True
        assert queried_session.metadata["client_info"] == "test-client"

    def test_end_session(self, db_session):
        """Test ending a session."""
        # Create an agent and session
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        session = DbSession(agent_id=agent.id)
        db_session.add(session)
        db_session.commit()
        
        # End the session
        session.end()
        db_session.commit()
        
        # Query the session back
        queried_session = db_session.query(DbSession).filter_by(agent_id=agent.id).first()
        assert queried_session.is_active == False
        assert queried_session.end_time is not None
        assert queried_session.duration is not None


class TestConversation:
    """Tests for the Conversation model."""

    def test_create_conversation(self, db_session):
        """Test creating a conversation."""
        # Create agent and session first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        session = DbSession(agent_id=agent.id)
        db_session.add(session)
        db_session.commit()
        
        # Create a conversation
        conversation = Conversation(
            session_id=session.id,
            metadata={"user_id": "test-user"}
        )
        db_session.add(conversation)
        db_session.commit()
        
        # Query the conversation back
        queried_conv = db_session.query(Conversation).filter_by(session_id=session.id).first()
        assert queried_conv is not None
        assert queried_conv.session_id == session.id
        assert queried_conv.is_active == True
        assert queried_conv.metadata["user_id"] == "test-user"

    def test_end_conversation(self, db_session):
        """Test ending a conversation."""
        # Create agent, session, and conversation
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        session = DbSession(agent_id=agent.id)
        db_session.add(session)
        db_session.commit()
        
        conversation = Conversation(session_id=session.id)
        db_session.add(conversation)
        db_session.commit()
        
        # End the conversation
        conversation.end()
        db_session.commit()
        
        # Query the conversation back
        queried_conv = db_session.query(Conversation).filter_by(session_id=session.id).first()
        assert queried_conv.is_active == False
        assert queried_conv.end_time is not None
        assert queried_conv.duration is not None


class TestEvent:
    """Tests for the Event model."""

    def test_create_event(self, db_session):
        """Test creating an event."""
        # Create agent first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        # Create an event
        event = Event(
            agent_id=agent.id,
            event_type=EventType.LLM_REQUEST,
            channel=EventChannel.LLM,
            level=EventLevel.INFO,
            direction=EventDirection.OUTGOING,
            data={"message": "Hello, world!"}
        )
        db_session.add(event)
        db_session.commit()
        
        # Query the event back
        queried_event = db_session.query(Event).filter_by(agent_id=agent.id).first()
        assert queried_event is not None
        assert queried_event.event_type == EventType.LLM_REQUEST.value
        assert queried_event.channel == EventChannel.LLM.value
        assert queried_event.level == EventLevel.INFO.value
        assert queried_event.direction == EventDirection.OUTGOING.value
        assert queried_event.data["message"] == "Hello, world!"


class TestLLMCall:
    """Tests for the LLMCall model."""

    def test_create_llm_call(self, db_session):
        """Test creating an LLM call."""
        # Create agent and event first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        event = Event(
            agent_id=agent.id,
            event_type=EventType.LLM_REQUEST,
            channel=EventChannel.LLM,
            level=EventLevel.INFO
        )
        db_session.add(event)
        db_session.commit()
        
        # Create an LLM call
        llm_call = LLMCall(
            event_id=event.id,
            model="gpt-4",
            prompt="What is the capital of France?",
            response="The capital of France is Paris.",
            tokens_in=10,
            tokens_out=7,
            duration_ms=500,
            is_stream=False,
            temperature=0.7,
            cost=0.01
        )
        db_session.add(llm_call)
        db_session.commit()
        
        # Query the LLM call back
        queried_call = db_session.query(LLMCall).filter_by(event_id=event.id).first()
        assert queried_call is not None
        assert queried_call.model == "gpt-4"
        assert queried_call.prompt == "What is the capital of France?"
        assert queried_call.response == "The capital of France is Paris."
        assert queried_call.tokens_in == 10
        assert queried_call.tokens_out == 7
        assert queried_call.duration_ms == 500
        assert queried_call.is_stream == False
        assert queried_call.temperature == 0.7
        assert queried_call.cost == 0.01
        assert queried_call.total_tokens == 17


class TestToolCall:
    """Tests for the ToolCall model."""

    def test_create_tool_call(self, db_session):
        """Test creating a tool call."""
        # Create agent and event first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        event = Event(
            agent_id=agent.id,
            event_type=EventType.TOOL_CALL,
            channel=EventChannel.TOOL,
            level=EventLevel.INFO
        )
        db_session.add(event)
        db_session.commit()
        
        # Create a tool call
        tool_call = ToolCall(
            event_id=event.id,
            tool_name="calculator",
            input_params={"a": 5, "b": 3, "operation": "add"},
            output_result={"result": 8},
            success=True,
            duration_ms=20,
            blocking=True
        )
        db_session.add(tool_call)
        db_session.commit()
        
        # Query the tool call back
        queried_call = db_session.query(ToolCall).filter_by(event_id=event.id).first()
        assert queried_call is not None
        assert queried_call.tool_name == "calculator"
        assert queried_call.input_params["a"] == 5
        assert queried_call.input_params["operation"] == "add"
        assert queried_call.output_result["result"] == 8
        assert queried_call.success == True
        assert queried_call.error_message is None
        assert queried_call.duration_ms == 20
        assert queried_call.blocking == True
        assert queried_call.has_error == False


class TestEventSecurity:
    """Tests for the EventSecurity model."""

    def test_create_event_security(self, db_session):
        """Test creating an event security record."""
        # Create agent and event first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        event = Event(
            agent_id=agent.id,
            event_type=EventType.LLM_REQUEST,
            channel=EventChannel.LLM,
            level=EventLevel.WARNING
        )
        db_session.add(event)
        db_session.commit()
        
        # Create an event security record
        security = EventSecurity(
            event_id=event.id,
            alert_level=AlertLevel.SUSPICIOUS,
            matched_terms=["sudo", "rm", "-rf"],
            reason="Potential harmful command",
            source_field="prompt"
        )
        db_session.add(security)
        db_session.commit()
        
        # Query the security record back
        queried_security = db_session.query(EventSecurity).filter_by(event_id=event.id).first()
        assert queried_security is not None
        assert queried_security.alert_level == AlertLevel.SUSPICIOUS.value
        assert "sudo" in queried_security.matched_terms
        assert "-rf" in queried_security.matched_terms
        assert queried_security.reason == "Potential harmful command"
        assert queried_security.source_field == "prompt"
        assert queried_security.is_suspicious == True
        assert queried_security.is_dangerous == False


class TestSecurityAlert:
    """Tests for the SecurityAlert model."""

    def test_create_security_alert(self, db_session):
        """Test creating a security alert."""
        # Create agent and event first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        event = Event(
            agent_id=agent.id,
            event_type=EventType.SECURITY_ALERT,
            channel=EventChannel.SYSTEM,
            level=EventLevel.ERROR
        )
        db_session.add(event)
        db_session.commit()
        
        # Create a security alert
        alert = SecurityAlert(
            event_id=event.id,
            alert_type="command_injection",
            severity=AlertSeverity.HIGH,
            description="Attempted to inject system commands",
            matched_terms=["sudo", "rm", "-rf"],
            action_taken="blocked"
        )
        db_session.add(alert)
        db_session.commit()
        
        # Query the alert back
        queried_alert = db_session.query(SecurityAlert).filter_by(event_id=event.id).first()
        assert queried_alert is not None
        assert queried_alert.alert_type == "command_injection"
        assert queried_alert.severity == AlertSeverity.HIGH.value
        assert queried_alert.description == "Attempted to inject system commands"
        assert "rm" in queried_alert.matched_terms
        assert queried_alert.action_taken == "blocked"
        assert queried_alert.is_high == True
        assert queried_alert.is_critical == False


class TestPerformanceMetric:
    """Tests for the PerformanceMetric model."""

    def test_create_performance_metric(self, db_session):
        """Test creating a performance metric."""
        # Create agent and event first
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        event = Event(
            agent_id=agent.id,
            event_type=EventType.PERFORMANCE_METRIC,
            channel=EventChannel.SYSTEM,
            level=EventLevel.INFO
        )
        db_session.add(event)
        db_session.commit()
        
        # Create a performance metric
        metric = PerformanceMetric(
            event_id=event.id,
            memory_usage=1024 * 1024,  # 1 MB
            cpu_usage=25.5,  # 25.5%
            duration_ms=150,
            tokens_processed=100,
            cost=0.002
        )
        db_session.add(metric)
        db_session.commit()
        
        # Query the metric back
        queried_metric = db_session.query(PerformanceMetric).filter_by(event_id=event.id).first()
        assert queried_metric is not None
        assert queried_metric.memory_usage == 1024 * 1024
        assert queried_metric.cpu_usage == 25.5
        assert queried_metric.duration_ms == 150
        assert queried_metric.tokens_processed == 100
        assert queried_metric.cost == 0.002
        assert queried_metric.duration_sec == 0.15


class TestRelationships:
    """Tests for the relationships between models."""

    def test_agent_session_relationship(self, db_session):
        """Test the relationship between agents and sessions."""
        # Create an agent
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        # Create two sessions for the agent
        session1 = DbSession(agent_id=agent.id)
        session2 = DbSession(agent_id=agent.id)
        db_session.add_all([session1, session2])
        db_session.commit()
        
        # Query the agent and check its sessions
        queried_agent = db_session.query(Agent).filter_by(agent_id="test-agent").first()
        assert len(queried_agent.sessions) == 2
        assert queried_agent.sessions[0].id == session1.id
        assert queried_agent.sessions[1].id == session2.id

    def test_session_conversation_relationship(self, db_session):
        """Test the relationship between sessions and conversations."""
        # Create an agent and session
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        session = DbSession(agent_id=agent.id)
        db_session.add(session)
        db_session.commit()
        
        # Create two conversations for the session
        conv1 = Conversation(session_id=session.id)
        conv2 = Conversation(session_id=session.id)
        db_session.add_all([conv1, conv2])
        db_session.commit()
        
        # Query the session and check its conversations
        queried_session = db_session.query(DbSession).filter_by(id=session.id).first()
        assert len(queried_session.conversations) == 2
        assert queried_session.conversations[0].id == conv1.id
        assert queried_session.conversations[1].id == conv2.id

    def test_event_specialized_relationships(self, db_session):
        """Test the relationships between events and specialized event tables."""
        # Create an agent
        agent = Agent(agent_id="test-agent")
        db_session.add(agent)
        db_session.commit()
        
        # Create an LLM request event
        event = Event(
            agent_id=agent.id,
            event_type=EventType.LLM_REQUEST,
            channel=EventChannel.LLM,
            level=EventLevel.INFO
        )
        db_session.add(event)
        db_session.commit()
        
        # Create an LLM call record
        llm_call = LLMCall(
            event_id=event.id,
            model="gpt-4",
            prompt="Test prompt",
            response="Test response"
        )
        db_session.add(llm_call)
        db_session.commit()
        
        # Query the event and check its LLM call
        queried_event = db_session.query(Event).filter_by(id=event.id).first()
        assert queried_event.llm_call is not None
        assert queried_event.llm_call.model == "gpt-4"
        assert queried_event.llm_call.prompt == "Test prompt"
        
        # Also check the relationship from LLM call to event
        queried_llm_call = db_session.query(LLMCall).filter_by(event_id=event.id).first()
        assert queried_llm_call.event is not None
        assert queried_llm_call.event.id == event.id
        assert queried_llm_call.event.event_type == EventType.LLM_REQUEST.value


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 