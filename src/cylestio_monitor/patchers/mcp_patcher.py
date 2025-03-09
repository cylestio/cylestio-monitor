import asyncio
from cylestio_monitor.events_listener import monitor_call
from cylestio_monitor.events_processor import log_event

def patch_mcp_client(ClientSession):
    """
    Replaces ClientSession.call_tool with a monitored version.
    """
    original_call_tool = ClientSession.call_tool
    ClientSession.call_tool = monitor_call(original_call_tool, channel="MCP")
    log_event("MCP_patch", {"message": "MCP client patched"}, "SYSTEM")