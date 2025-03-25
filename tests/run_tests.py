#!/usr/bin/env python3
"""
Isolated test runner for Cylestio Monitor

This script provides an isolated environment for running tests
with comprehensive mocking of dependencies to avoid issues with
LangChain and DB-related modules.
"""

import os
import sys
import unittest.mock
import types
import subprocess
import importlib
import argparse


def setup_python_path():
    """Set up Python path to include the package."""
    print("Setting up Python path...")
    
    # Ensure the root directory is in the Python path for proper imports
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        print(f"Adding {root_dir} to Python path")
        sys.path.insert(0, root_dir)
    
    # Also add src to path for direct imports
    src_dir = os.path.join(root_dir, 'src')
    if src_dir not in sys.path:
        print(f"Adding {src_dir} to Python path")
        sys.path.insert(0, src_dir)
        
    print(f"Python path: {sys.path}")


def setup_mock_modules():
    """Set up comprehensive mocks for problematic modules."""
    print("Setting up mocks for external dependencies...")
    
    # Mock DB-related modules
    sys.modules['sqlalchemy'] = unittest.mock.MagicMock()
    sys.modules['sqlite3'] = unittest.mock.MagicMock()
    
    # Create comprehensive LangChain mock environment
    mocked_modules = [
        # LangChain
        'langchain',
        'langchain.callbacks',
        'langchain.callbacks.base',
        'langchain.callbacks.manager',
        'langchain.chains',
        'langchain.chains.base',
        'langchain.llms',
        'langchain.llms.base',
        'langchain.chat_models',
        'langchain.chat_models.base',
        'langchain.schema',
        
        # LangChain Core
        'langchain_core',
        'langchain_core.callbacks',
        'langchain_core.callbacks.base',
        'langchain_core.callbacks.manager',
        'langchain_core.messages',
        'langchain_core.outputs',
        'langchain_core.runnables',
        'langchain_core.runnables.base',
        'langchain_core.prompts',
        'langchain_core.chains',
        'langchain_core.language_models',
        'langchain_core.language_models.llms',
        'langchain_core.language_models.chat_models',
        'langchain_core.globals',
    ]
    
    # Create module mocks
    for module_name in mocked_modules:
        if module_name not in sys.modules:
            sys.modules[module_name] = types.ModuleType(module_name)
    
    # Set up basic classes for LangChain
    sys.modules['langchain.callbacks.base'].BaseCallbackHandler = type('BaseCallbackHandler', (), {})
    sys.modules['langchain.callbacks.manager'].CallbackManager = type('CallbackManager', (), {})
    sys.modules['langchain.chains.base'].Chain = type('Chain', (), {})
    sys.modules['langchain.llms.base'].BaseLLM = type('BaseLLM', (), {})
    sys.modules['langchain.chat_models.base'].BaseChatModel = type('BaseChatModel', (), {})
    sys.modules['langchain.schema'].BaseMessage = type('BaseMessage', (), {})
    sys.modules['langchain.schema'].LLMResult = type('LLMResult', (), {})
    
    # Set up basic classes for LangChain Core
    sys.modules['langchain_core.callbacks.base'].BaseCallbackHandler = type('BaseCallbackHandler', (), {})
    sys.modules['langchain_core.callbacks.manager'].CallbackManager = type('CallbackManager', (), {})
    sys.modules['langchain_core.messages'].BaseMessage = type('BaseMessage', (), {'content': ''})
    sys.modules['langchain_core.outputs'].LLMResult = type('LLMResult', (), {})
    sys.modules['langchain_core.runnables.base'].Runnable = type('Runnable', (), {})
    sys.modules['langchain_core.chains'].Chain = type('Chain', (), {})
    sys.modules['langchain_core.language_models.llms'].BaseLLM = type('BaseLLM', (), {})
    sys.modules['langchain_core.language_models.chat_models'].BaseChatModel = type('BaseChatModel', (), {})
    
    # Mock global callback managers
    sys.modules['langchain_core.globals'].get_callback_manager = unittest.mock.MagicMock()
    sys.modules['langchain_core.globals'].set_callback_manager = unittest.mock.MagicMock()
    
    print("Mock environment set up successfully")


def clean_pycache():
    """Remove Python cache files that might cause issues."""
    print("Cleaning Python cache files...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the virtual environment directory and .git directory
        if '.venv' in dirpath or '.git' in dirpath:
            continue
            
        # Remove __pycache__ directories
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            print(f"Removing {pycache_path}")
            try:
                for file in os.listdir(pycache_path):
                    os.remove(os.path.join(pycache_path, file))
                os.rmdir(pycache_path)
            except OSError as e:
                print(f"Could not remove directory {pycache_path}: {e}")
            dirnames.remove('__pycache__')
            
        # Remove .pyc files
        for filename in filenames:
            if filename.endswith('.pyc'):
                pyc_path = os.path.join(dirpath, filename)
                print(f"Removing {pyc_path}")
                try:
                    os.remove(pyc_path)
                except OSError as e:
                    print(f"Could not remove file {pyc_path}: {e}")
    
    # Remove pytest cache
    pytest_cache = os.path.join(root_dir, '.pytest_cache')
    if os.path.exists(pytest_cache):
        print(f"Removing {pytest_cache}")
        import shutil
        shutil.rmtree(pytest_cache, ignore_errors=True)
    
    print("Cache cleanup complete")


def run_tests():
    """Run the tests with pytest."""
    print("Running tests...")
    # Make sure we're in the root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    os.chdir(root_dir)
    
    # Ensure package is installed in development mode
    print("Ensuring package is installed in development mode...")
    subprocess.run(["pip", "install", "-e", "."])
    
    # Construct the pytest command
    pytest_args = ['pytest', '-v']
    
    # Add any arguments passed to this script
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    
    # Run pytest
    print(f"Running command: {' '.join(pytest_args)}")
    result = subprocess.run(pytest_args)
    return result.returncode


def main():
    """Main function to run the isolated tests."""
    parser = argparse.ArgumentParser(description='Run tests with comprehensive mocking')
    parser.add_argument('--no-clean', action='store_true', help='Skip cleaning cache files')
    parser.add_argument('--no-mocks', action='store_true', help='Skip setting up mocks')
    args, unknown_args = parser.parse_known_args()
    
    # Update sys.argv to only include unknown args for pytest
    sys.argv = [sys.argv[0]] + unknown_args
    
    if not args.no_clean:
        clean_pycache()
    
    # Always set up the Python path
    setup_python_path()
    
    if not args.no_mocks:
        setup_mock_modules()
    
    return run_tests()


if __name__ == "__main__":
    sys.exit(main()) 