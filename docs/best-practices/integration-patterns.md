# Integration Patterns

Cylestio Monitor can be integrated into your applications in various ways, depending on your specific requirements and architecture. This guide outlines common integration patterns and best practices for each.

## Basic Integration Patterns

### 1. Direct Integration

The simplest integration pattern is to directly integrate Cylestio Monitor into your application code:

```python
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

# Create your LLM client
client = Anthropic()

# Enable monitoring
enable_monitoring(
    agent_id="my_agent",
    llm_client=client
)

# Use your client as normal
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

**Best for**:
- Simple applications
- Single-service architectures
- Prototypes and proof-of-concepts

**Considerations**:
- Monitoring is tightly coupled to your application code
- Each service needs to enable monitoring separately
- Configuration changes require code changes

### 2. Middleware Integration

For web applications, you can implement Cylestio Monitor as middleware:

```python
# Flask example
from flask import Flask, request, g
from cylestio_monitor import enable_monitoring, log_event
from anthropic import Anthropic

app = Flask(__name__)

# Create and monitor the LLM client
client = Anthropic()
enable_monitoring(
    agent_id="web-app-agent",
    llm_client=client
)

@app.before_request
def before_request():
    # Store request start time
    g.start_time = time.time()
    
    # Log request start
    log_event(
        "http_request_start",
        {
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.user_agent.string
        },
        "API",
        "info"
    )

@app.after_request
def after_request(response):
    # Calculate request duration
    duration_ms = (time.time() - g.start_time) * 1000
    
    # Log request finish
    log_event(
        "http_request_finish",
        {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        },
        "API",
        "info"
    )
    
    return response

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('question')
    
    # Use the monitored LLM client
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": user_input}]
    )
    
    return {"answer": response.content[0].text}
```

**Best for**:
- Web applications
- APIs
- Services with HTTP endpoints

**Considerations**:
- Provides consistent monitoring across all endpoints
- Can capture HTTP-specific metrics
- May not capture internal operations that don't go through the middleware

### 3. Decorator Pattern

You can use decorators to selectively monitor specific functions:

```python
from cylestio_monitor.events_listener import monitor_call
from cylestio_monitor import log_event

# Define a decorator for monitoring
def monitor(channel="CUSTOM"):
    def decorator(func):
        return monitor_call(func, channel)
    return decorator

# Use the decorator on specific functions
@monitor(channel="BUSINESS_LOGIC")
def process_order(order_data):
    # Process the order
    order_id = create_order(order_data)
    
    # Log a business event
    log_event(
        "order_created",
        {
            "order_id": order_id,
            "customer_id": order_data["customer_id"],
            "amount": order_data["amount"]
        },
        "BUSINESS_LOGIC",
        "info"
    )
    
    return order_id
```

**Best for**:
- Selective monitoring of specific functions
- Complex applications with many functions
- Applications where you want fine-grained control over what is monitored

**Considerations**:
- Requires adding decorators to each function you want to monitor
- Provides more control over what is monitored
- Can be combined with other integration patterns

## Advanced Integration Patterns

### 1. Service Wrapper Pattern

For microservice architectures, you can create a service wrapper that handles monitoring:

```python
class LLMService:
    def __init__(self, agent_id):
        self.client = Anthropic()
        enable_monitoring(
            agent_id=agent_id,
            llm_client=self.client
        )
    
    def generate_response(self, prompt):
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            log_event(
                "llm_service_error",
                {"error": str(e), "prompt": prompt},
                "SERVICE",
                "error"
            )
            raise

# Usage
llm_service = LLMService(agent_id="order-processing-service")
response = llm_service.generate_response("Generate an order confirmation email")
```

**Best for**:
- Microservice architectures
- Applications with multiple LLM clients
- Services that need to be reused across multiple applications

**Considerations**:
- Encapsulates monitoring logic in a reusable service
- Provides a clean API for other services to use
- Can include additional functionality like caching, rate limiting, etc.

### 2. Aspect-Oriented Programming (AOP) Pattern

For more complex applications, you can use aspect-oriented programming to separate monitoring concerns:

```python
# Using a library like aspectlib for Python
import aspectlib

from cylestio_monitor import log_event

@aspectlib.Aspect
def monitoring_aspect(*args, **kwargs):
    # Before the function call
    start_time = time.time()
    
    try:
        # Call the original function
        result = yield aspectlib.Proceed
        
        # After the function call
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the successful call
        log_event(
            "function_call",
            {
                "function": aspectlib.get_function_name(),
                "args": str(args),
                "kwargs": str(kwargs),
                "duration_ms": duration_ms,
                "success": True
            },
            "AOP",
            "info"
        )
        
        return result
    except Exception as e:
        # Log the failed call
        duration_ms = (time.time() - start_time) * 1000
        
        log_event(
            "function_call_error",
            {
                "function": aspectlib.get_function_name(),
                "args": str(args),
                "kwargs": str(kwargs),
                "duration_ms": duration_ms,
                "error": str(e),
                "success": False
            },
            "AOP",
            "error"
        )
        
        raise

