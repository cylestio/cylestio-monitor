# Cylestio Monitor Auto-Patching System

The Cylestio Monitor patching system provides automatic instrumentation for various LLM libraries and frameworks. This document explains how the auto-patching system works and how to extend it for new libraries.

## Supported Libraries

Cylestio Monitor automatically detects and patches the following libraries:

- **Anthropic Claude**: All Anthropic client instances are automatically detected and patched for monitoring
- **LangChain**: Automatically detected and patched when imported
- **LangGraph**: Automatically detected and patched when imported
- **MCP** (Machine Conversation Protocol): Automatically patched when detected

## How Auto-Patching Works

The auto-patching system uses a combination of techniques:

1. **Import-Time Patching**: Patches applied when a module is imported
2. **Constructor Patching**: Patches applied when new instances are created
3. **Framework Detection**: Automatic detection of frameworks in the environment

### Example: Anthropic Auto-Patching

The Anthropic auto-patching mechanism works by patching the `__init__` method of the `Anthropic` class:

```python
@functools.wraps(original_init)
def patched_init(self, *args, **kwargs):
    # Call original init
    original_init(self, *args, **kwargs)
    
    # Automatically patch this instance
    patcher = AnthropicPatcher(client=self)
    patcher.patch()
```

This ensures that any new Anthropic client instances are automatically patched without requiring explicit configuration.

## Usage

### Basic Usage

In most cases, you don't need to do anything special to use auto-patching:

```python
from cylestio_monitor import enable_monitoring

# Enable monitoring at the start of your application
enable_monitoring(agent_id="my-agent")

# Import supported libraries after enabling monitoring
from anthropic import Anthropic
client = Anthropic()  # This instance is automatically monitored

# Your application code...
```

### Backward Compatibility

For backward compatibility, the `llm_client` parameter is still supported:

```python
from anthropic import Anthropic
client = Anthropic()

# Both approaches work, but passing llm_client is now optional
enable_monitoring(agent_id="my-agent", llm_client=client)
```

## Extending for New Libraries

To add support for a new library, create a new patcher following these steps:

1. Create a new patcher class that extends `BasePatcher`
2. Implement the `patch()` and `unpatch()` methods for instance patching
3. Implement the class methods `patch_module()` and `unpatch_module()` for global patching
4. Add detection logic in the `enable_monitoring()` function

### Example Patcher Template

```python
from .base import BasePatcher

class NewLibraryPatcher(BasePatcher):
    """Patcher for New Library."""
    
    def __init__(self, client=None, config=None):
        super().__init__(config)
        self.client = client
        self.original_funcs = {}
    
    def patch(self):
        """Patch a specific instance."""
        if not self.client:
            return
            
        # Store original method
        original_method = self.client.some_method
        self.original_funcs["some_method"] = original_method
        
        # Create wrapped method
        def wrapped_method(*args, **kwargs):
            # Log before call
            # Call original method
            result = original_method(*args, **kwargs)
            # Log after call
            return result
            
        # Replace method
        self.client.some_method = wrapped_method
        self.is_patched = True
    
    def unpatch(self):
        """Unpatch a specific instance."""
        if not self.is_patched:
            return
            
        # Restore original method
        self.client.some_method = self.original_funcs["some_method"]
        self.is_patched = False
    
    @classmethod
    def patch_module(cls):
        """Apply global patches to the module."""
        # Import the library (safely)
        try:
            import new_library
            
            # Patch the constructor
            original_init = new_library.Client.__init__
            
            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                # Patch this instance
                patcher = cls(client=self)
                patcher.patch()
                
            # Apply the patch
            new_library.Client.__init__ = patched_init
            
        except ImportError:
            # Library not available
            pass
            
    @classmethod
    def unpatch_module(cls):
        """Remove global patches from the module."""
        # Restore original methods
        try:
            import new_library
            # Restore the constructor
            if hasattr(cls, "_original_init"):
                new_library.Client.__init__ = cls._original_init
        except ImportError:
            pass
```

## Troubleshooting

If auto-patching isn't working as expected:

1. Make sure you call `enable_monitoring()` before importing the libraries you want to monitor
2. Check if the library you're using is supported for auto-patching
3. Enable debug logs by setting the debug level: `enable_monitoring(agent_id="my-agent", config={"debug_level": "DEBUG"})`
4. For older code that explicitly passes clients, the explicit patching will take precedence 