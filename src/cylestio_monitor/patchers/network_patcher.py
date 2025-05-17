"""
Network connection patching module for Cylestio Monitor.

This module provides patching for socket connections to detect potential C2 or data exfiltration.
"""

import logging

logger = logging.getLogger(__name__)

# Keep track of patching status
_network_patched = False


def patch_network_monitoring(enable_detection: bool = True) -> bool:
    """
    Apply network connection monitoring patches.

    Args:
        enable_detection: Whether to enable network detection rules

    Returns:
        bool: True if successful, False otherwise
    """
    global _network_patched

    if _network_patched:
        logger.info("Network connection monitoring already enabled")
        return True

    try:
        # Import the network monitoring module
        from cylestio_monitor._sensors.network import initialize

        # Import the network detection module to enable/disable rules
        try:
            from cylestio_monitor._sensors.network import enable_network_detection

            # Set network detection according to configuration
            enable_network_detection(enable_detection)

            if enable_detection:
                logger.info("Network detection rules enabled")
            else:
                logger.info("Network detection rules disabled")
        except ImportError:
            logger.warning("Could not configure network detection")

        # Initialize network monitoring
        initialize()

        # Mark as patched
        _network_patched = True

        return True
    except Exception as e:
        logger.error(f"Failed to patch network connection monitoring: {e}")
        return False


def unpatch_network_monitoring() -> bool:
    """
    Remove network connection monitoring patches.

    Returns:
        bool: True if successful, False otherwise
    """
    global _network_patched

    if not _network_patched:
        return True

    try:
        # Import the unpatch function
        import socket
        from cylestio_monitor._sensors.network import _orig_connect, _orig_connect_ex

        # Restore original functions
        socket.socket.connect = _orig_connect
        socket.socket.connect_ex = _orig_connect_ex

        # Mark as unpatched
        _network_patched = False

        logger.info("Network connection monitoring unpatched")
        return True
    except Exception as e:
        logger.error(f"Failed to unpatch network connection monitoring: {e}")
        return False 