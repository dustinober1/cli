"""
Pytest configuration and shared fixtures for Vibe Coder testing.

This module provides all the essential fixtures needed for comprehensive testing
of the Vibe Coder CLI, including mocking, file system setup, and test utilities.
"""

import asyncio
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
import httpx
from rich.console import Console

from vibe_coder.types.config import AIProvider, AppConfig, InteractionMode, ProviderType
from vibe_coder.types.api import (
    ApiMessage,
    MessageRole,
    ApiRequest,
    ApiResponse,
    TokenUsage,
)
from vibe_coder.config.manager import ConfigManager
from vibe_coder.api.base import BaseApiClient
from vibe_coder.api.factory import ClientFactory
from vibe_coder.commands.slash.parser import SlashCommandParser
from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.healing.auto_healer import AutoHealer
from vibe_coder.analytics.cost_tracker import CostTracker
from vibe_coder.plugins.manager import PluginManager


# =============================================================================
# Async Configuration Fixtures
# =============================================================================

# Note: Removed custom event_loop fixture to avoid conflicts with pytest-asyncio


@pytest_asyncio.fixture
async def temp_config_dir() -> AsyncGenerator[Path, None]:
    """Create a temporary directory for configuration files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="vibe_coder_test_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def config_manager(temp_config_dir: Path) -> ConfigManager:
    """Create a ConfigManager instance with a temporary directory."""
    config_path = temp_config_dir / "config.json"

    # Patch the default config path
    with patch("vibe_coder.config.manager.DEFAULT_CONFIG_PATH", str(config_path)):
        manager = ConfigManager()
        # Ensure clean state
        manager.config = AppConfig()
        await manager._save_config()
        yield manager


@pytest_asyncio.fixture
async def sample_provider() -> AIProvider:
    """Create a sample AI provider for testing."""
    return AIProvider(
        name="test-openai",
        api_key="sk-test-key-12345",
        endpoint="https://api.openai.com/v1",
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
        headers={"Content-Type": "application/json"},
    )


@pytest_asyncio.fixture
async def sample_provider_anthropic() -> AIProvider:
    """Create a sample Anthropic provider for testing."""
    return AIProvider(
        name="test-claude",
        api_key="sk-ant-test-key-67890",
        endpoint="https://api.anthropic.com",
        model="claude-3-sonnet-20240229",
        temperature=0.5,
        max_tokens=4000,
    )


@pytest_asyncio.fixture
async def config_manager_with_provider(
    config_manager: ConfigManager,
    sample_provider: AIProvider
) -> ConfigManager:
    """Create a ConfigManager instance with a pre-configured provider."""
    config_manager.set_provider(sample_provider.name, sample_provider)
    config_manager.set_current_provider(sample_provider.name)
    await config_manager._save_config()
    return config_manager


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="vibe_coder_test_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_project(temp_dir: Path) -> Path:
    """Create a sample Python project structure for testing."""
    # Create directory structure
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()
    (temp_dir / "docs").mkdir()
    (temp_dir / "scripts").mkdir()

    # Create __init__.py files
    (temp_dir / "src" / "__init__.py").touch()
    (temp_dir / "tests" / "__init__.py").touch()

    # Create sample modules
    (temp_dir / "src" / "main.py").write_text("""
def main():
    \"\"\"Main entry point.\"\"\"
    print("Hello, World!")
    return 0


if __name__ == "__main__":
    exit(main())
""")

    (temp_dir / "src" / "utils.py").write_text("""
def helper_function(value: int) -> int:
    \"\"\"A simple helper function.\"\"\"
    return value * 2


class UtilityClass:
    \"\"\"A sample utility class.\"\"\"

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"
""")

    (temp_dir / "src" / "data.py").write_text("""
# Data module
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None

@dataclass
class Post:
    id: int
    user_id: int
    title: str
    content: str
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
""")

    # Create test files
    (temp_dir / "tests" / "test_main.py").write_text("""
import pytest
from src.main import main

