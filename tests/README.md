# CYT Test Suite

This directory contains automated tests for the Chasing Your Tail (CYT) project.

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_setup_wizard.py
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

- `test_setup_wizard.py` - Tests for setup wizard functionality
- `test_input_validation.py` - Tests for input validation and sanitization
- `test_integration.py` - Integration tests for installation and module imports

## GitHub Actions

Tests are automatically run on pull requests via GitHub Actions. The workflow:
- Tests across Python versions 3.11-3.12
- Runs code linting with flake8
- Performs security scanning with bandit
- Generates coverage reports

## Writing Tests

Follow these guidelines when adding new tests:

1. Place test files in the `tests/` directory
2. Name test files as `test_*.py`
3. Name test functions as `test_*`
4. Use pytest fixtures for setup/teardown
5. Add docstrings to describe what each test does

## Test Coverage

To view coverage report after running tests:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```
