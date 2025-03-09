"""Example of a calculator agent using MCP with monitoring.

This example demonstrates:
1. Setting up an agent with MCP
2. Integrating Cylestio Monitor for monitoring
3. Handling calculations with security validation
4. Monitoring agent interactions
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

from mcp import ClientSession, Context, Message
from cylestio_monitor import monitor

class CalculatorAgent:
    """Calculator agent with security validation."""
    
    # Whitelist of allowed operators and functions
    ALLOWED_OPERATORS = {'+', '-', '*', '/', '**', '(', ')', '.'}
    ALLOWED_FUNCTIONS = {'sum', 'min', 'max', 'abs', 'round'}
    
    # Regex for basic number validation
    NUMBER_PATTERN = re.compile(r'^-?\d*\.?\d+$')
    
    def __init__(self):
        """Initialize calculator agent."""
        self.security_violations: List[Dict[str, Any]] = []
        self.mcp_client = ClientSession(base_url="http://localhost:8000")
        
    def validate_token(self, token: str) -> bool:
        """Validate a single token in the expression.
        
        Args:
            token: Expression token
            
        Returns:
            True if token is valid
        """
        # Check if token is a number
        if self.NUMBER_PATTERN.match(token):
            return True
            
        # Check if token is an allowed operator
        if token in self.ALLOWED_OPERATORS:
            return True
            
        # Check if token is an allowed function
        if token in self.ALLOWED_FUNCTIONS:
            return True
            
        return False
        
    def validate_expression(self, expression: str) -> bool:
        """Validate a mathematical expression.
        
        Args:
            expression: Math expression to validate
            
        Returns:
            True if expression is valid
        """
        # Remove whitespace
        expression = expression.replace(' ', '')
        
        # Tokenize expression
        tokens = re.findall(r'[\d.]+|[+\-*/()]+|[a-zA-Z]+', expression)
        
        # Validate each token
        for token in tokens:
            if not self.validate_token(token):
                self.security_violations.append({
                    'timestamp': datetime.now().isoformat(),
                    'expression': expression,
                    'invalid_token': token,
                    'violation_type': 'invalid_token'
                })
                return False
                
        # Check for dangerous patterns
        dangerous_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'import\s+',
            r'__[a-zA-Z]+__',  # Dunder methods
            r'subprocess',
            r'os\.',
            r'sys\.',
            r'open\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                self.security_violations.append({
                    'timestamp': datetime.now().isoformat(),
                    'expression': expression,
                    'pattern': pattern,
                    'violation_type': 'dangerous_pattern'
                })
                return False
                
        return True
        
    def safe_eval(self, expression: str) -> Union[float, str]:
        """Safely evaluate a mathematical expression.
        
        Args:
            expression: Math expression to evaluate
            
        Returns:
            Result of evaluation or error message
        """
        try:
            # Validate expression
            if not self.validate_expression(expression):
                return "Invalid or potentially dangerous expression"
                
            # Create safe evaluation environment
            safe_dict = {
                'abs': abs,
                'max': max,
                'min': min,
                'sum': sum,
                'round': round
            }
            
            # Evaluate expression in safe environment
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            if isinstance(result, (int, float)):
                return float(result)
            else:
                return "Invalid result type"
                
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
            
    def get_security_report(self) -> Dict[str, Any]:
        """Get security violation report.
        
        Returns:
            Security report dictionary
        """
        return {
            'total_violations': len(self.security_violations),
            'violations': self.security_violations
        }
        
    async def process_expression(self, expression: str) -> str:
        """Process a mathematical expression.
        
        Args:
            expression: Expression to evaluate
            
        Returns:
            Result string
        """
        # Create MCP context
        context = Context(
            messages=[
                Message(role="user", content=expression)
            ],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "client_id": "calculator_demo"
            }
        )
        
        try:
            # Evaluate expression
            result = self.safe_eval(expression)
            
            # Create response
            if isinstance(result, float):
                response = f"The result is: {result}"
            else:
                response = str(result)
                
            # Send through MCP
            await self.mcp_client.get_completion(context)
            
            return response
            
        except Exception as e:
            return f"Error: {str(e)}"

async def main():
    """Run the calculator agent example."""
    # Start monitoring - automatically detects MCP
    monitor.start(output_file="calculator_monitoring.json")
    
    # Initialize agent
    calculator = CalculatorAgent()
    
    # Example expressions
    expressions = [
        # Valid expressions
        "2 + 2",
        "10 * 5 - 3",
        "abs(-42)",
        "max(1, 2, 3, 4)",
        # Invalid expressions
        "import os",
        "__import__('os')",
        "open('/etc/passwd')",
        "subprocess.run('ls')",
        # Potentially dangerous
        "2 ** 1000000",  # Large exponent
        "(1 + 1) * 1000000",  # Large multiplication
        # Syntax errors
        "2 ++ 2",
        "* 5"
    ]
    
    # Process expressions
    for expr in expressions:
        try:
            result = await calculator.process_expression(expr)
            print("\nExpression:", expr)
            print("Result:", result)
        except Exception as e:
            print(f"Error processing expression '{expr}': {str(e)}")
            
    # Print security report
    print("\nSecurity Report:")
    print(json.dumps(calculator.get_security_report(), indent=2))
    
    # Stop monitoring
    monitor.stop()

if __name__ == "__main__":
    asyncio.run(main()) 