def test_main():
    \"\"\"Test main function.\"\"\"
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
""")

    (temp_dir / "tests" / "test_utils.py").write_text("""
from src.utils import helper_function, UtilityClass

def test_helper_function():
    assert helper_function(5) == 10

def test_utility_class():
    util = UtilityClass("Test")
    assert util.greet() == "Hello, Test!"
""")

    # Create configuration files
    (temp_dir / "pyproject.toml").write_text("""
[tool.poetry]
name = "test-project"
version = "0.1.0"
description = "A test project"

[tool.poetry.dependencies]
python = "^3.9"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""")

    (temp_dir / "README.md").write_text("""
# Test Project

This is a sample Python project for testing Vibe Coder functionality.

## Features

- Sample modules
- Unit tests
- Configuration files
""")

    # Create .gitignore
    (temp_dir / ".gitignore").write_text("""
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.venv/
venv/
""")

    return temp_dir


@pytest.fixture
def git_repository(sample_python_project: Path) -> Path:
    """Initialize a git repository in the sample project."""
    import subprocess

    # Run git commands
    subprocess.run(["git", "init"], cwd=sample_python_project, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=sample_python_project, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=sample_python_project, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=sample_python_project, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=sample_python_project, capture_output=True)

    # Create a feature branch
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=sample_python_project, capture_output=True)

    # Make some changes
    (sample_python_project / "src" / "feature.py").write_text("""
def new_feature():
    \"\"\"A new feature function.\"\"\"
    return "New feature working!"
""")

    (sample_python_project / "README.md").write_text("""
# Test Project

This is a sample Python project for testing Vibe Coder functionality.

## Features

- Sample modules
- Unit tests
- Configuration files
- New feature branch with additional code
""")

    subprocess.run(["git", "add", "."], cwd=sample_python_project, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add new feature"], cwd=sample_python_project, capture_output=True)

    # Go back to main
    subprocess.run(["git", "checkout", "main"], cwd=sample_python_project, capture_output=True)

    return sample_python_project


# =============================================================================
# AI Mocking Fixtures
# =============================================================================

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = AsyncMock(spec=BaseApiClient)

    # Mock response
    mock_response = ApiResponse(
        content="This is a mock OpenAI response",
        usage=TokenUsage(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25
        ),
        finish_reason="stop"
    )

    client.send_request.return_value = mock_response

    # Mock streaming
    async def mock_stream(messages):
        yield "This "
        yield "is "
        yield "a "
        yield "mock "
        yield "streaming "
        yield "response"

    client.stream_request = mock_stream

    # Mock validation
    client.validate_connection.return_value = True

    return client


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = AsyncMock(spec=BaseApiClient)

    # Mock response (slightly different for Anthropic)
    mock_response = ApiResponse(
        content="This is a mock Claude response",
        usage=TokenUsage(
            prompt_tokens=12,
            completion_tokens=18,
            total_tokens=30
        ),
        finish_reason="end_turn"
    )

    client.send_request.return_value = mock_response

    # Mock streaming
    async def mock_stream(messages):
        yield "Claude "
        yield "mock "
        yield "streaming "
        yield "response"

    client.stream_request = mock_stream

    # Mock validation
    client.validate_connection.return_value = True

    return client


@pytest.fixture
def mock_generic_client():
    """Create a mock generic OpenAI-compatible client."""
    client = AsyncMock(spec=BaseApiClient)

    # Mock response
    mock_response = ApiResponse(
        content="This is a mock generic API response",
        usage=TokenUsage(
            prompt_tokens=8,
            completion_tokens=12,
            total_tokens=20
        ),
        finish_reason="stop"
    )

    client.send_request.return_value = mock_response

    # Mock streaming
    async def mock_stream(messages):
        yield "Generic "
        yield "API "
        yield "mock "
        yield "response"

    client.stream_request = mock_stream

    # Mock validation
    client.validate_connection.return_value = True

    return client


@pytest.fixture
def mock_provider():
    """Create a mock AI provider configuration."""
    return {
        "name": "mock-provider",
        "api_key": "mock-api-key-12345",
        "endpoint": "https://api.mock.com/v1",
        "model": "mock-model",
        "temperature": 0.7,
        "max_tokens": 1000,
        "headers": {"Content-Type": "application/json"},
    }


@pytest.fixture
def mock_ai_response():
    """Create a mock AI response for testing."""
    return ApiResponse(
        content="Here's the solution to your problem:\n\n```python\ndef solution():\n    return 'success'\n```",
        usage=TokenUsage(
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80
        ),
        finish_reason="stop"
    )


@pytest.fixture
def mock_api_messages():
    """Create a list of mock API messages for testing."""
    return [
        ApiMessage(role=MessageRole.SYSTEM, content="You are a helpful AI assistant."),
        ApiMessage(role=MessageRole.USER, content="Write a Python function to add two numbers."),
        ApiMessage(role=MessageRole.ASSISTANT, content="Here's a simple function:\n\n```python\ndef add(a, b):\n    return a + b\n```"),
    ]


# =============================================================================
# Command Context Fixtures
# =============================================================================

@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    console = MagicMock(spec=Console)
    console.print = MagicMock()
    console.input = MagicMock(return_value="test input")
    console.rule = MagicMock()
    console.panel = MagicMock()
    console.table = MagicMock()
    console.status = MagicMock()
    console.progress = MagicMock()
    return console


@pytest.fixture
def slash_command_parser():
    """Create a SlashCommandParser instance for testing."""
    return SlashCommandParser()


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for testing command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Command executed successfully"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for API testing."""
    client = MagicMock(spec=httpx.AsyncClient)

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "data": "test data"}
    mock_response.text = "Success response"
    client.get.return_value = mock_response
    client.post.return_value = mock_response

    return client


