# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.10] - 2025-05-12

### Added
- Added configurable telemetry endpoint to allow custom host/port configuration
- Enhanced API client to automatically append the /v1/telemetry path to endpoint URLs

### Changed
- Updated documentation to better describe configuration options
- Improved examples to demonstrate telemetry endpoint configuration
- Enhanced error handling for endpoint connections

### Fixed
- Fixed issue with telemetry endpoint configuration requiring full path specification

## [0.1.9] - 2025-05-05

### Fixed
- Fixed MCP patching failure caused by API compatibility issues with parameter handling
- Reimplemented MCP patcher with version-specific method signatures for different MCP versions
- Added robust error handling to prevent logging failures from interrupting patching
- Improved SDK resilience with graceful fallbacks for parameter incompatibilities
- Enhanced MCP tool call monitoring with proper error recovery and context maintenance

## [0.1.8] - 2025-05-05

### Fixed
- Fixed MCP patching failure caused by an API compatibility issue with agent_id parameter 
- Improved MCP patcher to handle different versions automatically without requiring custom patches
- Added error handling in event logging to prevent patching failures
- Enhanced SDK's robustness with graceful fallbacks for compatibility issues
- Improved compatibility between different versions of the monitoring API
- Enhanced MCP tool call logging with more robust error recovery

## [0.1.7] - 2025-05-01

### Added
- Added compatibility layer to handle version mismatches between LangChain components
- Implemented a fail-soft approach for functions with changing signatures like `convert_to_openai_function`
- Added flexible kwarg handling to support both older and newer library versions

### Changed
- Improved error handling to ensure monitor never crashes the host application
- Enhanced patching to handle incompatible library versions gracefully
- Added unique message IDs to security alerts for better tracking and identification
- Improved security scanning to only focus on the latest user message in conversations, reducing alert fatigue

### Fixed
- Fixed TypeError when using the monitor with mismatched LangChain component versions
- Resolved issue with `convert_to_openai_function` when called with the 'strict' kwarg on older versions
- Fixed issue where repeated security alerts were generated for the same content in conversation history

## [0.1.6] - 2025-04-30

### Added
- Added support for OpenAI Chat Completions and Completions APIs
- Enhanced LangChain support with updated imports for langchain-core and langchain-community
- Added monitoring for LangChain tools and tool decorators
- Improved chain execution tracking with better span context
- Added token usage tracking for supported LLM providers
- Enhanced security masking for sensitive data in security event logs
- Improved consistent masking across all event fields including content samples
- Added support for additional LLM providers
- Enhanced monitoring capabilities for prompt templates
- Improved documentation with more examples
- Better error handling for API requests

### Changed
- Updated LangChain imports to use langchain-core and langchain-community packages
- Improved tool monitoring with better error handling and context capture
- Enhanced chain execution monitoring with more detailed metrics
- Updated compatibility matrix to reflect new framework support
- Refined event schema for better interoperability
- Enhanced security features with improved data masking
- Updated dependencies to latest versions
- Improved performance of event processing pipeline

### Fixed
- Fixed import issues with LangChain components
- Improved error handling in tool execution monitoring
- Fixed span context propagation in chain execution
- Resolved deprecation warnings in LangChain imports
- Fixed an issue where sensitive data in security event content samples wasn't properly masked
- Fixed minor issues with token counting
- Improved reliability of event logging
- Fixed configuration handling in multi-environment setups

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
