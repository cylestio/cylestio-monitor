"""Tests for Model Context Protocol implementation."""

import pytest
from fastapi.testclient import TestClient
import httpx
from cylestio_monitor.mcp.client import MCPClient, Context, Message
from cylestio_monitor.mcp.server import MCPServer

@pytest.fixture
def test_server():
    """Create test server instance."""
    server = MCPServer(api_key="test-key")
    return server

@pytest.fixture
def test_client(test_server):
    """Create test client for FastAPI app."""
    return TestClient(test_server.app)

@pytest.fixture
def mcp_client():
    """Create MCP client instance."""
    return MCPClient(
        base_url="http://test",
        api_key="test-key"
    )

def test_create_context(mcp_client):
    """Test context creation."""
    data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "metadata": {"test": "value"}
    }
    
    context = mcp_client.create_context(data)
    assert isinstance(context, Context)
    assert len(context.messages) == 1
    assert context.messages[0].role == "user"
    assert context.messages[0].content == "Hello"
    assert context.metadata["test"] == "value"

def test_update_context(mcp_client):
    """Test context update."""
    initial_data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    context = mcp_client.create_context(initial_data)
    
    update_data = {
        "messages": [
            {"role": "assistant", "content": "Hi"}
        ],
        "metadata": {"key": "value"}
    }
    
    updated = mcp_client.update_context(context, update_data)
    assert len(updated.messages) == 2
    assert updated.metadata["key"] == "value"

def test_server_auth_required(test_client):
    """Test server authentication."""
    response = test_client.post("/v1/completions", json={
        "messages": [],
        "metadata": {}
    })
    assert response.status_code == 403

def test_server_auth_valid(test_client):
    """Test server with valid authentication."""
    response = test_client.post(
        "/v1/completions",
        json={
            "messages": [
                {"role": "user", "content": "test"}
            ],
            "metadata": {}
        },
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "context" in data
    assert "usage" in data

def test_server_completion(test_client):
    """Test completion generation."""
    response = test_client.post(
        "/v1/completions",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        },
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["role"] == "assistant"
    assert isinstance(data["message"]["content"], str)
    assert "usage" in data

@pytest.mark.asyncio
async def test_server_async_completion(test_server):
    """Test async completion processing."""
    context = Context(
        messages=[
            Message(role="user", content="test")
        ]
    )
    response = await test_server._process_completion(context)
    assert response.message.role == "assistant"
    assert isinstance(response.usage, dict)

def test_invalid_context(test_client):
    """Test invalid context handling."""
    response = test_client.post(
        "/v1/completions",
        json={"invalid": "data"},
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 422

def test_client_error_handling(mcp_client):
    """Test client error handling."""
    with pytest.raises(httpx.HTTPError):
        context = Context(messages=[])
        mcp_client.get_completion(context) 