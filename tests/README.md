# Test Directory

This directory is ready for test files.

## Structure
```
tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── e2e/                # End-to-end tests
└── fixtures/           # Test data and fixtures
```

## Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app
```