# =============================================================================
# Questionary Mocking Fixtures
# =============================================================================

@pytest.fixture
def mock_questionary():
    """Mock questionary prompts for testing interactive commands."""
    with patch("questionary.prompt") as mock_prompt:
        # Mock different prompt types
        mock_prompt.return_value = {
            "name": "test-provider",
            "api_key": "sk-test-key-12345",
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "confirm": True,
            "choice": "openai",
            "select": "Option 1",
            "checkbox": ["option1", "option2"],
            "text": "user input text",
            "password": "secret password",
            "path": "/path/to/file",
            "confirm_save": True,
        }

        # Mock individual prompt functions
        with patch("questionary.text") as mock_text, \
             patch("questionary.password") as mock_password, \
             patch("questionary.select") as mock_select, \
             patch("questionary.checkbox") as mock_checkbox, \
             patch("questionary.confirm") as mock_confirm, \
             patch("questionary.path") as mock_path:

            mock_text.return_value.ask.return_value = "test input"
            mock_password.return_value.ask.return_value = "password"
            mock_select.return_value.ask.return_value = "Selected option"
            mock_checkbox.return_value.ask.return_value = ["option1"]
            mock_confirm.return_value.ask.return_value = True
            mock_path.return_value.ask.return_value = "/path/to/file"

            yield mock_prompt


@pytest.fixture
def mock_wizard_responses():
    """Provide mock responses for the setup wizard."""
    return {
        "provider_type": "openai",
        "provider_name": "test-openai",
        "api_key": "sk-test-key-123456789",
        "endpoint": "https://api.openai.com/v1",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "save_to_env": False,
        "set_as_default": True,
    }


# =============================================================================
# Intelligence Module Fixtures
# =============================================================================

@pytest.fixture
def repository_mapper(sample_python_project: Path):
    """Create a RepositoryMapper instance for testing."""
    return RepositoryMapper(sample_python_project)