# Apply the aspect to specific functions or classes
aspectlib.weave(MyClass.important_method, monitoring_aspect)
```

**Best for**:
- Complex applications with many cross-cutting concerns
- Applications where you want to separate monitoring logic from business logic
- Large codebases with many developers

**Considerations**:
- Requires additional libraries for AOP support
- Provides a clean separation of concerns
- Can be more complex to set up and maintain

### 3. Proxy Pattern

For applications that need to monitor external services, you can use a proxy pattern:

```python
class LLMClientProxy:
    def __init__(self, agent_id, real_client=None):
        self.agent_id = agent_id
        self.real_client = real_client or Anthropic()
        
        # Enable monitoring for the real client
        enable_monitoring(
            agent_id=agent_id,
            llm_client=self.real_client
        )
    
    def __getattr__(self, name):
        # Get the attribute from the real client
        attr = getattr(self.real_client, name)
        
        # If it's a callable, wrap it with monitoring
        if callable(attr):
            def wrapper(*args, **kwargs):
                # Log the call
                log_event(
                    f"proxy_call_{name}",
                    {"args": str(args), "kwargs": str(kwargs)},
                    "PROXY",
                    "info"
                )
                
                # Call the real method
                return attr(*args, **kwargs)
            
            return wrapper
        
        # Otherwise, return the attribute as is
        return attr

# Usage
proxy_client = LLMClientProxy(agent_id="proxy-agent")
response = proxy_client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
```

**Best for**:
- Applications that need to monitor external services
- Applications that need to add functionality to existing clients
- Testing and debugging

**Considerations**:
- Provides a transparent way to add monitoring to existing clients
- Can be used to add other functionality like caching, rate limiting, etc.
- May not work with all types of clients

## Integration with Frameworks

### 1. FastAPI Integration

```python
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from cylestio_monitor import log_event, enable_monitoring
from anthropic import Anthropic

app = FastAPI()

# Create and monitor the LLM client
client = Anthropic()
enable_monitoring(
    agent_id="fastapi-agent",
    llm_client=client
)

# Monitoring middleware
class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Store request start time
        start_time = time.time()
        
        # Log request start
        log_event(
            "http_request_start",
            {
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host
            },
            "API",
            "info"
        )
        
        # Process the request
        response = await call_next(request)
        
        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request finish
        log_event(
            "http_request_finish",
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms
            },
            "API",
            "info"
        )
        
        return response

# Add the middleware
app.add_middleware(MonitoringMiddleware)

# Define routes
@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("question")
    
    # Use the monitored LLM client
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": user_input}]
    )
    
    return {"answer": response.content[0].text}
```

### 2. Django Integration

```python
# In middleware.py
from django.utils.deprecation import MiddlewareMixin
from cylestio_monitor import log_event
import time

class MonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Store request start time
        request.start_time = time.time()
        
        # Log request start
        log_event(
            "http_request_start",
            {
                "method": request.method,
                "path": request.path,
                "user": str(request.user) if request.user.is_authenticated else "anonymous"
            },
            "API",
            "info"
        )
        
        return None
    
    def process_response(self, request, response):
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration_ms = (time.time() - request.start_time) * 1000
            
            # Log request finish
            log_event(
                "http_request_finish",
                {
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                },
                "API",
                "info"
            )
        
        return response

# In settings.py
MIDDLEWARE = [
    # ... other middleware
    'myapp.middleware.MonitoringMiddleware',
]

# In apps.py
from django.apps import AppConfig
from cylestio_monitor import enable_monitoring
from anthropic import Anthropic

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        # Create and monitor the LLM client
        client = Anthropic()
        enable_monitoring(
            agent_id="django-agent",
            llm_client=client
        )
        
        # Store the client for use in views
        from django.conf import settings
        settings.LLM_CLIENT = client
```

## Best Practices for Integration

### 1. Use Descriptive Agent IDs

Use descriptive agent IDs that include information about the application, environment, and purpose:

```python
# Good
enable_monitoring(agent_id="order-processing-service-production")

# Bad
enable_monitoring(agent_id="agent1")
```

### 2. Implement Proper Error Handling

Ensure that monitoring doesn't interfere with your application's normal operation:

```python
try:
    # Enable monitoring
    enable_monitoring(
        agent_id="my-agent",
        llm_client=client
    )
except Exception as e:
    # Log the error but continue without monitoring
    print(f"Failed to enable monitoring: {e}")
```

### 3. Use Environment-Specific Configuration

Use environment-specific configuration to adjust monitoring settings:

```python
import os

# Get environment-specific settings
agent_id = f"my-agent-{os.environ.get('ENVIRONMENT', 'development')}"
log_file = os.environ.get('MONITORING_LOG_FILE')
debug_level = os.environ.get('MONITORING_DEBUG_LEVEL', 'INFO')

# Enable monitoring with environment-specific settings
enable_monitoring(
    agent_id=agent_id,
    llm_client=client,
    log_file=log_file,
    debug_level=debug_level
)
```

### 4. Implement Graceful Shutdown

Ensure that monitoring is properly disabled when your application shuts down:

```python
import atexit
from cylestio_monitor import disable_monitoring

# Register the disable_monitoring function to be called on exit
atexit.register(disable_monitoring)
```

### 5. Monitor the Monitor

Implement monitoring for the monitoring system itself:

```python
import time
from cylestio_monitor import enable_monitoring, log_event

# Time how long it takes to enable monitoring
start_time = time.time()
enable_monitoring(agent_id="my-agent")
enable_time = time.time() - start_time

# Log the monitoring initialization time
log_event(
    "monitoring_initialized",
    {"duration_ms": enable_time * 1000},
    "META",
    "info"
)
```

## Conclusion

Choosing the right integration pattern depends on your specific requirements, architecture, and constraints. By following these best practices and patterns, you can effectively integrate Cylestio Monitor into your applications and gain valuable insights into your AI agents' behavior. 