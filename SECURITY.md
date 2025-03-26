# Security Policy

## Supported Versions

We currently provide security updates for the following versions of Cylestio Monitor:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Cylestio Monitor seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do Not** disclose the vulnerability publicly
2. Email us at security@cylestio.com with details about the vulnerability
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggestions for mitigation

## Response Timeline

- **24 hours**: We will acknowledge receipt of your vulnerability report
- **72 hours**: We will provide an initial assessment of the vulnerability
- **7 days**: We will develop and test a fix
- **14 days**: We will release a security patch
- **30 days**: We will publicly disclose the vulnerability (unless circumstances require an adjusted timeline)

## Security Features

Cylestio Monitor includes several security features to protect your data:

1. **Content Monitoring**: Automatic detection of suspicious and dangerous content in API calls
2. **Data Encryption**: Sensitive data is encrypted in transit and at rest
3. **Access Control**: Fine-grained access control for monitoring data
4. **Audit Logging**: Comprehensive audit logs for all security-related events
5. **Data Minimization**: Only necessary data is collected and stored

## Security Best Practices

When using Cylestio Monitor, we recommend the following security best practices:

1. Keep Cylestio Monitor updated to the latest version
2. Use environment variables or secure secret management for API keys
3. Implement the principle of least privilege for access to monitoring data
4. Regularly review monitoring alerts and logs
5. Configure proper data retention policies

## Security Compliance

Cylestio Monitor is designed with the following compliance frameworks in mind:

- GDPR
- CCPA
- SOC 2
- HIPAA (when used with appropriate controls)

## Security Testing

We maintain a robust security testing program that includes:

1. Static Application Security Testing (SAST)
2. Dependency vulnerability scanning
3. Regular penetration testing
4. Security code reviews

## Contact

For security-related questions or concerns, please contact security@cylestio.com 