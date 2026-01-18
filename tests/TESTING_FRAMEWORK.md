# Knowledge Base GraphRAG - Testing Framework

## Overview

This testing framework provides comprehensive end-to-end testing capabilities for the Knowledge Base GraphRAG system. It includes tests for all features including the new improvements: embedding caching, background task processing, vector similarity search, circuit breaker integration, and standardized exceptions.

## Architecture

### Test Components

1. **Test Configuration (`test_config.py`)**: Centralized configuration for all test parameters
2. **Test Framework (`test_framework.py`)**: Modular, extensible framework for test creation
3. **Test Runner (`test_runner.py`)**: AI-agent friendly interface for executing tests
4. **Specific Test Modules**:
   - `test_knowledge_base_e2e.py`: Comprehensive end-to-end tests
   - `test_new_features.py`: Tests for newly added features
   - `test_e2e_ui.py`: Existing Playwright tests

## Prerequisites

Before running tests, ensure both servers are running:

```bash
# Terminal 1: Start API server
uv run kb-server

# Terminal 2: Start UI server  
cd streamlit-ui && uv run streamlit run app.py
```

## Running Tests

### Command Line Interface

The test runner provides multiple ways to execute tests:

```bash
# List available tests
python -m tests.test_runner list

# Show configuration
python -m tests.test_runner --config

# Run a specific test suite
python -m tests.test_runner run-suite --suite core
python -m tests.test_runner run-suite --suite features  
python -m tests.test_runner run-suite --suite e2e

# Run a specific test
python -m tests.test_runner run-test --test ingestion
python -m tests.test_runner run-test --test search
python -m tests.test_runner run-test --test new_features

# Run multiple specific tests
python -m tests.test_runner run --tests ingestion search graph
```

### Programmatically

```python
import asyncio
from tests.test_runner import TestRunner

async def run_tests():
    runner = TestRunner()
    
    # Run core test suite
    results = await runner.run_test_suite("core")
    
    # Run specific test
    result = await runner.run_specific_test("ingestion")
    
    # Run multiple tests
    results = await runner.run_multiple_tests(["ingestion", "search"])

asyncio.run(run_tests())
```

## Test Categories

### Core Functionality Tests
- **Ingestion**: Tests text ingestion pipeline
- **Search**: Tests semantic search with vector similarity
- **Graph Visualization**: Tests knowledge graph display
- **Dashboard**: Tests statistics and metrics display

### New Feature Tests
- **Embedding Cache**: Tests performance improvements from caching
- **Background Tasks**: Tests non-blocking operations
- **Vector Search**: Tests pgvector similarity search
- **API Integration**: Tests all new API endpoints

### End-to-End Tests
- **Comprehensive Pipeline**: Full workflow testing
- **Data Integrity**: Ensures data consistency
- **Performance**: Measures response times

## AI Agent Usage

The framework is designed for easy integration with AI agents:

### For AI Agents

1. **Quick Validation**: Use `run-test` for fast validation of specific features
2. **Comprehensive Testing**: Use `run-suite` for thorough validation
3. **Modular Access**: Each test is self-contained and can be run independently

### Example AI Agent Commands

```python
# AI agent can run specific feature tests
await runner.run_specific_test("new_features")

# Or run comprehensive validation
await runner.run_test_suite("e2e")

# Or test specific functionality
await runner.run_multiple_tests(["ingestion", "search"])
```

## Configuration

All test configuration is controlled through `tests/test_config.py`. Key settings include:

- Server endpoints (API and UI)
- Database connection settings
- Browser settings for Playwright
- Timeout values
- Screenshot options

Environment variables can override default values:
- `TEST_API_URL`: API server URL
- `TEST_UI_URL`: UI server URL
- `TEST_DB_USER`: Database user
- `TEST_DB_PASSWORD`: Database password

## Test Structure

### Base Classes

- `BaseKnowledgeBaseTest`: Common setup/teardown for all tests
- `KnowledgeBaseTestHelper`: Utility functions for common operations
- `TestConfig`: Configuration dataclass

### Test Modules

Each test module follows the same pattern:
1. Inherits from `BaseKnowledgeBaseTest`
2. Implements `run_test()` method
3. Returns boolean indicating success/failure

### Extending Tests

To add new tests:

1. Create a new test class inheriting from `BaseKnowledgeBaseTest`
2. Implement the `run_test()` method
3. Add to the test registry in `test_framework.py`

Example:
```python
class NewFeatureTest(BaseKnowledgeBaseTest):
    async def run_test(self) -> bool:
        # Implementation here
        return True  # or False
```

## Reporting

Test results include:
- Pass/fail status
- Execution time
- Detailed error messages
- Individual test results
- Summary statistics

## Troubleshooting

### Common Issues

1. **Servers Not Running**: Ensure both API and UI servers are started
2. **Database Connection**: Verify database credentials in config
3. **Timeout Issues**: Increase timeout values in configuration
4. **Playwright Error**: Ensure Playwright browsers are installed:
   ```bash
   uv run playwright install
   ```

### Debugging

Enable detailed logging by setting log level in configuration or using headful browser mode for visual inspection.

## Maintenance

- Tests are designed for easy maintenance and extension
- Configuration is centralized for consistent behavior
- Dependencies are minimal and well-documented
- Error handling is robust across all test scenarios