"""MCP client implementation for examples."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Message model for MCP."""
    role: str
    content: str
    name: Optional[str] = None
    
class Context(BaseModel):
    """Context model for MCP."""
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class Tool(BaseModel):
    """Tool model for MCP."""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ListToolsResponse(BaseModel):
    """Response model for list_tools."""
    tools: List[Tool]
    
class ClientSession:
    """Model Context Protocol client for examples."""
    
    def __init__(self, stdio=None, write=None):
        """Initialize MCP client."""
        self.stdio = stdio
        self.write = write
            
    async def get_completion(self, context: Context) -> Dict[str, Any]:
        """Get completion for a context.
        
        This is a simplified implementation that just returns the context
        for demonstration purposes.
        
        Args:
            context: Context object
            
        Returns:
            Context data
        """
        return {
            "context": context.model_dump(),
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        
    async def initialize(self):
        """Initialize the client session."""
        pass
        
    async def list_tools(self) -> ListToolsResponse:
        """List available tools."""
        # Example tools for weather queries
        tools = [
            Tool(
                name="get_weather",
                description="Get weather information for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            ),
            Tool(
                name="get_forecast",
                description="Get weather forecast for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get forecast for"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to forecast"
                        }
                    },
                    "required": ["location"]
                }
            )
        ]
        return ListToolsResponse(tools=tools)
        
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Call a tool with arguments."""
        # Simulate tool responses
        if tool_name == "get_weather":
            return {"content": f"Current weather in {tool_args.get('location', 'Unknown')}: Sunny, 22°C"}
        elif tool_name == "get_forecast":
            days = tool_args.get('days', 5)
            return {"content": f"{days}-day forecast for {tool_args.get('location', 'Unknown')}: Mostly sunny with occasional clouds"}
        return {"content": "Tool not found"} 