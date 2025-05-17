"""
Process execution patching module for Cylestio Monitor.

This module provides patching for subprocess.Popen and os.system to detect RCE.
"""

import logging

logger = logging.getLogger(__name__)

# Keep track of patching status
_process_patched = False


def patch_process_monitoring(enable_detection: bool = True) -> bool:
    """
    Apply process execution monitoring patches.

    Args:
        enable_detection: Whether to enable RCE detection rules

    Returns:
        bool: True if successful, False otherwise
    """
    global _process_patched

    if _process_patched:
        logger.info("Process execution monitoring already enabled")
        return True

    try:
        # Import the process monitoring module
        from cylestio_monitor._sensors.process import initialize

        # Import the process detection module to enable/disable rules
        try:
            from cylestio_monitor._sensors.process import enable_rce_detection

            # Set RCE detection according to configuration
            enable_rce_detection(enable_detection)

            if enable_detection:
                logger.info("RCE detection rules enabled")
            else:
                logger.info("RCE detection rules disabled")
        except ImportError:
            logger.warning("Could not configure RCE detection")

        # Initialize process monitoring
        initialize()

        # Mark as patched
        _process_patched = True

        return True
    except Exception as e:
        logger.error(f"Failed to patch process execution monitoring: {e}")
        return False


def unpatch_process_monitoring() -> bool:
    """
    Remove process execution monitoring patches.

    Returns:
        bool: True if successful, False otherwise
    """
    global _process_patched

    if not _process_patched:
        return True

    try:
        # Import the unpatch function
        import subprocess
        import os
        from cylestio_monitor._sensors.process import _orig_popen, _orig_system

        # Restore original functions
        subprocess.Popen = _orig_popen
        os.system = _orig_system

        # Mark as unpatched
        _process_patched = False

        logger.info("Process execution monitoring unpatched")
        return True
    except Exception as e:
        logger.error(f"Failed to unpatch process execution monitoring: {e}")
        return False
