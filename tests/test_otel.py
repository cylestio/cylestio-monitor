"""
Tests for the OpenTelemetry ID generation.
"""

import re
import unittest

from cylestio_monitor.utils.otel import generate_span_id, generate_trace_context, generate_trace_id


class TestOtelIdGeneration(unittest.TestCase):
    """Test case for OpenTelemetry ID generation."""

    def test_trace_id_format(self):
        """Test that generated trace IDs have the correct format."""
        trace_id = generate_trace_id()

        # Trace ID should be a 32-character hex string
        self.assertEqual(len(trace_id), 32)
        # Should match hexadecimal pattern
        self.assertTrue(re.match(r"^[0-9a-f]{32}$", trace_id))

    def test_span_id_format(self):
        """Test that generated span IDs have the correct format."""
        span_id = generate_span_id()

        # Span ID should be a 16-character hex string
        self.assertEqual(len(span_id), 16)
        # Should match hexadecimal pattern
        self.assertTrue(re.match(r"^[0-9a-f]{16}$", span_id))

    def test_generate_trace_context(self):
        """Test generating a complete trace context."""
        context = generate_trace_context()

        # Should have trace_id and span_id
        self.assertIn("trace_id", context)
        self.assertIn("span_id", context)
        self.assertIn("parent_span_id", context)

        # Parent span ID should be None if not provided
        self.assertIsNone(context["parent_span_id"])


if __name__ == "__main__":
    unittest.main()
