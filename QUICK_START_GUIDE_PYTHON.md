# Quick Start Guide for Python Developers

Welcome to Vibe Coder! This guide will get you from zero to your first commit in under 2 hours using Python.

---

## 🎯 Goal

By the end of this guide, you will:
1. Have the Python project running locally
2. Understand the codebase structure
3. Make your first code contribution
4. Run tests with pytest
5. Be ready to pick up your first task

---

## ✅ Prerequisites

Before starting, ensure you have:

- [ ] **Python 3.9+** (`python --version` or `python3 --version`)
- [ ] **Poetry** (recommended) or **pip**
- [ ] **Git** installed (`git --version`)
- [ ] A code editor (VS Code recommended with Python extension)
- [ ] Terminal/command line familiarity
- [ ] Basic Python knowledge

### Install Poetry (Recommended)

```bash
# On macOS/Linux/WSL
curl -sSL https://install.python-poetry.org | python3 -

# On Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Verify installation
poetry --version
```

---

## 🚀 Step 1: Clone and Setup (10 minutes)

### 1.1 Clone the Repository

```bash
# Clone the repo
git clone https://github.com/YOUR_ORG/vibe-coder.git
cd vibe-coder

# Create your feature branch
git checkout -b feature/your-name-setup
```

### 1.2 Install Dependencies with Poetry

```bash
# Install all dependencies
poetry install

# Activate the virtual environment
poetry shell

# Verify Python version
python --version  # Should be 3.9+
```

**Alternative: Using pip with venv**

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -e ".[dev]"
```

### 1.3 Verify Setup

```bash
# Check installed packages
poetry show

# Try running CLI (will show error - that's OK for now)
vibe-coder --help
```

---

## 📁 Step 2: Understand the Structure (15 minutes)

### 2.1 Python Project Layout

```
vibe-coder/
├── vibe_coder/              # Main package (note: underscore, not hyphen)
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Main CLI entry point (Typer app)
│   │
│   ├── commands/            # CLI command implementations
│   │   ├── __init__.py
│   │   ├── chat.py          # /chat command
│   │   ├── setup.py         # /setup command
│   │   └── slash/           # Slash command handlers
│   │
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   ├── manager.py       # ConfigManager class
│   │   ├── env_handler.py   # Environment variables
│   │   └── validator.py     # Config validation
│   │
│   ├── api/                 # API clients
│   │   ├── __init__.py
│   │   ├── base_client.py   # Abstract base class
│   │   ├── openai_client.py # OpenAI implementation
│   │   └── ...
│   │
│   ├── prompts/             # Interactive prompts (Questionary)
│   ├── utils/               # Helper functions
│   └── types/               # Type hints and dataclasses
│
├── tests/                   # Pytest tests
│   ├── __init__.py
│   ├── test_config/
│   ├── test_api/
│   └── ...
│
├── pyproject.toml           # Project metadata & dependencies (like package.json)
├── poetry.lock              # Locked dependencies (like package-lock.json)
├── Makefile                 # Common tasks shortcut
├── README.md
└── .gitignore
```

### 2.2 Key Python Files

**Start here:**
- `pyproject.toml` - Project configuration, dependencies, scripts
- `vibe_coder/cli.py` - CLI entry point (uses Typer)
- `vibe_coder/types/config.py` - Type definitions (dataclasses)
- `Makefile` - Common development tasks

**Key differences from Node.js/TypeScript:**
- `__init__.py` in every directory (makes it a package)
- `pyproject.toml` instead of `package.json`
- Type hints instead of TypeScript types
- `async`/`await` native in Python 3.9+

---

## 🏗️ Step 3: Your First Task (30 minutes)

Let's build the Logger Utility (Task 6.1) - a simple but essential component.

### 3.1 Create the File

```bash
# Create utils directory if it doesn't exist
mkdir -p vibe_coder/utils

# Create the logger file
touch vibe_coder/utils/logger.py

# Create __init__.py to make it a package
touch vibe_coder/utils/__init__.py
```

### 3.2 Write the Code

Open `vibe_coder/utils/logger.py`:

```python
"""
Logging utilities with colored output using Rich.
"""
import os
from rich.console import Console

