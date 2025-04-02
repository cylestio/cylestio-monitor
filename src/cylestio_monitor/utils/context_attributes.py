"""
Contextual Attributes for Telemetry Events.

This module provides utilities to automatically capture and add contextual information
about the runtime environment to telemetry events.
"""

import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Dict, List, Optional


def get_environment_context() -> Dict[str, str]:
    """Get information about the runtime environment.

    Returns:
        Dict[str, str]: Dictionary containing environment context information
    """
    context = {
        "os.type": platform.system(),
        "os.version": platform.version(),
        "python.version": sys.version.split()[0],
        "machine.type": platform.machine(),
    }

    return context


def get_library_versions(libraries: Optional[List[str]] = None) -> Dict[str, str]:
    """Get versions of specified Python libraries.

    Args:
        libraries: List of library names to check. If None, checks for common AI libraries.

    Returns:
        Dict[str, str]: Dictionary mapping library names to their versions
    """
    if libraries is None:
        libraries = [
            "anthropic",
            "langchain",
            "langchain-core",
            "langgraph",
            "mcp",
            "openai",
            "llama-index",
            "transformers",
        ]

    versions = {}
    for package in libraries:
        try:
            version_str = version(package)
            versions[f"library.{package}.version"] = version_str
        except PackageNotFoundError:
            pass

    return versions


def get_runtime_context() -> Dict[str, str]:
    """Get information about the Python runtime.

    Returns:
        Dict[str, str]: Dictionary containing Python runtime information
    """
    context = {
        "python.implementation": platform.python_implementation(),
        "python.compiler": platform.python_compiler(),
    }

    # Add environment variables (safely)
    for env_var in ["PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"]:
        if env_var in os.environ:
            context[f"env.{env_var.lower()}"] = os.environ[env_var]

    return context


def get_all_context() -> Dict[str, str]:
    """Get all available context information.

    Returns:
        Dict[str, str]: Combined dictionary of all context information
    """
    context = {}
    context.update(get_environment_context())
    context.update(get_library_versions())
    context.update(get_runtime_context())
    return context
