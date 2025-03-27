"""
Simple compatibility test to verify security functions work.
This file works with both old and new module structures.
"""

import pytest


def test_security_compatibility():
    """Test that we can import and use security functions."""
    # Try new path first
    try:
        from cylestio_monitor.events.processing.security import (
            contains_dangerous,
            contains_suspicious,
            normalize_text,
        )
        # Log success with new path
        print("Successfully imported from new path: cylestio_monitor.events.processing.security")
    except ImportError:
        # Fall back to old path
        try:
            from cylestio_monitor.events_processor import (
                contains_dangerous,
                contains_suspicious,
                normalize_text,
            )
            # Log success with old path
            print("Successfully imported from old path: cylestio_monitor.events_processor")
        except ImportError:
            pytest.fail("Could not import security functions from either path")
            return
            
    # Test basic functionality
    assert contains_dangerous("DROP TABLE users") is True
    assert contains_suspicious("HACK the system") is True
    assert normalize_text("Test") == "TEST" 