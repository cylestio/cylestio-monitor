"""
Tests for the network connection monitoring sensor.
"""
import socket
import unittest
import os
from unittest.mock import patch, MagicMock

from cylestio_monitor._sensors.network import (
    _span_connect, _span_connect_ex, initialize, _get_ip_port,
    _categorize_connection, _determine_severity, _is_own_endpoint, _setup_own_endpoints
)
from cylestio_monitor.patchers.network_patcher import (
    patch_network_monitoring, unpatch_network_monitoring
)


class TestNetworkSensor(unittest.TestCase):
    """Test cases for network connection monitoring."""

    def setUp(self):
        """Set up test fixtures, patch event logging."""
        # Save original functions
        self.orig_connect = socket.socket.connect
        self.orig_connect_ex = socket.socket.connect_ex

        # Patch event logging
        self.log_event_patcher = patch('cylestio_monitor._sensors.network.log_event')
        self.mock_log_event = self.log_event_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original functions
        socket.socket.connect = self.orig_connect
        socket.socket.connect_ex = self.orig_connect_ex

        # Stop patchers
        self.log_event_patcher.stop()

    def test_initialize(self):
        """Test initialization of the network monitoring sensor."""
        # Initialize the sensor
        initialize()

        # Verify that connect and connect_ex are patched
        self.assertEqual(socket.socket.connect, _span_connect)
        self.assertEqual(socket.socket.connect_ex, _span_connect_ex)

    def test_get_ip_port(self):
        """Test the _get_ip_port function."""
        # Test with tuple
        host, port = _get_ip_port(("example.com", 443))
        self.assertEqual(host, "example.com")
        self.assertEqual(port, 443)

        # Test with object that has ip and port attributes
        class DummyAddress:
            def __init__(self):
                self.ip = "192.168.1.1"
                self.port = 8080

        dummy_addr = DummyAddress()
        host, port = _get_ip_port(dummy_addr)
        self.assertEqual(host, "192.168.1.1")
        self.assertEqual(port, 8080)

        # Test with string
        host, port = _get_ip_port("unknown_format")
        self.assertEqual(host, "unknown_format")
        self.assertEqual(port, 0)

    def test_categorize_connection(self):
        """Test the _categorize_connection function."""
        # Test C2 port
        category = _categorize_connection("evil.com", 4444)
        self.assertEqual(category, "potential_c2")

        # Test exfiltration port
        category = _categorize_connection("ftp.example.com", 21)
        self.assertEqual(category, "potential_exfiltration")

        # Test direct IP
        category = _categorize_connection("192.168.1.1", 80)
        self.assertEqual(category, "direct_ip")

        # Test normal connection
        category = _categorize_connection("example.com", 443)
        self.assertEqual(category, "outbound_connection")

    def test_determine_severity(self):
        """Test the _determine_severity function."""
        # Test localhost (should be low regardless of port)
        severity = _determine_severity("localhost", 4444, True)
        self.assertEqual(severity, "low")

        # Test C2 port
        severity = _determine_severity("evil.com", 4444, False)
        self.assertEqual(severity, "critical")

        # Test exfiltration port
        severity = _determine_severity("ftp.example.com", 21, False)
        self.assertEqual(severity, "high")

        # Test direct IP
        severity = _determine_severity("192.168.1.1", 80, False)
        self.assertEqual(severity, "medium")

        # Test standard web port
        severity = _determine_severity("example.com", 443, False)
        self.assertEqual(severity, "low")

    @patch('socket.socket._real_connect', autospec=True)
    def test_span_connect(self, mock_real_connect):
        """Test the span_connect function."""
        # Initialize the sensor
        initialize()

        # Create a socket to test
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Setup for mocking the real connect function
        mock_real_connect.return_value = None

        # Call socket.connect to trigger our patched version
        try:
            # We expect this to raise an error since we're mocking _real_connect
            # But it should still call our logging function
            sock.connect(("example.com", 443))
        except AttributeError:
            pass  # This is expected due to our mocking

        # Verify that log_event was called
        self.assertEqual(self.mock_log_event.call_count, 1)

        # Check the call arguments
        args, kwargs = self.mock_log_event.call_args
        self.assertEqual(args[0], "net.conn_open")
        self.assertEqual(kwargs["level"], "INFO")
        self.assertIn("net.transport", kwargs["attributes"])
        self.assertIn("net.dst.ip", kwargs["attributes"])
        self.assertIn("net.dst.port", kwargs["attributes"])
        self.assertIn("net.is_local", kwargs["attributes"])
        self.assertIn("session.id", kwargs["attributes"])

    def test_patcher_functions(self):
        """Test the patch_network_monitoring and unpatch_network_monitoring functions."""
        # Patch network monitoring
        result = patch_network_monitoring()
        self.assertTrue(result)

        # Verify that connect and connect_ex are patched
        self.assertEqual(socket.socket.connect, _span_connect)
        self.assertEqual(socket.socket.connect_ex, _span_connect_ex)

        # Unpatch network monitoring
        result = unpatch_network_monitoring()
        self.assertTrue(result)

        # Verify that connect and connect_ex are restored
        self.assertEqual(socket.socket.connect, self.orig_connect)
        self.assertEqual(socket.socket.connect_ex, self.orig_connect_ex)

    @patch('cylestio_monitor.config.ConfigManager')
    def test_own_endpoint_setup(self, mock_config_manager):
        """Test that our own endpoints are correctly detected and filtered."""
        # Mock environment and config
        with patch.dict(os.environ, {"CYLESTIO_TELEMETRY_ENDPOINT": "http://telemetry.mydomain.com:8443"}, clear=True):
            # Force reset of endpoints
            from cylestio_monitor._sensors.network import _OWN_ENDPOINTS
            _OWN_ENDPOINTS.clear()

            # Run setup
            _setup_own_endpoints()

            # Check that our endpoint was added to the exclusion list
            self.assertTrue(_is_own_endpoint("telemetry.mydomain.com", 8443))
            # Check that alternate ports were added
            self.assertTrue(_is_own_endpoint("telemetry.mydomain.com", 80))
            self.assertTrue(_is_own_endpoint("telemetry.mydomain.com", 443))

        # Test default endpoint
        with patch.dict(os.environ, {}, clear=True):
            mock_instance = MagicMock()
            mock_instance.get.return_value = None
            mock_config_manager.return_value = mock_instance

            # Force reset of endpoints
            _OWN_ENDPOINTS.clear()

            # Run setup
            _setup_own_endpoints()

            # Check that default endpoint was added
            self.assertTrue(_is_own_endpoint("127.0.0.1", 8000))

        # Test config-based endpoint
        with patch.dict(os.environ, {}, clear=True):
            mock_instance = MagicMock()
            mock_instance.get.return_value = "https://api.mycustom.com:9000"
            mock_config_manager.return_value = mock_instance

            # Force reset of endpoints
            _OWN_ENDPOINTS.clear()

            # Run setup
            _setup_own_endpoints()

            # Check that custom endpoint was added
            self.assertTrue(_is_own_endpoint("api.mycustom.com", 9000))

    @patch('cylestio_monitor._sensors.network._orig_connect')
    def test_span_connect_skip_own_endpoint(self, mock_orig_connect):
        """Test that connections to our own endpoint are not monitored."""
        # Set up our own endpoint
        with patch.dict(os.environ, {"CYLESTIO_TELEMETRY_ENDPOINT": "http://api.cylestio.com:8000"}, clear=True):
            # Force reset of endpoints
            from cylestio_monitor._sensors.network import _OWN_ENDPOINTS
            _OWN_ENDPOINTS.clear()
            _setup_own_endpoints()

            # Create a socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Mock the original connect
            mock_orig_connect.return_value = None

            # Connect to our own endpoint
            _span_connect(sock, ("api.cylestio.com", 8000))

            # Verify original connect was called
            mock_orig_connect.assert_called_once()

            # Verify log_event was NOT called (no monitoring for our own endpoint)
            self.mock_log_event.assert_not_called()


if __name__ == '__main__':
    unittest.main()
