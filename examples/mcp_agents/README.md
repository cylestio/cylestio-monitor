# MCP Agent Examples

This directory contains example implementations of agents using the Model Context Protocol (MCP) with Cylestio Monitor integration.

## Examples

### 1. Weather Agent (`weather_agent.py`)

A simple weather agent that demonstrates:
- Basic MCP server and client setup
- Integration with external API (OpenWeatherMap)
- Query processing and response generation
- Input validation and error handling
- Monitoring of agent interactions

To run the weather agent:

1. Get an API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Set your API key in `weather_agent.py`:
   ```python
   WEATHER_API_KEY = "your_api_key_here"
   ```
3. Run the example:
   ```bash
   python weather_agent.py
   ```

The example will run several test queries, including:
- Normal weather queries for different cities
- XSS attempt in city name
- SQL injection attempt in city name
- Invalid queries

### 2. Calculator Agent (`calculator_agent.py`)

A secure calculator agent that demonstrates:
- Input validation and sanitization
- Security monitoring for dangerous expressions
- Safe expression evaluation
- Detection and logging of security violations

To run the calculator agent:

```bash
python calculator_agent.py
```

The example will test various expressions:
- Valid mathematical expressions
- Attempts to use dangerous functions
- Attempts to import modules
- Syntax errors
- Large computations

## Features Demonstrated

1. **Security**
   - Input validation and sanitization
   - Detection of dangerous patterns
   - Prevention of code injection
   - Security violation logging
   - Rate limiting and resource usage monitoring

2. **Monitoring**
   - Request/response logging
   - Error tracking
   - Performance metrics
   - Security incident reporting
   - Usage statistics

3. **Error Handling**
   - Input validation errors
   - API errors
   - Syntax errors
   - Resource limit errors
   - Security violations

4. **MCP Integration**
   - Context management
   - Message handling
   - Metadata tracking
   - Usage statistics
   - Error reporting

## Running the Examples

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run the examples individually:
   ```bash
   # Run weather agent
   python examples/mcp_agents/weather_agent.py

   # Run calculator agent
   python examples/mcp_agents/calculator_agent.py
   ```

3. Check the output for:
   - Agent responses
   - Usage statistics
   - Security reports
   - Monitoring summaries

## Security Notes

These examples demonstrate security best practices:
- Input validation and sanitization
- Prevention of code injection
- Resource usage limits
- Security monitoring and logging
- Safe evaluation of expressions

However, they are intended for demonstration purposes. In a production environment, you should:
- Use proper API key management
- Implement rate limiting
- Add additional security measures
- Use proper logging and monitoring
- Regularly update dependencies 