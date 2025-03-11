# Contributing to Cylestio Monitor

We welcome contributions to Cylestio Monitor! This guide will help you get started.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cylestio/cylestio-monitor.git
   cd cylestio-monitor
   ```

2. Set up the development environment:
   ```bash
   ./setup_dev.sh
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev,test,security]"
   ```

## Code Standards

- All code must pass the pre-commit hooks
- Follow the type hints and docstring requirements
- Write tests for new features

## Testing

Run the tests with pytest:

```bash
pytest
```

## Submitting Changes

1. Create a branch for your changes
2. Make your changes
3. Run the tests
4. Submit a pull request

## Security Considerations

When contributing, please keep security in mind:

- Avoid introducing new dependencies without careful consideration
- Follow secure coding practices
- Add appropriate security tests for new features 