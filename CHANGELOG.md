# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2024-03-11

### Fixed
- Fixed PyPI publishing workflow
- Improved release process documentation
- Added version verification in CI pipeline

## [0.1.0] - 2024-03-10

### Added
- Initial release
- Support for monitoring Anthropic Claude API calls
- Support for monitoring MCP tool calls
- SQLite database for event storage
- JSON file logging
- Security monitoring with keyword filtering
- Database utility functions for querying events
- Configuration management with OS-agnostic file locations
- Automatic framework detection
- Zero-configuration setup options

### Security
- Implemented security checks for dangerous prompts
- Added masking for sensitive data
- Integrated with pre-commit hooks for security scanning 