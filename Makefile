.PHONY: install test test-cov lint format clean run help

help:
	@echo "Vibe Coder - Development Commands"
	@echo ""
	@echo "  make install    Install dependencies with Poetry"
	@echo "  make test       Run tests with pytest"
	@echo "  make test-cov   Run tests with coverage report"
	@echo "  make lint       Run linters (flake8, mypy)"
	@echo "  make format     Format code (black, isort)"
	@echo "  make clean      Clean build artifacts"
	@echo "  make run        Run the CLI"
	@echo ""

install:
	poetry install

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=vibe_coder --cov-report=html --cov-report=term

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
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache

run:
	poetry run vibe-coder --help
