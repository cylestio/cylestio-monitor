# Security Configuration

Cylestio Monitor includes a robust security detection system that can be configured to match your organization's specific compliance and security requirements.

## Security Detection Categories

The security detection system operates across several categories:

### 1. Sensitive Data Detection

Identifies and masks various types of sensitive information:

- **Personal Identifiable Information (PII)**:
  - Credit card numbers
  - Social security numbers
  - Email addresses
  - Phone numbers
  - Passport numbers
  - Driver's license numbers
  - Bank account numbers

- **API Credentials**:
  - OpenAI API keys
  - Anthropic API keys
  - AWS access keys
  - GitHub tokens
  - Database connection strings
  - OAuth tokens

- **Sensitive Information**:
  - Personal health information
  - Financial data
  - Passwords and secrets
  - Private URLs and internal resources

### 2. Content Safety Detection

Analyzes content for potentially harmful or inappropriate material:

- **Prompt Injection Attempts**:
  - System prompt disclosure attempts
  - Instruction overrides
  - Role-breaking patterns
  - Jailbreak attempts

- **Harmful Content**:
  - Code execution attempts
  - Shell command injection
  - SQL injection patterns
  - Malicious URL patterns

### 3. Security Alert Levels

Security events are classified with different alert levels:

- **INFO**: General security information
- **WARNING**: Potentially suspicious content
- **SECURITY_ALERT**: Dangerous or highly sensitive content
- **CRITICAL**: Immediate security threats

## Configuration Options

### Custom Security Patterns

You can add your own security patterns by creating a configuration file:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "security": {
            "custom_patterns_file": "path/to/patterns.json"
        }
    }
)
```

The patterns file should follow this format:

```json
{
  "categories": {
    "sensitive_data": {
      "description": "Sensitive personal or organizational data",
      "patterns": [
        {
          "name": "custom_api_key",
          "pattern": "api[_-]?key[_-]?[a-zA-Z0-9]{16,}",
          "description": "Custom API Key Format"
        },
        {
          "name": "internal_project_code",
          "pattern": "PROJECT[_-][A-Z]{3}[0-9]{4}",
          "description": "Internal Project Code"
        }
      ]
    }
  }
}
```

### Security Keywords

You can also configure security keyword sets for non-regex pattern matching:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "security": {
            "custom_keywords_file": "path/to/keywords.json"
        }
    }
)
```

The keywords file should follow this format:

```json
{
  "dangerous_commands": [
    "rm -rf",
    "del /F /S /Q",
    "DROP DATABASE",
    "FORMAT C:"
  ],
  "prompt_manipulation": [
    "ignore previous instructions",
    "forget your instructions",
    "disregard your programming"
  ],
  "sensitive_data_keywords": [
    "confidential",
    "top secret",
    "proprietary",
    "internal use only"
  ]
}
```

## Default Security Configuration

The default security configuration includes patterns for common types of sensitive data and security concerns. These defaults are designed to help organizations meet common regulatory requirements such as SOC2, GDPR, and HIPAA.

You can view the current active security patterns at runtime:

```python
from cylestio_monitor.security_detection import SecurityScanner

# Get the singleton instance
scanner = SecurityScanner.get_instance()

# Print current patterns
print(scanner._pattern_registry.get_all_patterns())
```

## Customizing Masking Behavior

You can configure how sensitive data is masked in logs:

```python
cylestio_monitor.start_monitoring(
    agent_id="my-agent",
    config={
        "security": {
            "masking": {
                "credit_card": "first4_last4",  # Show first 4 and last 4 digits
                "email": "username_hidden",     # Hide username, show domain
                "api_key": "prefix_only",       # Show only key prefix
                "default": "full_mask"          # Complete masking
            }
        }
    }
)
```

## Security Event Logging

Security events are logged with detailed information about the detected content:

```json
{
  "schema_version": "1.0", 
  "timestamp": "2024-04-10T11:43:14.312935", 
  "trace_id": "d773c49ac81542aeb0a19c957c162d53", 
  "span_id": "9b2e531efe9ac834", 
  "name": "security.content.dangerous", 
  "level": "SECURITY_ALERT", 
  "attributes": {
    "security.alert_level": "dangerous", 
    "security.keywords": ["credit_card:8989-****-****-8989"], 
    "security.content_sample": "{'messages': [{'role': 'user', 'content': 'ok any alert for card 8989-****-****-8989 in sf?'}], 'mod...", 
    "security.category": "sensitive_data", 
    "security.severity": "high", 
    "security.description": "Credit Card Number"
  }
}
```

All sensitive data in security events is properly masked to ensure the security system itself doesn't become a vector for data leakage. 