console = Console()

DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"


def log_success(message: str) -> None:
    """
    Log a success message with a green checkmark.

    Args:
        message: The message to log

    Example:
        >>> log_success("Configuration saved successfully")
        ✓ Configuration saved successfully
    """
    console.print(f"[green]✓[/green] {message}")


def log_error(message: str) -> None:
    """
    Log an error message with a red X.

    Args:
        message: The error message to log

    Example:
        >>> log_error("Failed to connect to API")
        ✗ Failed to connect to API
    """
    console.print(f"[red]✗[/red] {message}", style="red")


def log_warning(message: str) -> None:
    """
    Log a warning message with a yellow warning symbol.

    Args:
        message: The warning message to log

    Example:
        >>> log_warning("API key is not set, using default")
        ⚠ API key is not set, using default
    """
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def log_info(message: str) -> None:
    """
    Log an info message with a blue info symbol.

    Args:
        message: The info message to log

    Example:
        >>> log_info("Loading configuration from ~/.vibe/config.json")
        ℹ Loading configuration from ~/.vibe/config.json
    """
    console.print(f"[blue]ℹ[/blue] {message}", style="blue")


def log_debug(message: str) -> None:
    """
    Log a debug message (only shown when DEBUG=true).

    Args:
        message: The debug message to log

    Example:
        >>> log_debug("Token count: 1234")
        [DEBUG] Token count: 1234  # Only if DEBUG=true
    """
    if DEBUG_MODE:
        console.print(f"[dim][DEBUG][/dim] {message}", style="dim")


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.

    Returns:
        True if DEBUG environment variable is set to 'true'

    Example:
        >>> is_debug_mode()
        False
        >>> # After setting DEBUG=true
        >>> is_debug_mode()
        True
    """
    return DEBUG_MODE
```

### 3.3 Create a Test

Create `tests/test_utils/test_logger.py`:

```python
"""Tests for logger utility."""
import os
import pytest
from io import StringIO
from unittest.mock import patch

from vibe_coder.utils.logger import (
    log_success,
    log_error,
    log_warning,
    log_info,
    log_debug,
    is_debug_mode,
)


def test_log_success(capsys):
    """Test success logging."""
    log_success("Test success")
    captured = capsys.readouterr()
    assert "Test success" in captured.out


def test_log_error(capsys):
    """Test error logging."""
    log_error("Test error")
    captured = capsys.readouterr()
    assert "Test error" in captured.out


def test_log_warning(capsys):
    """Test warning logging."""
    log_warning("Test warning")
    captured = capsys.readouterr()
    assert "Test warning" in captured.out


def test_log_info(capsys):
    """Test info logging."""
    log_info("Test info")
    captured = capsys.readouterr()
    assert "Test info" in captured.out


def test_log_debug_disabled(capsys):
    """Test debug logging when DEBUG is false."""
    with patch.dict(os.environ, {"DEBUG": "false"}):
        # Need to reimport to pick up new env var
        import importlib
        from vibe_coder.utils import logger
        importlib.reload(logger)

        logger.log_debug("Should not appear")
        captured = capsys.readouterr()
        assert "Should not appear" not in captured.out


def test_log_debug_enabled(capsys):
    """Test debug logging when DEBUG is true."""
    with patch.dict(os.environ, {"DEBUG": "true"}):
        import importlib
        from vibe_coder.utils import logger
        importlib.reload(logger)

        logger.log_debug("Should appear")
        captured = capsys.readouterr()
        assert "Should appear" in captured.out


def test_is_debug_mode_false():
    """Test is_debug_mode returns False by default."""
    with patch.dict(os.environ, {"DEBUG": "false"}):
        import importlib
        from vibe_coder.utils import logger
        importlib.reload(logger)

        assert logger.is_debug_mode() is False


def test_is_debug_mode_true():
    """Test is_debug_mode returns True when DEBUG=true."""
    with patch.dict(os.environ, {"DEBUG": "true"}):
        import importlib
        from vibe_coder.utils import logger
        importlib.reload(logger)

        assert logger.is_debug_mode() is True
```

Create `tests/test_utils/__init__.py` (empty file).

### 3.4 Run the Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_utils/test_logger.py

# Run with verbose output
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=vibe_coder --cov-report=term-missing

# Or use the Makefile
make test
```

You should see output like:
```
============================= test session starts ==============================
collected 7 items

tests/test_utils/test_logger.py .......                                  [100%]

============================== 7 passed in 0.12s ===============================
```

### 3.5 Try It Out

Create a test script `test_logger_demo.py`:

```python
#!/usr/bin/env python3
"""Demo script to test logger utility."""

from vibe_coder.utils.logger import (
    log_success,
    log_error,
    log_warning,
    log_info,
    log_debug,
)

print("\nTesting logger utility:\n")

log_success("This is a success message")
log_error("This is an error message")
log_warning("This is a warning message")
log_info("This is an info message")
log_debug("This is a debug message (set DEBUG=true to see)")

print("\nDone!\n")
```

Run it:

```bash
# Normal mode
python test_logger_demo.py

# With debug mode
DEBUG=true python test_logger_demo.py
```

### 3.6 Format and Lint Your Code

```bash
# Format code with Black
poetry run black vibe_coder tests

# Sort imports with isort
poetry run isort vibe_coder tests

# Or use Makefile
make format

# Run linter
make lint
```

### 3.7 Commit Your Work

```bash
# Stage your changes
git add vibe_coder/utils/logger.py
git add vibe_coder/utils/__init__.py
git add tests/test_utils/test_logger.py
git add tests/test_utils/__init__.py

# Commit with a good message
git commit -m "feat: implement logger utility (Task 6.1)

- Add log_success, log_error, log_warning, log_info, log_debug functions
- Use Rich console for colored output
- Add debug mode support via DEBUG env var
- Add comprehensive pytest tests
- All tests passing (7/7)

Co-Authored-By: Your Name <your.email@example.com>"

# Push to your branch
git push origin feature/your-name-setup
```

---

## 🎓 Step 4: Learn the Python Workflow (15 minutes)

### 4.1 Poetry Commands

```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add requests

# Add a dev dependency
poetry add --group dev pytest-mock

# Update dependencies
poetry update

# Show installed packages
poetry show

# Run command in virtual environment
poetry run python script.py

# Activate shell (stay in venv)
poetry shell

# Build package
poetry build

# Publish to PyPI
poetry publish
```

### 4.2 Development Commands (Makefile)

```bash
# Install dependencies
make install

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code (Black + isort)
make format

# Run linter (flake8 + mypy)
make lint

# Clean build artifacts
make clean
```

### 4.3 Commit Message Format

Same as TypeScript version - use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature
git commit -m "feat(api): add Anthropic API client"

# Bug fix
git commit -m "fix(config): handle missing config file gracefully"

# Documentation
git commit -m "docs: add API usage examples"

# Tests
git commit -m "test: add integration tests for chat command"
```

---

## 🧪 Step 5: Testing with pytest (10 minutes)

### 5.1 Test Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config/test_manager.py

# Run specific test function
pytest tests/test_utils/test_logger.py::test_log_success

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=vibe_coder --cov-report=html

# Run tests matching a pattern
pytest -k "logger"

# Run in watch mode (requires pytest-watch)
ptw
```

### 5.2 Writing Tests

**Basic test structure:**

```python
import pytest
from vibe_coder.utils.helper import my_function

def test_my_function():
    """Test my_function with valid input."""
    result = my_function("input")
    assert result == "expected"

def test_my_function_with_invalid_input():
    """Test my_function with invalid input."""
    with pytest.raises(ValueError):
        my_function(None)
```

**Using fixtures:**

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    import shutil
    shutil.rmtree(temp_path)

def test_with_fixture(temp_dir):
    """Test using a fixture."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello")
    assert test_file.read_text() == "Hello"
