"""Tests for the base patcher module."""



from src.cylestio_monitor.patchers.base import BasePatcher


class TestBasePatcher(BasePatcher):
    """Test implementation of BasePatcher for testing."""

    def patch(self):
        """Test implementation of patch."""
        self.is_patched = True

    def unpatch(self):
        """Test implementation of unpatch."""
        self.is_patched = False


def test_base_patcher_init():
    """Test the BasePatcher initialization."""
    # Create a config dictionary
    config = {"test_key": "test_value"}

    # Create a BasePatcher instance
    patcher = TestBasePatcher(config)

    # Check that the config is set correctly
    assert patcher.config == config
    assert patcher.is_patched is False


def test_base_patcher_patch():
    """Test the patch method of BasePatcher."""
    # Create a BasePatcher instance
    patcher = TestBasePatcher()

    # Patch the method
    patcher.patch()

    # Check that is_patched is set to True
    assert patcher.is_patched is True


def test_base_patcher_unpatch():
    """Test the unpatch method of BasePatcher."""
    # Create a BasePatcher instance
    patcher = TestBasePatcher()

    # Set is_patched to True
    patcher.is_patched = True

    # Unpatch the method
    patcher.unpatch()

    # Check that is_patched is set to False
    assert patcher.is_patched is False
