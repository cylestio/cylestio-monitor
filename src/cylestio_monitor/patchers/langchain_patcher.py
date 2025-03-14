"""LangChain framework patcher for Cylestio Monitor.

This module provides patching functionality to intercept and monitor LangChain events,
including chain executions, LLM calls, and tool usage.
"""

import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

try:
    # Try to import from langchain_core (0.3+)
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
except ImportError:
    # Fall back to older imports
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import BaseMessage
    from langchain.schema import LLMResult

from ..events_processor import EventProcessor


class LangChainMonitor(BaseCallbackHandler):
    """Monitor for LangChain events."""

    def __init__(self, event_processor: EventProcessor):
        """Initialize the LangChain monitor.
        
        Args:
            event_processor: The event processor to handle monitored events.
        """
        super().__init__()
        self.event_processor = event_processor
        self._start_times: Dict[str, float] = {}
        self._chain_types: Dict[str, str] = {}
        self._session_id = f"langchain-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
    def _get_langchain_version(self) -> str:
        """Get the installed LangChain version."""
        try:
            # Try to get langchain_core version first (0.3+)
            try:
                import langchain_core
                return getattr(langchain_core, "__version__", "unknown")
            except ImportError:
                # Fall back to langchain
                import langchain
                return getattr(langchain, "__version__", "unknown")
        except:
            return "unknown"
    
    def _create_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        direction: Optional[str] = None,
        level: str = "info"
    ) -> None:
        """Create and process a LangChain event with enhanced metadata."""
        # Add LangChain-specific metadata
        enhanced_data = {
            **data,
            "framework_version": self._get_langchain_version(),
            "components": {
                "chain_type": data.get("chain_type"),
                "llm_type": data.get("llm_type"),
                "tool_type": data.get("tool_type")
            }
        }
        
        # Add session/conversation tracking
        if "chain_id" in data:
            enhanced_data["session_id"] = f"langchain-{data['chain_id']}"
        elif "run_id" in data:
            enhanced_data["session_id"] = f"langchain-{data['run_id']}"
        else:
            enhanced_data["session_id"] = self._session_id
            
        # Add turn number if not present
        if "turn_number" not in enhanced_data and "chain_id" in data:
            enhanced_data["turn_number"] = len(self._start_times)
        
        # Convert UUID objects to strings to make them JSON serializable
        enhanced_data = self._make_json_serializable(enhanced_data)
        
        # Process the event with correct channel
        self.event_processor.process_event(
            event_type=event_type,
            data=enhanced_data,
            channel="LANGCHAIN",  # Always use LANGCHAIN channel
            level=level,
            direction=direction
        )
    
    def _make_json_serializable(self, data):
        """Make data JSON serializable by converting problematic types."""
        if isinstance(data, dict):
            return {k: self._make_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._make_json_serializable(item) for item in data)
        elif hasattr(data, 'isoformat'):  # Handle datetime objects
            return data.isoformat()
        elif hasattr(data, '__str__'):  # Convert UUID and other objects to strings
            return str(data)
        else:
            return data
    
    # Chain callbacks
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Handle chain start event."""
        chain_id = kwargs.get("run_id", str(time.time()))
        self._start_times[chain_id] = time.time()
        self._chain_types[chain_id] = serialized.get("name", "unknown")
        
        # Format inputs for better readability
        formatted_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (list, dict)):
                formatted_inputs[key] = value
            else:
                formatted_inputs[key] = str(value)
        
        self._create_event(
            "chain_start",
            {
                "chain_id": chain_id,
                "chain_type": self._chain_types[chain_id],
                "input": formatted_inputs,
                "metadata": serialized.get("metadata", {}),
                "run_id": chain_id
            },
            direction="incoming"
        )
    
    def on_chain_end(
        self, outputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Handle chain end event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            chain_type = self._chain_types.pop(run_id, "unknown")
            
            # Format outputs for better readability
            formatted_outputs = {}
            for key, value in outputs.items():
                if isinstance(value, (list, dict)):
                    formatted_outputs[key] = value
                else:
                    formatted_outputs[key] = str(value)
            
            self._create_event(
                "chain_finish",
                {
                    "chain_id": run_id,
                    "chain_type": chain_type,
                    "output": formatted_outputs,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "chains_per_second": 1.0 / duration if duration > 0 else None
                    },
                    "run_id": run_id
                },
                direction="outgoing"
            )
    
    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Handle chain error event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            chain_type = self._chain_types.pop(run_id, "unknown")
            
            self._create_event(
                "chain_error",
                {
                    "chain_id": run_id,
                    "chain_type": chain_type,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000
                    },
                    "run_id": run_id
                },
                level="error"
            )
    
    # LLM callbacks
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Handle LLM start event."""
        run_id = kwargs.get("run_id", str(time.time()))
        self._start_times[run_id] = time.time()
        
        self._create_event(
            "llm_start",
            {
                "llm_type": serialized.get("name", "unknown"),
                "prompts": prompts,
                "metadata": serialized.get("metadata", {}),
                "run_id": run_id
            },
            direction="outgoing"
        )
    
    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> None:
        """Handle chat model start event."""
        run_id = kwargs.get("run_id", str(time.time()))
        self._start_times[run_id] = time.time()
        
        # Format messages for better readability
        formatted_messages = []
        for message_list in messages:
            formatted_list = []
            for message in message_list:
                formatted_list.append({
                    "type": message.__class__.__name__,
                    "content": str(message.content)
                })
            formatted_messages.append(formatted_list)
        
        self._create_event(
            "chat_model_start",
            {
                "llm_type": serialized.get("name", "unknown"),
                "messages": formatted_messages,
                "metadata": serialized.get("metadata", {}),
                "run_id": run_id
            },
            direction="outgoing"
        )
    
    def on_llm_end(
        self, response: LLMResult, **kwargs: Any
    ) -> None:
        """Handle LLM end event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            # Format response for better readability
            formatted_response = {
                "generations": [[str(gen) for gen in gens] for gens in response.generations]
            }
            if hasattr(response, "llm_output") and response.llm_output:
                formatted_response["llm_output"] = response.llm_output
            
            self._create_event(
                "llm_finish",
                {
                    "response": formatted_response,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "tokens_per_second": None  # Would need token count
                    },
                    "run_id": run_id
                },
                direction="incoming"
            )
    
    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Handle LLM error event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            self._create_event(
                "llm_error",
                {
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000
                    },
                    "run_id": run_id
                },
                level="error"
            )
    
    # Tool callbacks
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Handle tool start event."""
        run_id = kwargs.get("run_id", str(time.time()))
        self._start_times[run_id] = time.time()
        
        self._create_event(
            "tool_start",
            {
                "tool_type": serialized.get("name", "unknown"),
                "input": input_str,
                "metadata": serialized.get("metadata", {}),
                "run_id": run_id
            },
            direction="outgoing"
        )
    
    def on_tool_end(
        self, output: str, **kwargs: Any
    ) -> None:
        """Handle tool end event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            self._create_event(
                "tool_finish",
                {
                    "output": output,
                    "performance": {
                        "duration_ms": duration * 1000
                    },
                    "run_id": run_id
                },
                direction="incoming"
            )
    
    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Handle tool error event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            self._create_event(
                "tool_error",
                {
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000
                    },
                    "run_id": run_id
                },
                level="error"
            )
    
    # Retriever callbacks
    def on_retriever_start(
        self, serialized: Dict[str, Any], query: str, **kwargs: Any
    ) -> None:
        """Handle retriever start event."""
        run_id = kwargs.get("run_id", str(time.time()))
        self._start_times[run_id] = time.time()
        
        self._create_event(
            "retriever_start",
            {
                "retriever_type": serialized.get("name", "unknown"),
                "query": query,
                "metadata": serialized.get("metadata", {}),
                "run_id": run_id
            },
            direction="outgoing"
        )
    
    def on_retriever_end(
        self, documents: List[Any], **kwargs: Any
    ) -> None:
        """Handle retriever end event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            # Format documents for better readability
            formatted_docs = []
            for doc in documents:
                if hasattr(doc, "page_content"):
                    formatted_docs.append({
                        "content": doc.page_content,
                        "metadata": getattr(doc, "metadata", {})
                    })
                else:
                    formatted_docs.append(str(doc))
            
            self._create_event(
                "retriever_finish",
                {
                    "documents": formatted_docs,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "docs_retrieved": len(documents)
                    },
                    "run_id": run_id
                },
                direction="incoming"
            )
    
    def on_retriever_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Handle retriever error event."""
        run_id = kwargs.get("run_id", None)
        if run_id in self._start_times:
            duration = time.time() - self._start_times.pop(run_id)
            
            self._create_event(
                "retriever_error",
                {
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000
                    },
                    "run_id": run_id
                },
                level="error"
            )


def patch_langchain(event_processor: EventProcessor) -> None:
    """Patch LangChain for monitoring.
    
    Args:
        event_processor: Event processor instance
    """
    monitor = LangChainMonitor(event_processor)
    
    try:
        # First approach: Try to monkey patch all Runnable methods to include our callback
        try:
            # Import the necessary modules for LangChain 0.3+
            from langchain_core.runnables.base import Runnable
            
            # Store the original methods
            original_invoke = Runnable.invoke
            original_ainvoke = Runnable.ainvoke if hasattr(Runnable, 'ainvoke') else None
            original_batch = Runnable.batch if hasattr(Runnable, 'batch') else None
            original_abatch = Runnable.abatch if hasattr(Runnable, 'abatch') else None
            
            # Define our patched invoke method
            def patched_invoke(self, input, config=None, **kwargs):
                # Create a new config if none exists
                if config is None:
                    config = {}
                
                # Add our monitor to the callbacks if callbacks exist
                if "callbacks" in config:
                    if isinstance(config["callbacks"], list):
                        if monitor not in config["callbacks"]:
                            config["callbacks"].append(monitor)
                else:
                    # Create callbacks list with our monitor
                    config["callbacks"] = [monitor]
                
                # Call the original method
                return original_invoke(self, input, config=config, **kwargs)
            
            # Apply the patch to invoke
            Runnable.invoke = patched_invoke
            
            # Define and apply patch for ainvoke if it exists
            if original_ainvoke:
                async def patched_ainvoke(self, input, config=None, **kwargs):
                    # Create a new config if none exists
                    if config is None:
                        config = {}
                    
                    # Add our monitor to the callbacks if callbacks exist
                    if "callbacks" in config:
                        if isinstance(config["callbacks"], list):
                            if monitor not in config["callbacks"]:
                                config["callbacks"].append(monitor)
                    else:
                        # Create callbacks list with our monitor
                        config["callbacks"] = [monitor]
                    
                    # Call the original method
                    return await original_ainvoke(self, input, config=config, **kwargs)
                
                Runnable.ainvoke = patched_ainvoke
            
            # Define and apply patch for batch if it exists
            if original_batch:
                def patched_batch(self, inputs, config=None, **kwargs):
                    # Create a new config if none exists
                    if config is None:
                        config = {}
                    
                    # Add our monitor to the callbacks if callbacks exist
                    if "callbacks" in config:
                        if isinstance(config["callbacks"], list):
                            if monitor not in config["callbacks"]:
                                config["callbacks"].append(monitor)
                    else:
                        # Create callbacks list with our monitor
                        config["callbacks"] = [monitor]
                    
                    # Call the original method
                    return original_batch(self, inputs, config=config, **kwargs)
                
                Runnable.batch = patched_batch
            
            # Define and apply patch for abatch if it exists
            if original_abatch:
                async def patched_abatch(self, inputs, config=None, **kwargs):
                    # Create a new config if none exists
                    if config is None:
                        config = {}
                    
                    # Add our monitor to the callbacks if callbacks exist
                    if "callbacks" in config:
                        if isinstance(config["callbacks"], list):
                            if monitor not in config["callbacks"]:
                                config["callbacks"].append(monitor)
                    else:
                        # Create callbacks list with our monitor
                        config["callbacks"] = [monitor]
                    
                    # Call the original method
                    return await original_abatch(self, inputs, config=config, **kwargs)
                
                Runnable.abatch = patched_abatch
            
            # Additionally, try to patch specific classes that might not use Runnable
            try:
                # Try to patch the Chain class directly
                try:
                    from langchain.chains.base import Chain
                    
                    original_chain_call = Chain.__call__
                    
                    def patched_chain_call(self, inputs, callbacks=None, *args, **kwargs):
                        # Add our monitor to callbacks
                        if callbacks is None:
                            callbacks = []
                        if monitor not in callbacks:
                            callbacks.append(monitor)
                        
                        # Call the original method
                        return original_chain_call(self, inputs, callbacks=callbacks, *args, **kwargs)
                    
                    Chain.__call__ = patched_chain_call
                except ImportError:
                    # Try newer imports
                    try:
                        from langchain_core.chains import Chain
                        
                        original_chain_call = Chain.__call__
                        
                        def patched_chain_call(self, inputs, callbacks=None, *args, **kwargs):
                            # Add our monitor to callbacks
                            if callbacks is None:
                                callbacks = []
                            if monitor not in callbacks:
                                callbacks.append(monitor)
                            
                            # Call the original method
                            return original_chain_call(self, inputs, callbacks=callbacks, *args, **kwargs)
                        
                        Chain.__call__ = patched_chain_call
                    except ImportError:
                        pass
                
                # Try to patch LLM classes
                try:
                    from langchain.llms.base import BaseLLM
                    
                    original_llm_generate = BaseLLM._generate
                    
                    def patched_llm_generate(self, prompts, stop=None, callbacks=None, *args, **kwargs):
                        # Add our monitor to callbacks
                        if callbacks is None:
                            callbacks = []
                        if monitor not in callbacks:
                            callbacks.append(monitor)
                        
                        # Call the original method
                        return original_llm_generate(self, prompts, stop=stop, callbacks=callbacks, *args, **kwargs)
                    
                    BaseLLM._generate = patched_llm_generate
                except ImportError:
                    # Try newer imports
                    try:
                        from langchain_core.language_models.llms import BaseLLM
                        
                        original_llm_generate = BaseLLM._generate
                        
                        def patched_llm_generate(self, prompts, stop=None, callbacks=None, *args, **kwargs):
                            # Add our monitor to callbacks
                            if callbacks is None:
                                callbacks = []
                            if monitor not in callbacks:
                                callbacks.append(monitor)
                            
                            # Call the original method
                            return original_llm_generate(self, prompts, stop=stop, callbacks=callbacks, *args, **kwargs)
                        
                        BaseLLM._generate = patched_llm_generate
                    except ImportError:
                        pass
                
                # Try to patch Chat model classes
                try:
                    from langchain.chat_models.base import BaseChatModel
                    
                    original_chat_generate = BaseChatModel._generate
                    
                    def patched_chat_generate(self, messages, stop=None, callbacks=None, *args, **kwargs):
                        # Add our monitor to callbacks
                        if callbacks is None:
                            callbacks = []
                        if monitor not in callbacks:
                            callbacks.append(monitor)
                        
                        # Call the original method
                        return original_chat_generate(self, messages, stop=stop, callbacks=callbacks, *args, **kwargs)
                    
                    BaseChatModel._generate = patched_chat_generate
                    
                    # Specifically patch ChatAnthropic if it's available
                    try:
                        from langchain_anthropic import ChatAnthropic
                        
                        # Store the original _generate method
                        original_anthropic_generate = ChatAnthropic._generate
                        
                        # Define a very simple wrapper that just removes callbacks
                        def patched_anthropic_generate(self, messages, stop=None, callbacks=None, **kwargs):
                            """Very simple wrapper that just removes callbacks parameter."""
                            # Add our monitor to callbacks for monitoring purposes only
                            if callbacks is None:
                                callbacks = []
                            if monitor not in callbacks:
                                callbacks.append(monitor)
                            
                            # Call any monitoring callbacks that we can
                            run_manager = None
                            try:
                                # Try to fire callback events for monitoring
                                for callback in callbacks:
                                    if hasattr(callback, "on_llm_start"):
                                        try:
                                            callback.on_llm_start(
                                                {"name": self.__class__.__name__}, 
                                                [str(message.content) for message in messages],
                                                verbose=getattr(self, "verbose", False)
                                            )
                                        except Exception:
                                            # Ignore callback errors
                                            pass
                            except Exception:
                                # If callback handling fails, just continue
                                pass
                            
                            # Make a copy of kwargs WITHOUT the callbacks
                            clean_kwargs = {k: v for k, v in kwargs.items() if k != "callbacks"}
                            
                            try:
                                # Call the original method WITHOUT passing callbacks
                                result = original_anthropic_generate(self, messages, stop=stop, **clean_kwargs)
                                
                                # Try to fire callback events for monitoring
                                try:
                                    for callback in callbacks:
                                        if hasattr(callback, "on_llm_end"):
                                            try:
                                                callback.on_llm_end(result)
                                            except Exception:
                                                # Ignore callback errors
                                                pass
                                except Exception:
                                    # If callback handling fails, just continue
                                    pass
                                
                                return result
                            except Exception as e:
                                # Try to fire callback events for monitoring
                                try:
                                    for callback in callbacks:
                                        if hasattr(callback, "on_llm_error"):
                                            try:
                                                callback.on_llm_error(e)
                                            except Exception:
                                                # Ignore callback errors
                                                pass
                                except Exception:
                                    # If callback handling fails, just continue
                                    pass
                                
                                # Re-raise the original exception
                                raise
                        
                        # Apply our patched method
                        ChatAnthropic._generate = patched_anthropic_generate
                        
                        # If stream_generate exists, patch it similarly with a very simple approach
                        if hasattr(ChatAnthropic, '_stream_generate'):
                            original_anthropic_stream = ChatAnthropic._stream_generate
                            
                            def patched_anthropic_stream(self, messages, stop=None, callbacks=None, **kwargs):
                                """Very simple wrapper that just removes callbacks parameter."""
                                # Add monitor to callbacks list for monitoring only
                                if callbacks is None:
                                    callbacks = []
                                if monitor not in callbacks:
                                    callbacks.append(monitor)
                                
                                # Try to notify callbacks - this is just for monitoring
                                try:
                                    for callback in callbacks:
                                        if hasattr(callback, "on_llm_start"):
                                            try:
                                                callback.on_llm_start(
                                                    {"name": self.__class__.__name__}, 
                                                    [str(message.content) for message in messages],
                                                    verbose=getattr(self, "verbose", False)
                                                )
                                            except Exception:
                                                # Ignore callback errors
                                                pass
                                except Exception:
                                    # If callback handling fails, just continue
                                    pass
                                
                                # Make a clean copy of kwargs WITHOUT callbacks
                                clean_kwargs = {k: v for k, v in kwargs.items() if k != "callbacks"}
                                
                                # Call original without callbacks
                                return original_anthropic_stream(self, messages, stop=stop, **clean_kwargs)
                            
                            ChatAnthropic._stream_generate = patched_anthropic_stream
                        
                        # Log successful patch
                        event_processor.process_event(
                            event_type="framework_patch",
                            data={
                                "framework": {
                                    "name": "langchain",
                                    "component": "ChatAnthropic",
                                    "version": monitor._get_langchain_version(),
                                },
                                "version": monitor._get_langchain_version(),
                                "patch_time": datetime.now().isoformat(),
                                "method": "ChatAnthropic._generate",
                                "note": "Using simple wrapper approach to avoid internal method dependencies"
                            },
                            channel="LANGCHAIN",
                            level="info"
                        )
                    except ImportError:
                        pass
                except ImportError:
                    # Try newer imports
                    try:
                        from langchain_core.language_models.chat_models import BaseChatModel
                        
                        original_chat_generate = BaseChatModel._generate
                        
                        def patched_chat_generate(self, messages, stop=None, callbacks=None, *args, **kwargs):
                            # Add our monitor to callbacks
                            if callbacks is None:
                                callbacks = []
                            if monitor not in callbacks:
                                callbacks.append(monitor)
                            
                            # Call the original method
                            return original_chat_generate(self, messages, stop=stop, callbacks=callbacks, *args, **kwargs)
                        
                        BaseChatModel._generate = patched_chat_generate
                    except ImportError:
                        pass
            except Exception as e:
                # Log but continue if we have at least patched Runnable
                event_processor.process_event(
                    event_type="framework_patch_warning",
                    data={
                        "framework": "langchain",
                        "warning": f"Could not patch all classes: {str(e)}",
                        "warning_type": type(e).__name__
                    },
                    channel="LANGCHAIN",
                    level="warning"
                )
            
            # Log successful patch
            event_processor.process_event(
                event_type="framework_patch",
                data={
                    "framework": {
                        "name": "langchain",
                        "version": monitor._get_langchain_version(),
                        "components": {}
                    },
                    "version": monitor._get_langchain_version(),
                    "patch_time": datetime.now().isoformat(),
                    "method": "Runnable.invoke"
                },
                channel="LANGCHAIN",
                level="info"
            )
            return
        except ImportError:
            # If we can't import Runnable, try the next approach
            pass
            
        # Second approach: Try the LangChain 0.3+ approach with CallbackManager
        try:
            # Try the LangChain 0.3+ approach first
            from langchain_core.callbacks import CallbackManager
            
            # Import the get_callback_manager and set_callback_manager functions
            try:
                from langchain_core.globals import get_callback_manager, set_callback_manager
                
                # Get the current callback manager
                current_manager = get_callback_manager()
                
                # Add our monitor to the handlers
                if hasattr(current_manager, 'handlers'):
                    if monitor not in current_manager.handlers:
                        current_manager.handlers.append(monitor)
                else:
                    # Create a new callback manager with our monitor
                    new_manager = CallbackManager(handlers=[monitor])
                    set_callback_manager(new_manager)
                
                # Log successful patch
                event_processor.process_event(
                    event_type="framework_patch",
                    data={
                        "framework": {
                            "name": "langchain",
                            "version": monitor._get_langchain_version(),
                            "components": {}
                        },
                        "version": monitor._get_langchain_version(),
                        "patch_time": datetime.now().isoformat(),
                        "method": "CallbackManager"
                    },
                    channel="LANGCHAIN",
                    level="info"
                )
                return
            except ImportError:
                # If we can't import the globals module, try the next approach
                pass
                
            # Try using the configure method if available
            if hasattr(CallbackManager, 'configure'):
                # Get the current callback manager
                callback_manager = CallbackManager.configure()
                
                # Add our monitor to the handlers
                callback_manager.add_handler(monitor)
                
                # Log successful patch
                event_processor.process_event(
                    event_type="framework_patch",
                    data={
                        "framework": {
                            "name": "langchain",
                            "version": monitor._get_langchain_version(),
                            "components": {}
                        },
                        "version": monitor._get_langchain_version(),
                        "patch_time": datetime.now().isoformat(),
                        "method": "CallbackManager"
                    },
                    channel="LANGCHAIN",
                    level="info"
                )
                return
        except ImportError:
            pass
            
        # Try the LangChain 0.2 approach
        try:
            from langchain.callbacks.manager import CallbackManager
            
            # Get the current callback manager
            callback_manager = CallbackManager.configure()
            
            # Add our monitor to the handlers
            callback_manager.add_handler(monitor)
            
            # Log successful patch
            event_processor.process_event(
                event_type="framework_patch",
                data={
                    "framework": {
                        "name": "langchain",
                        "version": monitor._get_langchain_version(),
                        "components": {}
                    },
                    "version": monitor._get_langchain_version(),
                    "patch_time": datetime.now().isoformat(),
                    "method": "CallbackManager"
                },
                channel="LANGCHAIN",
                level="info"
            )
            return
        except ImportError:
            pass
            
        # Try the older approach (pre-0.2)
        try:
            from langchain.callbacks import set_global_handlers
            set_global_handlers([monitor])
            
            # Log successful patch
            event_processor.process_event(
                event_type="framework_patch",
                data={
                    "framework": {
                        "name": "langchain",
                        "version": monitor._get_langchain_version(),
                        "components": {}
                    },
                    "version": monitor._get_langchain_version(),
                    "patch_time": datetime.now().isoformat(),
                    "method": "set_global_handlers"
                },
                channel="LANGCHAIN",
                level="info"
            )
            return
        except ImportError:
            pass
        
    except Exception as e:
        # Log patch failure
        event_processor.process_event(
            event_type="framework_patch_error",
            data={
                "framework": "langchain",
                "error": str(e),
                "error_type": type(e).__name__
            },
            channel="LANGCHAIN",
            level="error"
        )
        # Don't raise the exception, just log it and continue
        # This allows the application to run even if LangChain monitoring fails 