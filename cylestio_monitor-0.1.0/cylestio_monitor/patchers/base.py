"""Base patcher class for Cylestio Monitor."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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
