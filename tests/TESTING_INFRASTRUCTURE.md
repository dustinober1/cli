# Testing Infrastructure Documentation

This document describes the comprehensive testing infrastructure created for the Vibe Coder CLI project.

## Overview

The testing infrastructure includes:
- **`conftest.py`** - Comprehensive pytest fixtures for all testing needs
- **`.env.test`** - Test environment configuration
- **`pytest.ini`** - Detailed pytest configuration with markers and options
- **Updated `Makefile`** - New test targets for different test types

## 1. Fixtures in `conftest.py`

### Async Configuration Fixtures
- `event_loop` - Custom event loop for async tests
- `temp_config_dir` - Temporary directory for configuration files
- `config_manager` - ConfigManager instance with temporary storage
- `sample_provider` - Sample OpenAI provider configuration
- `sample_provider_anthropic` - Sample Anthropic provider configuration
- `config_manager_with_provider` - ConfigManager with pre-configured provider

### File System Fixtures
- `temp_dir` - Generic temporary directory
- `sample_python_project` - Complete Python project structure with:
  - Source modules (`src/`)
  - Test files (`tests/`)
  - Configuration files (`pyproject.toml`, `.gitignore`)
  - Documentation (`README.md`)
- `git_repository` - Git-initialized version of sample project with:
  - Initial commit
  - Feature branch
  - Multiple commits

### AI Mocking Fixtures
- `mock_openai_client` - Mock OpenAI API client
- `mock_anthropic_client` - Mock Anthropic API client
- `mock_generic_client` - Mock generic OpenAI-compatible client
- `mock_provider` - Mock provider configuration dictionary
- `mock_ai_response` - Mock API response object
- `mock_api_messages` - Sample API message history

### Command Context Fixtures
- `mock_console` - Mock Rich console for CLI testing
- `slash_command_parser` - SlashCommandParser instance
- `mock_subprocess` - Mock subprocess.run
- `mock_http_client` - Mock httpx.AsyncClient

### Questionary Mocking Fixtures
- `mock_questionary` - Mock all questionary prompts
- `mock_wizard_responses` - Pre-defined wizard responses

### Intelligence Module Fixtures
- `repository_mapper` - RepositoryMapper instance
- `sample_ast_data` - Sample AST analysis data

### Healing Module Fixtures
- `auto_healer` - AutoHealer instance
- `error_snippet` - Code with errors for testing
- `fixed_snippet` - Corrected version of error snippet

### Analytics Module Fixtures
- `cost_tracker` - CostTracker instance
- `sample_usage_data` - Sample usage statistics

### Plugin System Fixtures
- `plugin_manager` - PluginManager instance
- `sample_plugin_code` - Example plugin implementation

### Utility Fixtures
- `create_test_file` - Dynamic test file creation
- `assert_files_equal` - File comparison utility
- `capture_console_output` - Console output capture

## 2. Test Environment Configuration (`.env.test`)

Contains mock configurations for:
- OpenAI, Anthropic, Ollama, and Generic providers
- Test settings (mock responses, disabled telemetry)
- Cache and rate limiting settings
- File system paths for testing
- Database and logging configuration

**Important:** Never contains real API keys or sensitive data.

## 3. Pytest Configuration (`pytest.ini`)

### Test Discovery
- `testpaths = tests`
- `python_files = test_*.py *_test.py`
- `python_classes = Test*`
- `python_functions = test_*`

### Default Options
- Verbose output
- Strict marker and config enforcement
- Coverage reporting (HTML, XML, terminal)
- Short tracebacks
- Duration reporting

### Markers

#### Test Type Markers
- `unit` - Unit tests (fast, isolated)
- `integration` - Integration tests (external dependencies)
- `e2e` - End-to-end tests (full workflow)
- `slow` - Slow running tests (>1 second)
- `performance` - Performance benchmarks

#### Dependency Markers
- `network` - Requires network access
- `github` - Requires GitHub API access
- `database` - Requires database connection

#### Feature-Specific Markers
- `cli` - CLI command tests
- `config` - Configuration management tests
- `api` - API client tests
- `intelligence` - Intelligence module tests
- `healing` - Auto-healing tests
- `analytics` - Analytics/cost tracking tests
- `plugins` - Plugin system tests
- `mcp` - MCP integration tests
- `slash` - Slash command tests

#### Provider-Specific Markers
- `openai` - OpenAI integration tests
- `anthropic` - Anthropic integration tests
- `ollama` - Ollama integration tests
- `generic` - Generic provider tests

