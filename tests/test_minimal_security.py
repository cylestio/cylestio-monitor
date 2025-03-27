"""Minimal security test to verify imports."""

import pytest

def test_import_new_structure():
    """Test that we can import from the new module structure."""
    try:
        from cylestio_monitor.events.processing.security import (
            contains_dangerous,
            contains_suspicious,
            normalize_text,
        )
        assert callable(contains_dangerous)
        assert callable(contains_suspicious)
        assert callable(normalize_text)
        print("Successfully imported security functions from new path")
    except ImportError as e:
        pytest.fail(f"Failed to import from new module structure: {e}")
        
    # Optional: If this succeeds, the old structure should not exist
    try:
        import cylestio_monitor.events_processor
        pytest.fail("Old module structure still exists, which should have been removed")
    except ImportError:
        # This is expected - the old module should be gone
        pass 