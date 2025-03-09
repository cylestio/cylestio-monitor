"""Auto-detection module for Cylestio Monitor.

This module handles automatic detection of available frameworks and creates
appropriate patchers without requiring explicit user configuration.
"""

import importlib
from typing import List, Any

from .patchers.base import BasePatcher

def detect_frameworks() -> List[BasePatcher]:
    """Auto-detect available frameworks and create patchers.
    
    This function attempts to import various frameworks and creates
    appropriate patchers for those that are available.
    
    Returns:
        List of initialized patchers for detected frameworks
    """
    patchers = []
    
    # Try to detect MCP
    try:
        if importlib.util.find_spec("mcp"):
            from .patchers.mcp import MCPPatcher
            patchers.append(MCPPatcher())
    except ImportError:
        pass
        
    # Try to detect Anthropic
    try:
        if importlib.util.find_spec("anthropic"):
            from .patchers.anthropic import AnthropicPatcher
            patchers.append(AnthropicPatcher())
    except ImportError:
        pass
        
    # Add more framework detection here...
    
    return patchers 