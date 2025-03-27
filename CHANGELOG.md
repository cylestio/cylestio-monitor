# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2024-03-27

### Security
- Enhanced sensitive data masking for API keys and tokens
- Implemented security scanning in CI/CD pipeline
- Added security tests for sensitive data handling
- Activated Bandit and Safety checks in pre-commit hooks
- Fixed security warnings by adding usedforsecurity=False to MD5 hash functions

### Added
- Added OpenTelemetry-compliant schema for events
- Improved documentation for OpenTelemetry integration
- Added tracing context and span support
- Enhanced API for distributed tracing

### Changed
- Updated documentation to reflect OpenTelemetry-compliant API changes
- Standardized event schema to align with OpenTelemetry specifications

## [0.1.3] - 2024-03-21

### Added
- Enhanced response tracking for all supported frameworks
- Improved error handling in Anthropic SDK patcher
- Added debugging capabilities for LLM response tracking
- Event type consistency across all frameworks (LLM_call_start, LLM_call_finish)

### Fixed
- Fixed issue with Anthropic callback handling for response events
- Fixed model type handling in events_processor.py for Anthropic
- Added fallback mechanism for LangChain run_id tracking
- Improved robustness of LangChain callback response capture
- Better error handling in multi-framework examples

### Changed
- Updated documentation to reflect enhanced response tracking capabilities
- Improved example code with better error handling
- Standardized event naming across frameworks
- Enhanced framework compatibility matrix with response tracking information

## [0.1.2] - 2024-03-11

### Changed
- Simplified repository documentation to focus on core SDK functionality
- Moved comprehensive documentation to centralized docs site (https://docs.cylestio.com)
- Updated documentation URLs in package metadata
- Removed redundant documentation files
- Enhanced README with clearer installation and usage instructions

### Removed
- Removed MkDocs configuration and related files
- Removed redundant documentation that is now in the centralized docs

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