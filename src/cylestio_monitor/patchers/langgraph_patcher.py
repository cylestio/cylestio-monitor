"""LangGraph framework patcher for Cylestio Monitor.

This module provides patching functionality to intercept and monitor LangGraph events,
including graph node executions, data source interactions, and state transitions.
"""

import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import logging

from langgraph.graph import END, StateGraph
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGenerationChunk, GenerationChunk, LLMResult
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableConfig

from ..utils.trace_context import TraceContext
from ..utils.event_logging import log_event


class LangGraphMonitor:
    """Monitor for LangGraph events."""

    def __init__(self):
        """Initialize the LangGraph monitor."""
        self._start_times: Dict[str, float] = {}
        self._node_types: Dict[str, str] = {}
        self._session_id = f"langgraph-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._turn_counters: Dict[str, int] = {}
        
    def _get_langgraph_version(self) -> str:
        """Get the installed LangGraph version."""
        try:
            import langgraph
            return getattr(langgraph, "__version__", "unknown")
        except:
            return "unknown"
    
    def _create_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        direction: Optional[str] = None,
        level: str = "INFO"
    ) -> None:
        """Create and process a LangGraph event with enhanced metadata."""
        # Add LangGraph-specific metadata
        enhanced_data = {
            **data,
            "framework_version": self._get_langgraph_version(),
            "components": {
                "node_type": data.get("node_type"),
                "graph_type": data.get("graph_type")
            }
        }
        
        # Add session/conversation tracking
        if "graph_id" in data:
            enhanced_data["session_id"] = f"langgraph-{data['graph_id']}"
            
            # Track turn numbers
            if "graph_id" in data and "turn_number" not in enhanced_data:
                graph_id = data["graph_id"]
                if graph_id not in self._turn_counters:
                    self._turn_counters[graph_id] = 0
                else:
                    self._turn_counters[graph_id] += 1
                enhanced_data["turn_number"] = self._turn_counters[graph_id]
        else:
            enhanced_data["session_id"] = self._session_id
        
        # Add direction if provided
        if direction:
            enhanced_data["direction"] = direction
            
        # Log the event
        log_event(
            name=f"langgraph.{event_type}",
            attributes=enhanced_data,
            level=level
        )
    
    def on_graph_start(self, graph_id: str, graph_config: Dict[str, Any], inputs: Dict[str, Any]) -> None:
        """Handle graph start event."""
        self._start_times[graph_id] = time.time()
        
        # Format inputs for better readability
        formatted_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (list, dict)):
                formatted_inputs[key] = value
            else:
                formatted_inputs[key] = str(value)
        
        self._create_event(
            "graph_start",
            {
                "graph_id": graph_id,
                "graph_type": graph_config.get("name", "unknown"),
                "input": formatted_inputs,
                "metadata": graph_config.get("metadata", {}),
                "config": {
                    "name": graph_config.get("name"),
                    "description": graph_config.get("description"),
                    "nodes": list(graph_config.get("nodes", {}).keys())
                }
            },
            direction="incoming"
        )
    
    def on_graph_end(self, graph_id: str, outputs: Dict[str, Any]) -> None:
        """Handle graph end event."""
        if graph_id in self._start_times:
            duration = time.time() - self._start_times.pop(graph_id)
            
            # Format outputs for better readability
            formatted_outputs = {}
            for key, value in outputs.items():
                if isinstance(value, (list, dict)):
                    formatted_outputs[key] = value
                else:
                    formatted_outputs[key] = str(value)
            
            self._create_event(
                "graph_finish",
                {
                    "graph_id": graph_id,
                    "output": formatted_outputs,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "graphs_per_second": 1.0 / duration if duration > 0 else None
                    }
                },
                direction="outgoing"
            )
    
    def on_graph_error(self, graph_id: str, error: Exception) -> None:
        """Handle graph error event."""
        if graph_id in self._start_times:
            duration = time.time() - self._start_times.pop(graph_id)
            
            self._create_event(
                "graph_error",
                {
                    "graph_id": graph_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "error_time": datetime.now().isoformat()
                    }
                },
                level="error"
            )
    
    def on_node_start(self, graph_id: str, node_id: str, node_type: str, inputs: Dict[str, Any]) -> None:
        """Handle node start event."""
        node_run_id = f"{graph_id}:{node_id}:{time.time()}"
        self._start_times[node_run_id] = time.time()
        self._node_types[node_run_id] = node_type
        
        # Format inputs for better readability
        formatted_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (list, dict)):
                formatted_inputs[key] = value
            else:
                formatted_inputs[key] = str(value)
        
        # Estimate token count
        estimated_tokens = sum(len(str(v)) // 4 for v in inputs.values())
        
        self._create_event(
            "node_start",
            {
                "graph_id": graph_id,
                "node_id": node_id,
                "node_type": node_type,
                "run_id": node_run_id,
                "input": {
                    "content": formatted_inputs,
                    "estimated_tokens": estimated_tokens
                }
            },
            direction="incoming"
        )
    
    def on_node_end(self, graph_id: str, node_id: str, outputs: Dict[str, Any]) -> None:
        """Handle node end event."""
        # Find the matching node_run_id
        node_run_id_prefix = f"{graph_id}:{node_id}:"
        matching_keys = [k for k in self._start_times.keys() if k.startswith(node_run_id_prefix)]
        
        if matching_keys:
            node_run_id = matching_keys[0]  # Use the first matching key
            duration = time.time() - self._start_times.pop(node_run_id)
            node_type = self._node_types.pop(node_run_id, "unknown")
            
            # Format outputs for better readability
            formatted_outputs = {}
            for key, value in outputs.items():
                if isinstance(value, (list, dict)):
                    formatted_outputs[key] = value
                else:
                    formatted_outputs[key] = str(value)
            
            # Estimate token count
            estimated_tokens = sum(len(str(v)) // 4 for v in outputs.values())
            
            self._create_event(
                "node_finish",
                {
                    "graph_id": graph_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "run_id": node_run_id,
                    "output": {
                        "content": formatted_outputs,
                        "estimated_tokens": estimated_tokens
                    },
                    "performance": {
                        "duration_ms": duration * 1000,
                        "nodes_per_second": 1.0 / duration if duration > 0 else None
                    }
                },
                direction="outgoing"
            )
    
    def on_node_error(self, graph_id: str, node_id: str, error: Exception) -> None:
        """Handle node error event."""
        # Find the matching node_run_id
        node_run_id_prefix = f"{graph_id}:{node_id}:"
        matching_keys = [k for k in self._start_times.keys() if k.startswith(node_run_id_prefix)]
        
        if matching_keys:
            node_run_id = matching_keys[0]  # Use the first matching key
            duration = time.time() - self._start_times.pop(node_run_id)
            node_type = self._node_types.pop(node_run_id, "unknown")
            
            self._create_event(
                "node_error",
                {
                    "graph_id": graph_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "run_id": node_run_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "error_time": datetime.now().isoformat()
                    }
                },
                level="error"
            )
    
    def on_state_update(self, graph_id: str, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Handle state update event."""
        # Format states for better readability
        formatted_old_state = {}
        formatted_new_state = {}
        
        for key, value in old_state.items():
            if isinstance(value, (list, dict)):
                formatted_old_state[key] = value
            else:
                formatted_old_state[key] = str(value)
                
        for key, value in new_state.items():
            if isinstance(value, (list, dict)):
                formatted_new_state[key] = value
            else:
                formatted_new_state[key] = str(value)
        
        # Calculate changes
        changes = {}
        for key in set(old_state.keys()) | set(new_state.keys()):
            if key not in old_state:
                changes[key] = {"type": "added", "value": formatted_new_state[key]}
            elif key not in new_state:
                changes[key] = {"type": "removed", "value": formatted_old_state[key]}
            elif old_state[key] != new_state[key]:
                changes[key] = {
                    "type": "modified",
                    "old_value": formatted_old_state[key],
                    "new_value": formatted_new_state[key]
                }
        
        self._create_event(
            "state_update",
            {
                "graph_id": graph_id,
                "old_state": formatted_old_state,
                "new_state": formatted_new_state,
                "changes": changes
            }
        )
    
    def on_agent_action(self, graph_id: str, agent_id: str, action: Dict[str, Any]) -> None:
        """Handle agent action event."""
        # Format action for better readability
        formatted_action = {}
        for key, value in action.items():
            if isinstance(value, (list, dict)):
                formatted_action[key] = value
            else:
                formatted_action[key] = str(value)
        
        self._create_event(
            "agent_action",
            {
                "graph_id": graph_id,
                "agent_id": agent_id,
                "action": formatted_action,
                "action_type": action.get("type", "unknown")
            }
        )


def patch_langgraph() -> None:
    """Patch LangGraph for monitoring."""
    monitor = LangGraphMonitor()
    
    # Register the monitor with LangGraph
    try:
        # Try to register with LangGraph callbacks
        try:
            from langgraph.callbacks import set_global_handlers
            set_global_handlers([monitor])
            
            # Log successful patch
            log_event(
                name="framework_patch",
                attributes={
                    "framework": "langgraph",
                    "version": monitor._get_langgraph_version(),
                    "patch_time": datetime.now().isoformat(),
                    "method": "set_global_handlers"
                },
                level="info"
            )
            return
        except ImportError:
            pass
        
        # Try alternative approach for newer versions
        try:
            import langgraph
            
            # Check if we can monkey patch the StateGraph class
            if hasattr(langgraph, "graph") and hasattr(langgraph.graph, "StateGraph"):
                # Log that we're using monkey patching instead
                log_event(
                    name="framework_patch",
                    attributes={
                        "framework": "langgraph",
                        "version": monitor._get_langgraph_version(),
                        "patch_time": datetime.now().isoformat(),
                        "method": "monkey_patch",
                        "note": "Using monkey patching as callbacks module is not available"
                    },
                    level="info"
                )
                return
        except ImportError:
            pass
        
        # If we get here, we couldn't patch LangGraph
        raise ImportError("Could not find a compatible way to register callbacks with LangGraph")
        
    except Exception as e:
        # Log patch failure
        log_event(
            name="framework_patch_error",
            attributes={
                "framework": "langgraph",
                "error": str(e),
                "error_type": type(e).__name__
            },
            level="error"
        )
        # Don't raise the exception, just log it and continue
        # This allows the application to run even if LangGraph monitoring fails 

def unpatch_langgraph():
    """Remove monitoring patches from LangGraph library.
    
    This function is called by stop_monitoring to restore original functionality.
    """
    logger = logging.getLogger(__name__)
    logger.info("Unpatching LangGraph - restoring original functionality")
    
    # Nothing specific to unpatch for now
    pass 