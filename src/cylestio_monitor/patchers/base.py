"""Base patcher class for Cylestio Monitor."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
import logging


class BasePatcher(ABC):
    """Base class for all patchers.

    A patcher is responsible for intercepting and monitoring interactions with
    a specific framework or library. Each patcher must implement:
    - patch(): Apply the monitoring patches
    - unpatch(): Remove the monitoring patches
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize patcher.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.is_patched = False
        self.logger = logging.getLogger("CylestioMonitor.Patcher")

    @abstractmethod
    def patch(self) -> None:
        """Apply monitoring patches.

        This method should:
        1. Check if the target framework/library is available
        2. Apply necessary patches to intercept interactions
        3. Set up monitoring hooks

        Raises:
            ImportError: If required framework/library is not available
            RuntimeError: If patching fails
        """
        pass

    @abstractmethod
    def unpatch(self) -> None:
        """Remove monitoring patches.

        This method should:
        1. Remove all applied patches
        2. Clean up any monitoring hooks
        3. Restore original functionality

        Raises:
            RuntimeError: If unpatching fails
        """
        pass

    @classmethod
    def patch_module(cls) -> None:
        """Apply global patches to the module rather than specific instances.
        
        This is used for automatic detection and patching of library modules
        without requiring explicit client instantiation.
        
        Subclasses should implement this if they support module-level patching.
        """
        logger = logging.getLogger(f"CylestioMonitor.Patcher.{cls.__name__}")
        logger.debug(f"Module-level patching not implemented for {cls.__name__}")
        
    @classmethod    
    def unpatch_module(cls) -> None:
        """Remove global patches from the module.
        
        Subclasses should implement this if they support module-level patching.
        """
        logger = logging.getLogger(f"CylestioMonitor.Patcher.{cls.__name__}")
        logger.debug(f"Module-level unpatching not implemented for {cls.__name__}")
