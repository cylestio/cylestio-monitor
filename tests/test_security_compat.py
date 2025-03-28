"""
Simple compatibility test to verify security functions work.
This file works with both old and new module structures.
"""

import pytest
import sys


def test_security_compatibility():
    """Test that we can import and use security functions."""
    # Try new path first
    try:
        from cylestio_monitor.events.processing.security import (
            contains_dangerous,
            contains_suspicious,
            normalize_text,
        )
        print("Successfully imported from new path: cylestio_monitor.events.processing.security")
        module_path = "new"
    except ImportError as e:
        print(f"Failed to import from new path: {e}")
        # Fall back to old path
        try:
            from cylestio_monitor.events_processor import (
                contains_dangerous,
                contains_suspicious,
                normalize_text,
            )
            print("Successfully imported from old path: cylestio_monitor.events_processor")
            module_path = "old"
        except ImportError as e:
            print(f"Failed to import from old path: {e}")
            print("Available Python paths:", sys.path)
            print("Available cylestio_monitor modules:", [m for m in sys.modules.keys() if "cylestio" in m])
            pytest.fail("Could not import security functions from either path")
            return
    
    # Print which module we're using
    print(f"Using module from {module_path} path")
            
    # Test basic functionality
    assert contains_dangerous("DROP TABLE users") is True
    assert contains_suspicious("HACK the system") is True
    assert normalize_text("Test") == "TEST" 