@pytest.fixture
def sample_ast_data():
    """Provide sample AST data for testing."""
    return {
        "functions": [
            {
                "name": "main",
                "module": "src.main",
                "line": 2,
                "docstring": "Main entry point.",
                "args": [],
                "returns": None,
            },
            {
                "name": "helper_function",
                "module": "src.utils",
                "line": 2,
                "docstring": "A simple helper function.",
                "args": [{"name": "value", "type": "int"}],
                "returns": "int",
            },
        ],
        "classes": [
            {
                "name": "UtilityClass",
                "module": "src.utils",
                "line": 7,
                "docstring": "A sample utility class.",
                "methods": [
                    {
                        "name": "greet",
                        "line": 13,
                        "docstring": None,
                        "args": [],
                        "returns": "str",
                    }
                ],
            }
        ],
        "imports": [
            {"module": "dataclasses", "from_module": None, "names": ["dataclass"]},
            {"module": "typing", "from_module": None, "names": ["List", "Optional"]},
        ],
        "dependencies": {
            "src.main": [],
            "src.utils": [],
            "src.data": ["dataclasses", "typing"],
        },
    }


# =============================================================================
# Healing Module Fixtures
# =============================================================================

@pytest.fixture
def auto_healer(sample_python_project: Path):
    """Create an AutoHealer instance for testing."""
    return AutoHealer(sample_python_project)


@pytest.fixture
def error_snippet():
    """Provide a code snippet with an error for testing."""
    return '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    # Missing error handling for empty list
    return total / count  # Will raise ZeroDivisionError for empty list
'''


@pytest.fixture
def fixed_snippet():
    """Provide the fixed version of the error snippet."""
    return '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0  # Handle empty list case
    total = sum(numbers)
    count = len(numbers)
    return total / count
'''


# =============================================================================
# Analytics Module Fixtures
# =============================================================================

@pytest.fixture
def cost_tracker():
    """Create a CostTracker instance for testing."""
    return CostTracker()


@pytest.fixture
def sample_usage_data():
    """Provide sample usage data for testing."""
    return {
        "openai": {
            "requests": 10,
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "cost": 0.045,
        },
        "anthropic": {
            "requests": 5,
            "prompt_tokens": 800,
            "completion_tokens": 400,
            "total_tokens": 1200,
            "cost": 0.036,
        },
    }


# =============================================================================
# Plugin System Fixtures
# =============================================================================

@pytest.fixture
def plugin_manager():
    """Create a PluginManager instance for testing."""
    return PluginManager()


@pytest.fixture
def sample_plugin_code():
    """Provide sample plugin code for testing."""
    return '''
from vibe_coder.plugins.base import BaseAnalyzerPlugin

class CustomAnalyzer(BaseAnalyzerPlugin):
    """A custom analyzer plugin for testing."""

    name = "custom_analyzer"
    version = "1.0.0"
    description = "A test analyzer plugin"

    def analyze(self, file_path: str) -> dict:
        """Analyze a file and return metrics."""
        return {
            "file": file_path,
            "lines": 100,
            "functions": 5,
            "classes": 2,
        }
'''


# =============================================================================
# Test Utilities
# =============================================================================

@pytest.fixture
def create_test_file():
    """Utility fixture to create test files dynamically."""
    created_files = []

    def _create_file(path: Path, content: str = ""):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        created_files.append(path)
        return path

    yield _create_file

    # Cleanup created files
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()


@pytest.fixture
def assert_files_equal():
    """Utility to compare file contents."""
    def _assert_equal(file1: Path, file2: Path):
        assert file1.exists(), f"File {file1} does not exist"
        assert file2.exists(), f"File {file2} does not exist"
        assert file1.read_text() == file2.read_text(), f"Files {file1} and {file2} differ"

    return _assert_equal


@pytest.fixture
def capture_console_output():
    """Capture Rich console output for testing."""
    from io import StringIO
    from rich.console import Console

    console = Console(file=StringIO(), width=80)
    yield console
    captured = console.file.getvalue()
    return captured


# =============================================================================
# Markers and Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers",
        "unit: Mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: Mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: Mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "network: Mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers",
        "github: Mark test as requiring GitHub API access"
    )


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically clean up temporary files after each test."""
    temp_files = []

    yield

    # Clean up any temp files created during test
    for temp_file in temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except Exception:
            pass