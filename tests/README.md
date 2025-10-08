# MyWorkAnalyzer Test Suite

This directory contains the test suite for MyWorkAnalyzer.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_common.py -v
```

### Run specific test
```bash
pytest tests/test_common.py::TestLoadConfig::test_load_config_valid -v
```

## Test Structure

```
tests/
├── __init__.py                  # Test package initialization
├── README.md                    # This file
├── fixtures/                    # Test fixtures and data
│   └── config_test.yaml        # Test configuration
├── test_common.py              # Tests for common.py
└── test_annotate.py            # Tests for annotate.py
```

## Writing New Tests

1. Create a new file named `test_<module>.py`
2. Import pytest and the module to test
3. Create test classes grouping related tests
4. Use descriptive test names starting with `test_`
5. Use fixtures for common setup
6. Assert expected behavior

## Test Coverage Goals

- **Current**: ~40% (basic tests implemented)
- **Target**: >60% for production readiness
- **Ideal**: >80% comprehensive coverage

## Continuous Integration

Tests should be run in CI/CD pipeline before merging changes.

## Test Categories

- **Unit Tests**: Test individual functions (test_common.py, test_annotate.py)
- **Integration Tests**: Test module interactions (TODO)
- **End-to-End Tests**: Test complete workflows (TODO)