```

**Async tests:**

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await my_async_function()
    assert result is not None
```

---

## 🛠️ Step 6: VS Code Setup (10 minutes)

### 6.1 Install Extensions

Recommended extensions (`.vscode/extensions.json`):

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "charliermarsh.ruff",
    "littlefoxteam.vscode-python-test-adapter"
  ]
}
```

### 6.2 VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.tabSize": 4
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*.pyc": true,
    "**/.venv": true,
    "**/.mypy_cache": true
  }
}
```

### 6.3 Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: vibe-coder CLI",
      "type": "python",
      "request": "launch",
      "module": "vibe_coder.cli",
      "args": ["--help"],
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

---

## 📚 Step 7: Python-Specific Resources (10 minutes)

### 7.1 Project Documentation

Same as TypeScript version - read:
1. `README.md`
2. `IMPLEMENTATION_PLAN_PYTHON.md`
3. `IMPLEMENTATION_PLAN_PYTHON_PART2.md`
4. `ROADMAP.md`

### 7.2 Python Libraries Used

**Core Libraries:**
- [Typer](https://typer.tiangolo.com/) - CLI framework (like Click but better)
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [Questionary](https://questionary.readthedocs.io/) - Interactive prompts
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [dynaconf](https://www.dynaconf.com/) - Configuration management

**AI SDKs:**
- [OpenAI Python](https://github.com/openai/openai-python)
- [Anthropic Python](https://github.com/anthropics/anthropic-sdk-python)

**Testing:**
- [pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

### 7.3 Python Best Practices

**Type Hints:**
```python
from typing import Optional, List, Dict

def process_data(
    items: List[str],
    config: Optional[Dict[str, str]] = None
) -> bool:
    """Process data with optional config."""
    pass
```

**Dataclasses:**
```python
from dataclasses import dataclass, field

@dataclass
class Config:
    """Application configuration."""
    name: str
    port: int = 8000
    features: List[str] = field(default_factory=list)
```

**Async/Await:**
```python
import asyncio

async def fetch_data(url: str) -> dict:
    """Fetch data asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Run async function
result = asyncio.run(fetch_data("https://api.example.com"))
```

---

## 🎯 Step 8: Pick Your First Real Task (10 minutes)

### 8.1 Junior-Friendly Tasks

**Phase 1 (Foundation):**
- ✅ Task 1.1: Initialize Python Project (Poetry setup)
- [ ] Task 1.2: Create Directory Structure
- [ ] Task 1.3: Install Core Dependencies

**Phase 2 (Configuration):**
- [ ] Task 2.1: Define Type Hints (dataclasses)
- [ ] Task 2.3: Create Environment Handler

**Phase 6 (Utilities):**
- ✅ Task 6.1: Logger Utility (DONE!)
- [ ] Task 6.2: Token Counter
- [ ] Task 6.4: File Operations

---

## 🎉 Step 9: You're Ready!

Congratulations! You've:
- ✅ Set up Python development environment
- ✅ Understood the project structure
- ✅ Completed your first task (logger)
- ✅ Written and ran tests
- ✅ Learned Poetry and pytest

### Key Differences from Node.js/TypeScript:

| Feature | TypeScript | Python |
|---------|-----------|--------|
| Package Manager | npm/yarn | poetry/pip |
| Type System | Built-in (TypeScript) | Optional (type hints) |
| Testing | Jest | pytest |
| Linting | ESLint | flake8/ruff |
| Formatting | Prettier | Black |
| Async | async/await | async/await (native) |
| CLI Framework | Commander.js | Typer |
| Colored Output | Chalk | Rich |

### Next Steps:

1. Join team communication
2. Pick your next task
3. Start coding!

---

## 📞 Common Issues

**Problem: Poetry not found after installation**
```bash
# Add to PATH (macOS/Linux)
export PATH="$HOME/.local/bin:$PATH"

# Or use pipx instead
pipx install poetry
```

**Problem: Wrong Python version**
```bash
# Tell Poetry which Python to use
poetry env use python3.9

# Or use pyenv to manage Python versions
pyenv install 3.9.16
pyenv local 3.9.16
```

**Problem: Import errors**
```bash
# Make sure you're in the virtual environment
poetry shell

# Or run with poetry
poetry run python script.py
```

**Problem: Tests not found**
```bash
# Install package in editable mode
poetry install

# Make sure __init__.py files exist
find tests -type d -exec touch {}/__init__.py \;
```

---

Good luck and happy coding! 🐍🚀
