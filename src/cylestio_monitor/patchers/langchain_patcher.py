"""
Patchers for LangChain to integrate with the telemetry system.

This module provides patchers for various LangChain components to instrument them
for telemetry data collection.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union, Type

from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.patchers.base import BasePatcher

logger = logging.getLogger("CylestioMonitor")


class LangChainPatcher(BasePatcher):
    """Patcher for LangChain components."""
    
    def __init__(self):
        """Initialize the LangChain patcher."""
        super().__init__("langchain")
        self._patched = False
        self._chain_methods = {}  # Keep track of original methods
        self._llm_methods = {}
        self._retriever_methods = {}
        self._document_methods = {}
        
    def apply(self) -> bool:
        """Apply the LangChain patches.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._patched:
            logger.warning("LangChain is already patched")
            return False
        
        try:
            # Log patch event
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "langchain",
                    "patch.type": "monkey_patch",
                    "patch.components": [
                        "chains", "llms", "retrievers",
                        "documents", "chat_models"
                    ]
                }
            )
            
            # Apply individual patches
            self._patch_chains()
            self._patch_llms()
            self._patch_retrievers()
            self._patch_chat_models()
            self._patch_documents()
            
            self._patched = True
            logger.info("Successfully patched LangChain")
            return True
        except ImportError as e:
            logger.warning(f"Failed to patch LangChain: {e}")
            return False
        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={
                    "framework.name": "langchain"
                }
            )
            logger.exception(f"Error patching LangChain: {e}")
            return False
            
    def _patch_chains(self) -> None:
        """Patch LangChain chains."""
        try:
            # Import here to avoid dependency if not used
            from langchain.chains.base import Chain
            
            # Store original method
            original_call = Chain.__call__
            self._chain_methods["__call__"] = original_call
            
            def instrumented_call(self, *args, **kwargs):
                """Instrumented version of Chain.__call__."""
                # Start a new span for this chain
                span_info = TraceContext.start_span(f"chain.{self.__class__.__name__}")
                
                # Extract relevant attributes
                chain_attributes = {
                    "chain.name": self.__class__.__name__,
                    "chain.id": str(id(self)),
                    "framework.name": "langchain",
                    "framework.type": "chain",
                }
                
                # Add input attributes (safely)
                if args and len(args) > 0:
                    chain_attributes["chain.input.type"] = type(args[0]).__name__
                    if isinstance(args[0], dict):
                        chain_attributes["chain.input.keys"] = list(args[0].keys())
                
                if kwargs:
                    chain_attributes["chain.input.kwargs"] = list(kwargs.keys())
                
                # Log chain start event
                log_event(
                    name="chain.start",
                    attributes=chain_attributes
                )
                
                try:
                    # Call the original method
                    result = original_call(self, *args, **kwargs)
                    
                    # Prepare result attributes
                    result_attributes = chain_attributes.copy()
                    result_attributes.update({
                        "chain.status": "success",
                    })
                    
                    # Handle different result types
                    if isinstance(result, dict):
                        # For security and size reasons, only include keys not values
                        result_attributes["chain.result.keys"] = list(result.keys())
                    elif hasattr(result, "__dict__"):
                        result_attributes["chain.result.type"] = type(result).__name__
                        result_attributes["chain.result.attrs"] = list(result.__dict__.keys())
                    else:
                        result_attributes["chain.result.type"] = type(result).__name__
                    
                    # Log chain end event
                    log_event(
                        name="chain.end",
                        attributes=result_attributes
                    )
                    
                    return result
                except Exception as e:
                    # Log chain error event
                    log_error(
                        name="chain.error",
                        error=e,
                        attributes=chain_attributes
                    )
                    raise
                finally:
                    # End the span
                    TraceContext.end_span()
            
            # Apply the patch
            Chain.__call__ = instrumented_call
            logger.debug("Patched LangChain chains")
        except ImportError:
            logger.debug("LangChain chains not available, skipping patch")
        except Exception as e:
            logger.warning(f"Error patching LangChain chains: {e}")
            raise

    def _patch_llms(self) -> None:
        """Patch LangChain LLMs."""
        try:
            # Import here to avoid dependency if not used
            from langchain.llms.base import BaseLLM
            
            # Store original method
            original_generate = BaseLLM._generate
            self._llm_methods["_generate"] = original_generate
            
            def instrumented_generate(self, prompts, stop=None, *args, **kwargs):
                """Instrumented version of BaseLLM._generate."""
                # Start a new span for this LLM call
                span_info = TraceContext.start_span(f"llm.{self.__class__.__name__}")
                
                # Extract relevant attributes
                llm_attributes = {
                    "llm.name": self.__class__.__name__,
                    "llm.id": str(id(self)),
                    "framework.name": "langchain",
                    "framework.type": "llm",
                    "llm.num_prompts": len(prompts) if isinstance(prompts, list) else 1,
                }
                
                # Add model info if available
                if hasattr(self, "model_name"):
                    llm_attributes["llm.model"] = self.model_name
                
                # Add stop tokens info if available
                if stop:
                    llm_attributes["llm.stop_tokens"] = stop if isinstance(stop, list) else [stop]
                
                # Log LLM start event
                log_event(
                    name="llm.request",
                    attributes=llm_attributes
                )
                
                try:
                    # Call the original method
                    result = original_generate(self, prompts, stop, *args, **kwargs)
                    
                    # Prepare result attributes
                    result_attributes = llm_attributes.copy()
                    result_attributes.update({
                        "llm.status": "success",
                    })
                    
                    # Add token usage if available
                    if hasattr(result, "llm_output") and result.llm_output:
                        if "token_usage" in result.llm_output:
                            token_usage = result.llm_output["token_usage"]
                            if "completion_tokens" in token_usage:
                                result_attributes["llm.response.usage.output_tokens"] = token_usage["completion_tokens"]
                            if "prompt_tokens" in token_usage:
                                result_attributes["llm.response.usage.input_tokens"] = token_usage["prompt_tokens"]
                            if "total_tokens" in token_usage:
                                result_attributes["llm.response.usage.total_tokens"] = token_usage["total_tokens"]
                    
                    # Log LLM response event
                    log_event(
                        name="llm.response",
                        attributes=result_attributes
                    )
                    
                    return result
                except Exception as e:
                    # Log LLM error event
                    log_error(
                        name="llm.error",
                        error=e,
                        attributes=llm_attributes
                    )
                    raise
                finally:
                    # End the span
                    TraceContext.end_span()
            
            # Apply the patch
            BaseLLM._generate = instrumented_generate
            logger.debug("Patched LangChain LLMs")
        except ImportError:
            logger.debug("LangChain LLMs not available, skipping patch")
        except Exception as e:
            logger.warning(f"Error patching LangChain LLMs: {e}")

    def _patch_retrievers(self) -> None:
        """Patch LangChain retrievers."""
        try:
            # Import here to avoid dependency if not used
            from langchain.schema.retriever import BaseRetriever
            
            # Store original method
            original_get_relevant_documents = BaseRetriever.get_relevant_documents
            self._retriever_methods["get_relevant_documents"] = original_get_relevant_documents
            
            def instrumented_get_relevant_documents(self, query, *args, **kwargs):
                """Instrumented version of BaseRetriever.get_relevant_documents."""
                # Start a new span for this retriever call
                span_info = TraceContext.start_span(f"retriever.{self.__class__.__name__}")
                
                # Extract relevant attributes
                retriever_attributes = {
                    "retriever.name": self.__class__.__name__,
                    "retriever.id": str(id(self)),
                    "framework.name": "langchain",
                    "framework.type": "retriever",
                    "retriever.query.length": len(query) if isinstance(query, str) else 0,
                }
                
                # Log retriever start event
                log_event(
                    name="retrieval.query",
                    attributes=retriever_attributes
                )
                
                try:
                    # Call the original method
                    documents = original_get_relevant_documents(self, query, *args, **kwargs)
                    
                    # Prepare result attributes
                    result_attributes = retriever_attributes.copy()
                    result_attributes.update({
                        "retriever.status": "success",
                        "retriever.num_documents": len(documents) if documents else 0,
                    })
                    
                    # Log retriever result event
                    log_event(
                        name="retrieval.result",
                        attributes=result_attributes
                    )
                    
                    return documents
                except Exception as e:
                    # Log retriever error event
                    log_error(
                        name="retrieval.error",
                        error=e,
                        attributes=retriever_attributes
                    )
                    raise
                finally:
                    # End the span
                    TraceContext.end_span()
            
            # Apply the patch
            BaseRetriever.get_relevant_documents = instrumented_get_relevant_documents
            logger.debug("Patched LangChain retrievers")
        except ImportError:
            logger.debug("LangChain retrievers not available, skipping patch")
        except Exception as e:
            logger.warning(f"Error patching LangChain retrievers: {e}")

    def _patch_chat_models(self) -> None:
        """Patch LangChain chat models."""
        try:
            # Import here to avoid dependency if not used
            from langchain.chat_models.base import BaseChatModel
            
            # Store original method
            original_generate = BaseChatModel._generate
            self._llm_methods["chat_generate"] = original_generate
            
            def instrumented_generate(self, messages, stop=None, *args, **kwargs):
                """Instrumented version of BaseChatModel._generate."""
                # Start a new span for this chat model call
                span_info = TraceContext.start_span(f"chat_model.{self.__class__.__name__}")
                
                # Extract relevant attributes
                chat_attributes = {
                    "llm.name": self.__class__.__name__,
                    "llm.id": str(id(self)),
                    "framework.name": "langchain",
                    "framework.type": "chat_model",
                    "llm.num_messages": len(messages) if isinstance(messages, list) else 1,
                }
                
                # Add model info if available
                if hasattr(self, "model_name"):
                    chat_attributes["llm.model"] = self.model_name
                
                # Add message roles counts
                if isinstance(messages, list):
                    role_counts = {}
                    for msg in messages:
                        role = getattr(msg, "type", "unknown")
                        role_counts[role] = role_counts.get(role, 0) + 1
                    for role, count in role_counts.items():
                        chat_attributes[f"llm.messages.{role}"] = count
                
                # Log chat model start event
                log_event(
                    name="llm.request",
                    attributes=chat_attributes
                )
                
                try:
                    # Call the original method
                    result = original_generate(self, messages, stop, *args, **kwargs)
                    
                    # Prepare result attributes
                    result_attributes = chat_attributes.copy()
                    result_attributes.update({
                        "llm.status": "success",
                    })
                    
                    # Add token usage if available
                    if hasattr(result, "llm_output") and result.llm_output:
                        if "token_usage" in result.llm_output:
                            token_usage = result.llm_output["token_usage"]
                            if "completion_tokens" in token_usage:
                                result_attributes["llm.response.usage.output_tokens"] = token_usage["completion_tokens"]
                            if "prompt_tokens" in token_usage:
                                result_attributes["llm.response.usage.input_tokens"] = token_usage["prompt_tokens"]
                            if "total_tokens" in token_usage:
                                result_attributes["llm.response.usage.total_tokens"] = token_usage["total_tokens"]
                    
                    # Extract response message roles
                    if hasattr(result, "generations") and result.generations:
                        roles = []
                        for gen in result.generations:
                            if hasattr(gen, "message") and hasattr(gen.message, "type"):
                                roles.append(gen.message.type)
                        if roles:
                            result_attributes["llm.response.roles"] = roles
                    
                    # Log chat model response event
                    log_event(
                        name="llm.response",
                        attributes=result_attributes
                    )
                    
                    return result
                except Exception as e:
                    # Log chat model error event
                    log_error(
                        name="llm.error",
                        error=e,
                        attributes=chat_attributes
                    )
                    raise
                finally:
                    # End the span
                    TraceContext.end_span()
            
            # Apply the patch
            BaseChatModel._generate = instrumented_generate
            logger.debug("Patched LangChain chat models")
        except ImportError:
            logger.debug("LangChain chat models not available, skipping patch")
        except Exception as e:
            logger.warning(f"Error patching LangChain chat models: {e}")

    def _patch_documents(self) -> None:
        """Patch LangChain documents."""
        logger.debug("Document patching not implemented yet, skipping")
        pass 

# Global instance for module-level patching
_langchain_patcher = None

def patch_langchain():
    """Apply LangChain patches globally."""
    global _langchain_patcher
    
    if _langchain_patcher is None:
        logger.info("Initializing global LangChain patcher")
        _langchain_patcher = LangChainPatcher()
    
    try:
        result = _langchain_patcher.apply()
        if result:
            logger.info("LangChain patched successfully")
        else:
            logger.warning("Failed to patch LangChain")
        return result
    except ImportError:
        logger.warning("LangChain not available, skipping patch")
        return False
    except Exception as e:
        logger.error(f"Error patching LangChain: {e}")
        return False

def unpatch_langchain():
    """Remove LangChain patches globally."""
    global _langchain_patcher
    
    if _langchain_patcher is not None and _langchain_patcher._patched:
        try:
            # Implement the unpatch logic here
            logger.info("LangChain unpatch not yet implemented")
            return True
        except Exception as e:
            logger.error(f"Error unpatching LangChain: {e}")
            return False
    return False 