"""
Tests for the event utilities.
"""

import pytest
from datetime import datetime, timezone, timedelta
import re

from cylestio_monitor.utils.event_utils import (
    get_utc_timestamp, 
    format_timestamp, 
    parse_timestamp, 
    validate_iso8601,
    create_event_dict
)
from tests.utils.timestamp_validation import validate_timestamp_format


class TestTimestampUtilities:
    """Test suite for timestamp utility functions."""
    
    def test_get_utc_timestamp(self):
        """Test that get_utc_timestamp returns a timezone-aware UTC datetime."""
        dt = get_utc_timestamp()
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) == timedelta(0)
    
    def test_format_timestamp_none(self):
        """Test formatting with no input (current time)."""
        result = format_timestamp()
        # Check format: YYYY-MM-DDTHH:MM:SS.sssZ
        assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$', result)
        assert result.endswith('Z')
    
    def test_format_timestamp_datetime(self):
        """Test formatting with a datetime input."""
        dt = datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        assert result == '2023-09-15T14:30:45.123456Z'
    
    def test_format_timestamp_naive_datetime(self):
        """Test formatting with a naive datetime input."""
        dt = datetime(2023, 9, 15, 14, 30, 45, 123456)  # No tzinfo
        result = format_timestamp(dt)
        assert result == '2023-09-15T14:30:45.123456Z'
    
    def test_format_timestamp_other_timezone(self):
        """Test formatting with a datetime in another timezone."""
        # New York timezone (UTC-4 or UTC-5 depending on DST)
        est = timezone(timedelta(hours=-4))
        dt = datetime(2023, 9, 15, 10, 30, 45, 123456, tzinfo=est)
        result = format_timestamp(dt)
        # Should be converted to UTC (14:30:45)
        assert result == '2023-09-15T14:30:45.123456Z'
    
    def test_format_timestamp_string_z(self):
        """Test formatting with a string input with Z suffix."""
        result = format_timestamp("2023-09-15T14:30:45.123Z")
        assert result == '2023-09-15T14:30:45.123000Z'
    
    def test_format_timestamp_string_offset(self):
        """Test formatting with a string input with timezone offset."""
        result = format_timestamp("2023-09-15T10:30:45-04:00")
        assert result == '2023-09-15T14:30:45.000000Z'
    
    def test_format_timestamp_string_no_tz(self):
        """Test formatting with a string input with no timezone."""
        result = format_timestamp("2023-09-15T14:30:45")
        assert result == '2023-09-15T14:30:45.000000Z'
    
    def test_format_timestamp_invalid_string(self):
        """Test formatting with an invalid string input."""
        with pytest.raises(ValueError):
            format_timestamp("not a timestamp")
    
    def test_parse_timestamp_z(self):
        """Test parsing a timestamp with Z suffix."""
        dt = parse_timestamp("2023-09-15T14:30:45.123Z")
        assert dt.year == 2023
        assert dt.month == 9
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.microsecond == 123000
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) == timedelta(0)
    
    def test_parse_timestamp_offset(self):
        """Test parsing a timestamp with timezone offset."""
        dt = parse_timestamp("2023-09-15T10:30:45-04:00")
        assert dt.hour == 14  # Should be converted to UTC
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) == timedelta(0)
    
    def test_parse_timestamp_no_tz(self):
        """Test parsing a timestamp with no timezone."""
        dt = parse_timestamp("2023-09-15T14:30:45")
        assert dt.hour == 14
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) == timedelta(0)
    
    def test_parse_timestamp_invalid(self):
        """Test parsing an invalid timestamp."""
        with pytest.raises(ValueError):
            parse_timestamp("not a timestamp")
    
    def test_validate_iso8601_valid(self):
        """Test validation with valid ISO-8601 formats."""
        assert validate_iso8601("2023-09-15T14:30:45Z")
        assert validate_iso8601("2023-09-15T14:30:45.123Z")
        assert validate_iso8601("2023-09-15T14:30:45+00:00")
        assert validate_iso8601("2023-09-15T14:30:45-04:00")
    
    def test_validate_iso8601_invalid(self):
        """Test validation with invalid formats."""
        assert not validate_iso8601("2023-09-15 14:30:45")  # Missing T
        assert not validate_iso8601("2023/09/15T14:30:45Z")  # Wrong date separators
        assert not validate_iso8601("not a timestamp")
    
    def test_create_event_dict_basic(self):
        """Test basic event dictionary creation."""
        event = create_event_dict("test.event")
        assert event["name"] == "test.event"
        assert "timestamp" in event
        assert event["level"] == "INFO"
        assert "agent_id" in event
        assert event["attributes"] == {}
    
    def test_create_event_dict_custom_timestamp(self):
        """Test event with custom timestamp."""
        dt = datetime(2023, 9, 15, 14, 30, 45, tzinfo=timezone.utc)
        event = create_event_dict("test.event", timestamp=dt)
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
    
    def test_create_event_dict_string_timestamp(self):
        """Test event with string timestamp."""
        event = create_event_dict("test.event", timestamp="2023-09-15T14:30:45Z")
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
    
    def test_create_event_dict_full(self):
        """Test event with all fields."""
        event = create_event_dict(
            name="test.event",
            attributes={"key": "value"},
            level="ERROR",
            agent_id="test-agent",
            timestamp="2023-09-15T14:30:45Z",
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789"
        )
        assert event["name"] == "test.event"
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
        assert event["level"] == "ERROR"
        assert event["agent_id"] == "test-agent"
        assert event["attributes"] == {"key": "value"}
        assert event["trace_id"] == "trace123"
        assert event["span_id"] == "span456"
        assert event["parent_span_id"] == "parent789"
        
    # Additional timestamp validation tests
    
    def test_timestamp_edge_cases(self):
        """Test timestamp formatting with edge cases."""
        # Microseconds precision
        assert format_timestamp("2023-09-15T14:30:45.123456Z").endswith(".123456Z")
        
        # No microseconds should add them
        assert format_timestamp("2023-09-15T14:30:45Z").endswith(".000000Z")
        
        # Fractional seconds should be preserved
        assert format_timestamp("2023-09-15T14:30:45.5Z").endswith(".500000Z")
        
        # Future date
        future = datetime(2050, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert format_timestamp(future) == "2050-01-01T00:00:00.000000Z"
        
        # Past date
        past = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert format_timestamp(past) == "1970-01-01T00:00:00.000000Z"
    
    def test_validate_timestamp_format_validation(self):
        """Test the timestamp format validation function."""
        # Valid formats
        assert validate_timestamp_format("2023-09-15T14:30:45Z")
        assert validate_timestamp_format("2023-09-15T14:30:45.123Z")
        assert validate_timestamp_format("2023-09-15T14:30:45.123456Z")
        
        # Invalid formats
        assert not validate_timestamp_format("2023-09-15T14:30:45")  # No Z
        assert not validate_timestamp_format("2023-09-15T14:30:45+00:00")  # Wrong timezone format
        assert not validate_timestamp_format("2023-09-15 14:30:45Z")  # Missing T
        assert not validate_timestamp_format("not a timestamp")
    
    def test_all_outputs_are_utc_z(self):
        """Test that all timestamp output methods produce UTC with Z suffix."""
        # List of functions that produce timestamps
        dt = datetime(2023, 9, 15, 14, 30, 45, tzinfo=timezone.utc)
        non_utc_dt = datetime(2023, 9, 15, 10, 30, 45, 
                            tzinfo=timezone(timedelta(hours=-4)))
        
        # Test format_timestamp with various inputs
        assert format_timestamp().endswith("Z")
        assert format_timestamp(dt).endswith("Z")
        assert format_timestamp(non_utc_dt).endswith("Z")
        assert format_timestamp("2023-09-15T14:30:45").endswith("Z")
        assert format_timestamp("2023-09-15T14:30:45Z").endswith("Z")
        assert format_timestamp("2023-09-15T10:30:45-04:00").endswith("Z")
        
        # Test with event creation
        event = create_event_dict("test.event")
        assert event["timestamp"].endswith("Z")
        
        event = create_event_dict("test.event", timestamp=dt)
        assert event["timestamp"].endswith("Z")
        
        event = create_event_dict("test.event", timestamp=non_utc_dt)
        assert event["timestamp"].endswith("Z") 