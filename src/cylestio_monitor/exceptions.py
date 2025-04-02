"""Exceptions for the cylestio_monitor package."""


class ApiError(Exception):
    """Error when interacting with Cylestio API."""

    pass


class MonitoringError(Exception):
    """Base exception for monitoring errors."""

    pass