## 4. Makefile Test Targets

### Basic Test Commands
```bash
make test          # Run all tests
make test-unit     # Run unit tests only
make test-integration  # Run integration tests only
make test-all      # Run all test suites (unit + integration + performance)
make test-performance  # Run performance benchmarks
make test-watch    # Run tests in watch mode
make test-cov      # Run tests with coverage report
```

### Marker-Specific Tests
```bash
make test-cli      # Run CLI tests
make test-api      # Run API tests
make test-config   # Run config tests
make test-intelligence  # Run intelligence tests
make test-healing  # Run healing tests
make test-analytics  # Run analytics tests
make test-plugins  # Run plugin tests
make test-slash    # Run slash command tests
make test-mcp      # Run MCP tests
```

### Provider-Specific Tests
```bash
make test-openai   # OpenAI tests
make test-anthropic  # Anthropic tests
make test-ollama   # Ollama tests
make test-generic  # Generic provider tests
```

### Special Categories
```bash
make test-security     # Security tests
make test-reliability  # Reliability tests
make test-compatibility  # Compatibility tests
```

## 5. Usage Examples

### Using Fixtures in Tests
```python
import pytest
from vibe_coder.types.config import AIProvider

@pytest.mark.unit
def test_provider_creation(sample_provider):
    """Test creating a provider from fixture."""
    provider = AIProvider(**sample_provider)
    assert provider.name == "test-openai"
    assert provider.api_key == "sk-test-key-12345"

@pytest.mark.asyncio
async def test_async_config(config_manager):
    """Test async config operations."""
    providers = await config_manager.list_providers()
    assert isinstance(providers, dict)

@pytest.mark.integration
def test_file_operations(sample_python_project):
    """Test with sample project structure."""
    assert (sample_python_project / "src").exists()
    assert (sample_python_project / "pyproject.toml").exists()
```

### Running Specific Tests
```bash
# Run all unit tests
poetry run pytest -m unit

# Run all API tests
poetry run pytest -m api

# Run OpenAI-specific tests
poetry run pytest -m openai

# Run tests for a specific module
poetry run pytest tests/test_config/test_types.py -v

# Run tests with specific markers
poetry run pytest -m "unit and api"

# Run tests excluding certain markers
poetry run pytest -m "not slow"
```

## 6. Best Practices

### Writing Tests
1. Use appropriate markers for categorization
2. Leverage fixtures for common setup
3. Keep tests isolated and independent
4. Use descriptive test names
5. Test both success and failure cases

### Async Testing
- Use `@pytest.mark.asyncio` decorator
- Leverage async fixtures
- Test both sync and async code paths

### Integration Testing
- Use `@pytest.mark.integration` marker
- Test with actual file system operations
- Use the `sample_python_project` fixture
- Mock external dependencies appropriately

### Performance Testing
- Use `@pytest.mark.performance` marker
- Measure execution times
- Use `pytest.mark.slow` for longer tests

## 7. Dependencies

New test dependencies added to `pyproject.toml`:
- `pytest-mock` - Advanced mocking support
- `pytest-xdist` - Parallel test execution
- `pytest-watch` - Watch mode for TDD
- `pytest-timeout` - Test timeout handling
- `pytest-html` - HTML test reports
- `pytest-json-report` - JSON test reports
- `factory-boy` - Test data factories
- `faker` - Fake data generation

## 8. Continuous Integration

The testing infrastructure is designed to work well with CI/CD:
- JUnit XML output support (commented in pytest.ini)
- Coverage reporting in multiple formats
- Marker-based test selection
- Parallel test execution support

## 9. Maintenance

To keep the testing infrastructure healthy:
1. Regularly update fixtures as the codebase evolves
2. Add new markers for new features
3. Review test coverage reports
4. Update dependencies regularly
5. Clean up unused fixtures and tests

## 10. Troubleshooting

### Common Issues
1. **Event loop errors in async tests**: Use the `event_loop` fixture
2. **Fixture not found**: Ensure fixtures are imported from conftest
3. **Marker not recognized**: Check pytest.ini marker definitions
4. **Coverage too low**: Review uncovered code and add tests

### Debugging
- Use `--pdb` option to drop into debugger on failure
- Use `-vv` for extra verbose output
- Use `--trace-config` to see configuration details
- Use `--collect-only` to see discovered tests without running them