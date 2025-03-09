import pytest
from cylestio_monitor import enable_monitoring

def test_enable_monitoring_basic():
    # Just ensure it doesn't crash
    enable_monitoring(mcp_enabled=False)
    assert True

test_enable_monitoring_basic()