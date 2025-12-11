.PHONY: install test test-cov test-unit test-integration test-all test-performance test-watch lint format clean run help

help:
	@echo "Vibe Coder - Development Commands"
	@echo ""
	@echo "  make install       Install dependencies with Poetry"
	@echo "  make test          Run all tests with pytest"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-all      Run all test suites (unit + integration + performance)"
	@echo "  make test-performance  Run performance benchmarks"
	@echo "  make test-watch    Run tests in watch mode"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run linters (flake8, mypy)"
	@echo "  make format        Format code (black, isort)"
	@echo "  make clean         Clean build artifacts"
	@echo "  make run           Run the CLI"
	@echo ""

install:
	poetry install

test:
	poetry run pytest

test-unit:
	poetry run pytest -m "unit or (not integration and not e2e and not slow)" --disable-warnings

test-integration:
	poetry run pytest -m "integration or e2e" -v --tb=short

test-all:
	@echo "Running all test suites..."
	@echo "=== Unit Tests ===" && $(MAKE) test-unit
	@echo ""
	@echo "=== Integration Tests ===" && $(MAKE) test-integration
	@echo ""
	@echo "=== Performance Tests ===" && $(MAKE) test-performance
	@echo ""
	@echo "=== Coverage Report ===" && $(MAKE) test-cov

test-performance:
	poetry run pytest -m "performance or slow" -v --durations=0

test-watch:
	poetry run ptw --runner "python -m pytest -x -v" -- tests/

test-cov:
	poetry run pytest --cov=vibe_coder --cov-report=html --cov-report=term-missing --cov-report=xml

# Test with specific markers
test-cli:
	poetry run pytest -m "cli" -v

test-api:
	poetry run pytest -m "api" -v

test-config:
	poetry run pytest -m "config" -v

test-intelligence:
	poetry run pytest -m "intelligence" -v

test-healing:
	poetry run pytest -m "healing" -v

test-analytics:
	poetry run pytest -m "analytics" -v

test-plugins:
	poetry run pytest -m "plugins" -v

test-slash:
	poetry run pytest -m "slash" -v

test-mcp:
	poetry run pytest -m "mcp" -v

# Provider-specific tests
test-openai:
	poetry run pytest -m "openai" -v

test-anthropic:
	poetry run pytest -m "anthropic" -v

test-ollama:
	poetry run pytest -m "ollama" -v

test-generic:
	poetry run pytest -m "generic" -v

# Special test categories
test-security:
	poetry run pytest -m "security" -v

test-reliability:
	poetry run pytest -m "reliability" -v

test-compatibility:
	poetry run pytest -m "compatibility" -v

lint:
	poetry run flake8 vibe_coder tests
	poetry run mypy vibe_coder

format:
	poetry run black vibe_coder tests
	poetry run isort vibe_coder tests

clean:
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache test_results
	rm -rf /tmp/vibe_coder_test

run:
	poetry run vibe-coder --help
