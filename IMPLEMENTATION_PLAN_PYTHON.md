# CLI Vibe Coder - Python Implementation Plan

## Project Overview
A standalone command-line AI coding assistant built with Python that allows users to configure any AI API endpoint and API key, installable via pip/pipx.

## Project Goals
- Create a CLI tool that works with any AI API provider (OpenAI, Anthropic, local LLMs, etc.)
- Allow users to configure API endpoints and keys through interactive prompts or config files
- Provide an intuitive coding assistant interface
- Make it installable via `pip install` or `pipx install`
- Support multiple environment configurations
- Leverage Python's strengths: built-in AST parsing, rich AI ecosystem, excellent CLI libraries

---

## Phase 1: Project Foundation & Setup

### Task 1.1: Initialize Python Project with Poetry
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**Steps:**
1. Install Poetry (if not installed): `curl -sSL https://install.python-poetry.org | python3 -`
2. Create new project: `poetry new vibe-coder`
3. Update `pyproject.toml`:
   ```toml
   [tool.poetry]
   name = "vibe-coder"
   version = "0.1.0"
   description = "A configurable CLI coding assistant that works with any AI API"
   authors = ["Your Name <your.email@example.com>"]
   license = "MIT"
   readme = "README.md"
   homepage = "https://github.com/yourusername/vibe-coder"
   repository = "https://github.com/yourusername/vibe-coder"
   keywords = ["cli", "ai", "coding-assistant", "openai", "anthropic"]

   [tool.poetry.dependencies]
   python = "^3.9"

   [tool.poetry.scripts]
   vibe-coder = "vibe_coder.cli:main"
   ```

4. Initialize git repository
5. Create `.gitignore` for Python

**Acceptance Criteria:**
- `pyproject.toml` exists with correct metadata
- Poetry environment is set up
- Git repository initialized

---

### Task 1.2: Create Project Directory Structure
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**Steps:**
1. Create `vibe_coder/` directory (main package)
2. Create `vibe_coder/commands/` directory
3. Create `vibe_coder/config/` directory
4. Create `vibe_coder/api/` directory
5. Create `vibe_coder/utils/` directory
6. Create `vibe_coder/prompts/` directory
7. Create `vibe_coder/types/` directory
8. Create `tests/` directory
9. Create `examples/` directory
10. Add `__init__.py` to all package directories

**Directory Structure:**
```
vibe-coder/
├── vibe_coder/
│   ├── __init__.py
│   ├── cli.py                    # Main CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── setup.py
│   │   ├── config.py
│   │   ├── test.py
│   │   └── slash/
│   │       ├── __init__.py
│   │       ├── core.py
│   │       ├── files.py
│   │       ├── coding.py
│   │       ├── editor.py
│   │       ├── model.py
│   │       ├── git.py
│   │       └── advanced.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── env_handler.py
│   │   └── validator.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   ├── generic_client.py
│   │   └── client_factory.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── setup_wizard.py
│   │   ├── select_provider.py
│   │   ├── chat_interface.py
│   │   └── manage_config.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── error_handler.py
│   │   ├── token_counter.py
│   │   ├── code_formatter.py
│   │   ├── file_ops.py
│   │   ├── repo_mapper.py
│   │   ├── apply_engine.py
│   │   └── context_manager.py
│   ├── rag/
│   │   ├── __init__.py
│   │   └── vector_store.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── mcp_client.py
│   └── agents/
│       ├── __init__.py
│       └── auto_healer.py
├── tests/
│   ├── __init__.py
│   ├── test_config/
│   ├── test_api/
│   ├── test_utils/
│   └── test_integration/
├── examples/
├── docs/
├── pyproject.toml
├── poetry.lock
├── README.md
└── .gitignore
```

**Acceptance Criteria:**
- All directories exist
- All `__init__.py` files present
- Structure matches specification

---

### Task 1.3: Install Core Dependencies
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**Steps:**
1. Add CLI framework: `poetry add typer[all]` (includes Rich for formatting)
2. Add interactive prompts: `poetry add questionary`
3. Add HTTP client: `poetry add httpx`
4. Add environment variables: `poetry add python-dotenv`
5. Add config management: `poetry add dynaconf`
6. Add progress indicators (included in typer[all])
7. Add OpenAI SDK: `poetry add openai`
8. Add Anthropic SDK: `poetry add anthropic`

**Development dependencies:**
```bash
poetry add --group dev pytest pytest-cov pytest-asyncio black flake8 mypy isort
```

**Acceptance Criteria:**
- All dependencies in `pyproject.toml`
- `poetry install` runs without errors
- Virtual environment created

---

### Task 1.4: Set Up Python Tooling Configuration
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**Steps:**
1. Create `pyproject.toml` configurations:

```toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=vibe_coder --cov-report=term-missing"
```

2. Create `.flake8`:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = .git,__pycache__,dist,build,.venv
```

3. Create `Makefile` for common tasks:
```makefile
.PHONY: install test lint format clean

install:
	poetry install

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=vibe_coder --cov-report=html

lint:
	poetry run flake8 vibe_coder tests
	poetry run mypy vibe_coder

format:
	poetry run black vibe_coder tests
	poetry run isort vibe_coder tests

clean:
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

**Acceptance Criteria:**
- Linting and formatting tools configured
- `make format` and `make lint` work
- Type checking enabled

---

### Task 1.5: Create Main CLI Entry Point
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/cli.py`

**Steps:**
1. Import Typer and create app:
```python
import typer
from typing import Optional
from rich.console import Console

app = typer.Typer(
    name="vibe-coder",
    help="A configurable CLI coding assistant that works with any AI API",
    add_completion=True,
)
console = Console()

@app.command()
def chat(
    provider: Optional[str] = typer.Option(None, help="Provider name to use"),
    model: Optional[str] = typer.Option(None, help="Model to use"),
    temperature: Optional[float] = typer.Option(None, help="Temperature (0.0-2.0)"),
):
    """Start an interactive chat session."""
    console.print("Chat command - to be implemented", style="yellow")

@app.command()
def setup():
    """Run the setup wizard to configure providers."""
    console.print("Setup command - to be implemented", style="yellow")

def main():
    app()

if __name__ == "__main__":
    main()
```

2. Test CLI works:
```bash
poetry run vibe-coder --help
```

**Acceptance Criteria:**
- CLI runs without errors
- `--help` shows commands
- Basic commands defined

---

## Phase 2: Configuration System

### Task 2.1: Define Python Type Hints and Models
**Difficulty:** Junior-friendly
**Estimated Complexity:** Medium

**File:** `vibe_coder/types/config.py`

**Steps:**
1. Use dataclasses and type hints:

```python
from dataclasses import dataclass, field
from typing import Optional, Dict
from enum import Enum

class InteractionMode(Enum):
    """Available interaction modes."""
    CODE = "code"
    ARCHITECT = "architect"
    ASK = "ask"
    AUDIT = "audit"

@dataclass
class AIProvider:
    """Configuration for an AI provider."""
    name: str
    api_key: str
    endpoint: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Validate provider configuration."""
        if self.temperature and not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")

@dataclass
class AppConfig:
    """Application configuration."""
    current_provider: str
    providers: Dict[str, AIProvider] = field(default_factory=dict)
    default_model: Optional[str] = None
    default_temperature: float = 0.7
    default_max_tokens: Optional[int] = None
    offline_mode: bool = False
    debug_mode: bool = False

    def get_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """Get provider by name or current provider."""
        provider_name = name or self.current_provider
        return self.providers.get(provider_name)
```

2. Create API types in `vibe_coder/types/api.py`:

```python
from dataclasses import dataclass
from typing import List, Optional, Literal
from enum import Enum

class MessageRole(Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ApiMessage:
    """A message in the conversation."""
    role: MessageRole
    content: str

@dataclass
class TokenUsage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class ApiRequest:
    """Request to AI API."""
    messages: List[ApiMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False

@dataclass
class ApiResponse:
    """Response from AI API."""
    content: str
    model: Optional[str] = None
    usage: Optional[TokenUsage] = None
    finish_reason: Optional[str] = None
```

**Acceptance Criteria:**
- Types are well-documented
- Validation in `__post_init__`
- Exports work correctly

---

### Task 2.2: Create Configuration Manager
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/config/manager.py`

**Steps:**
1. Use dynaconf for configuration management:

```python
from pathlib import Path
from typing import Optional, Dict, List
import json
from dynaconf import Dynaconf
from vibe_coder.types.config import AIProvider, AppConfig

class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or Path.home() / ".vibe"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        # Initialize dynaconf
        self.settings = Dynaconf(
            settings_files=[str(self.config_file)],
            environments=True,
        )

        # Load or create default config
        if not self.config_file.exists():
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "current_provider": "",
            "providers": {},
            "offline_mode": False,
            "debug_mode": False,
        }
        self._save_config(default_config)

    def _save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get provider by name."""
        config = self._load_config()
        provider_data = config.get("providers", {}).get(name)
        if provider_data:
            return AIProvider(**provider_data)
        return None

    def set_provider(self, name: str, provider: AIProvider) -> None:
        """Save provider configuration."""
        config = self._load_config()
        if "providers" not in config:
            config["providers"] = {}

        # Convert dataclass to dict
        config["providers"][name] = {
            "name": provider.name,
            "api_key": provider.api_key,
            "endpoint": provider.endpoint,
            "model": provider.model,
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens,
            "headers": provider.headers,
        }
        self._save_config(config)

    def get_current_provider(self) -> Optional[AIProvider]:
        """Get the currently active provider."""
        config = self._load_config()
        current_name = config.get("current_provider")
        if current_name:
            return self.get_provider(current_name)
        return None

    def set_current_provider(self, name: str) -> None:
        """Set the current active provider."""
        config = self._load_config()
        config["current_provider"] = name
        self._save_config(config)

    def list_providers(self) -> List[str]:
        """List all configured provider names."""
        config = self._load_config()
        return list(config.get("providers", {}).keys())

    def delete_provider(self, name: str) -> None:
        """Delete a provider configuration."""
        config = self._load_config()
        if name in config.get("providers", {}):
            del config["providers"][name]
            if config.get("current_provider") == name:
                config["current_provider"] = ""
            self._save_config(config)

    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._create_default_config()

# Singleton instance
config_manager = ConfigManager()
```

**Acceptance Criteria:**
- Configuration persists between runs
- All methods work correctly
- Error handling in place
- Thread-safe operations

---

### Task 2.3: Create Environment Variable Handler
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**File:** `vibe_coder/config/env_handler.py`

**Steps:**
1. Use python-dotenv:

```python
import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv, set_key
from vibe_coder.types.config import AIProvider

def load_env_config() -> Optional[Dict[str, str]]:
    """Load configuration from environment variables."""
    # Load from .env file if exists
    load_dotenv()

    config = {}

    # Check for vibe-coder specific env vars
    if api_key := os.getenv("VIBE_CODER_API_KEY"):
        config["api_key"] = api_key

    if endpoint := os.getenv("VIBE_CODER_ENDPOINT"):
        config["endpoint"] = endpoint

    if model := os.getenv("VIBE_CODER_MODEL"):
        config["model"] = model

    if temperature := os.getenv("VIBE_CODER_TEMPERATURE"):
        try:
            config["temperature"] = float(temperature)
        except ValueError:
            pass

    return config if config else None

def save_to_env(values: Dict[str, str], env_path: Optional[Path] = None) -> None:
    """Save configuration values to .env file."""
    if env_path is None:
        env_path = Path.cwd() / ".env"

    # Create .env if it doesn't exist
    env_path.touch(exist_ok=True)

    # Set values
    for key, value in values.items():
        env_key = f"VIBE_CODER_{key.upper()}"
        set_key(str(env_path), env_key, str(value))

    print(f"⚠️  Configuration saved to {env_path}")
    print("⚠️  WARNING: Do not commit .env files to version control!")

def get_env_provider() -> Optional[AIProvider]:
    """Get provider configuration from environment variables."""
    config = load_env_config()
    if not config:
        return None

    if "api_key" not in config or "endpoint" not in config:
        return None

    return AIProvider(
        name="env-provider",
        api_key=config["api_key"],
        endpoint=config["endpoint"],
        model=config.get("model"),
        temperature=config.get("temperature", 0.7),
    )
```

**Acceptance Criteria:**
- Reads .env files correctly
- Environment variables are parsed
- Handles missing files gracefully
- Security warnings displayed

---

### Task 2.4: Create Configuration Validator
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/config/validator.py`

**Steps:**
1. Create validation functions:

```python
from typing import List
from urllib.parse import urlparse
import re
from vibe_coder.types.config import AIProvider

def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key or not isinstance(api_key, str):
        return False

    # Must be at least 10 characters
    if len(api_key) < 10:
        return False

    # Should not contain spaces
    if ' ' in api_key:
        return False

    return True

def validate_endpoint(endpoint: str) -> bool:
    """Validate endpoint URL."""
    if not endpoint or not isinstance(endpoint, str):
        return False

    try:
        result = urlparse(endpoint)
        # Must have scheme and netloc
        if not all([result.scheme, result.netloc]):
            return False

        # Must be http or https
        if result.scheme not in ['http', 'https']:
            return False

        return True
    except Exception:
        return False

def validate_temperature(temperature: float) -> bool:
    """Validate temperature value."""
    try:
        temp = float(temperature)
        return 0.0 <= temp <= 2.0
    except (ValueError, TypeError):
        return False

def validate_provider(provider: AIProvider) -> List[str]:
    """
    Validate provider configuration.

    Returns:
        List of error messages. Empty list means valid.
    """
    errors = []

    if not provider.name:
        errors.append("Provider name is required")

    if not validate_api_key(provider.api_key):
        errors.append(
            "API key must be at least 10 characters and contain no spaces"
        )

    if not validate_endpoint(provider.endpoint):
        errors.append(
            "Endpoint must be a valid HTTP/HTTPS URL"
        )

    if provider.temperature is not None:
        if not validate_temperature(provider.temperature):
            errors.append(
                "Temperature must be between 0.0 and 2.0"
            )

    if provider.max_tokens is not None:
        if not isinstance(provider.max_tokens, int) or provider.max_tokens < 1:
            errors.append(
                "Max tokens must be a positive integer"
            )

    return errors

def is_localhost(url: str) -> bool:
    """Check if URL is localhost."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in ['localhost', '127.0.0.1', '::1'] or \
               hostname.startswith('192.168.') or \
               hostname.startswith('10.')
    except Exception:
        return False
```

**Acceptance Criteria:**
- All validation functions work
- Return meaningful error messages
- Handle edge cases
- Type hints are correct

---

## Phase 3: API Integration Layer

### Task 3.1: Create Base API Client
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/api/base_client.py`

**Steps:**
1. Create abstract base class:

```python
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from vibe_coder.types.api import ApiRequest, ApiResponse, ApiMessage
from vibe_coder.types.config import AIProvider

class BaseApiClient(ABC):
    """Abstract base class for AI API clients."""

    def __init__(self, provider: AIProvider):
        """Initialize API client with provider configuration."""
        self.provider = provider
        self.api_key = provider.api_key
        self.endpoint = provider.endpoint
        self.model = provider.model

    @abstractmethod
    async def send_request(self, request: ApiRequest) -> ApiResponse:
        """
        Send a request to the AI API.

        Args:
            request: The API request to send

        Returns:
            API response with generated content
        """
        pass

    @abstractmethod
    async def stream_request(
        self,
        request: ApiRequest
    ) -> AsyncIterator[str]:
        """
        Send a streaming request to the AI API.

        Args:
            request: The API request to send

        Yields:
            Chunks of the generated response
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that the API connection works.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    def format_error(self, error: Exception) -> str:
        """
        Format an error message for display.

        Args:
            error: The exception to format

        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_msg = str(error)

        return f"❌ {error_type}: {error_msg}"

    def _get_model(self, request_model: Optional[str] = None) -> str:
        """Get the model to use for this request."""
        return request_model or self.model or "default"

    def _get_temperature(
        self,
        request_temp: Optional[float] = None
    ) -> float:
        """Get the temperature to use for this request."""
        return request_temp or self.provider.temperature or 0.7
```

**Acceptance Criteria:**
- Abstract methods defined
- Base functionality implemented
- Async/await support
- Type hints complete

---

### Task 3.2: Create OpenAI API Client
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/api/openai_client.py`

**Steps:**
1. Use OpenAI Python SDK:

```python
from typing import AsyncIterator, Optional
import openai
from openai import AsyncOpenAI
from vibe_coder.api.base_client import BaseApiClient
from vibe_coder.types.api import ApiRequest, ApiResponse, ApiMessage, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider

class OpenAIClient(BaseApiClient):
    """OpenAI API client implementation."""

    def __init__(self, provider: AIProvider):
        """Initialize OpenAI client."""
        super().__init__(provider)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.endpoint if self.endpoint != "https://api.openai.com/v1" else None,
        )

    def _format_messages(self, messages: list[ApiMessage]) -> list[dict]:
        """Convert ApiMessage to OpenAI format."""
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]

    async def send_request(self, request: ApiRequest) -> ApiResponse:
        """Send request to OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self._get_model(request.model),
                messages=self._format_messages(request.messages),
                temperature=self._get_temperature(request.temperature),
                max_tokens=request.max_tokens,
                stream=False,
            )

            # Extract response
            content = response.choices[0].message.content or ""
            usage = None
            if response.usage:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            return ApiResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
            )

        except Exception as e:
            raise Exception(self.format_error(e))

    async def stream_request(self, request: ApiRequest) -> AsyncIterator[str]:
        """Stream response from OpenAI API."""
        try:
            stream = await self.client.chat.completions.create(
                model=self._get_model(request.model),
                messages=self._format_messages(request.messages),
                temperature=self._get_temperature(request.temperature),
                max_tokens=request.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise Exception(self.format_error(e))

    async def validate_connection(self) -> bool:
        """Validate OpenAI API connection."""
        try:
            # Try to list models
            await self.client.models.list()
            return True
        except Exception:
            return False
```

**Acceptance Criteria:**
- Implements all abstract methods
- Uses official OpenAI SDK
- Handles errors properly
- Supports streaming
- API key never logged

---

### Task 3.3: Create Anthropic API Client
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/api/anthropic_client.py`

**Steps:**
1. Use Anthropic Python SDK:

```python
from typing import AsyncIterator
import anthropic
from vibe_coder.api.base_client import BaseApiClient
from vibe_coder.types.api import ApiRequest, ApiResponse, ApiMessage, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider

class AnthropicClient(BaseApiClient):
    """Anthropic API client implementation."""

    def __init__(self, provider: AIProvider):
        """Initialize Anthropic client."""
        super().__init__(provider)

        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.endpoint if self.endpoint != "https://api.anthropic.com/v1" else None,
        )

    def _format_messages(self, messages: list[ApiMessage]) -> tuple[str, list[dict]]:
        """
        Convert ApiMessage to Anthropic format.

        Returns:
            Tuple of (system_prompt, messages)
        """
        system_prompt = ""
        formatted_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        return system_prompt, formatted_messages

    async def send_request(self, request: ApiRequest) -> ApiResponse:
        """Send request to Anthropic API."""
        try:
            system_prompt, messages = self._format_messages(request.messages)

            response = await self.client.messages.create(
                model=self._get_model(request.model) or "claude-3-5-sonnet-20241022",
                system=system_prompt if system_prompt else None,
                messages=messages,
                temperature=self._get_temperature(request.temperature),
                max_tokens=request.max_tokens or 4096,
            )

            # Extract response
            content = response.content[0].text if response.content else ""
            usage = TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return ApiResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.stop_reason,
            )

        except Exception as e:
            raise Exception(self.format_error(e))

    async def stream_request(self, request: ApiRequest) -> AsyncIterator[str]:
        """Stream response from Anthropic API."""
        try:
            system_prompt, messages = self._format_messages(request.messages)

            async with self.client.messages.stream(
                model=self._get_model(request.model) or "claude-3-5-sonnet-20241022",
                system=system_prompt if system_prompt else None,
                messages=messages,
                temperature=self._get_temperature(request.temperature),
                max_tokens=request.max_tokens or 4096,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise Exception(self.format_error(e))

    async def validate_connection(self) -> bool:
        """Validate Anthropic API connection."""
        try:
            # Try a minimal request
            system_prompt, messages = self._format_messages([
                ApiMessage(role=MessageRole.USER, content="Hi")
            ])

            await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=messages,
                max_tokens=10,
            )
            return True
        except Exception:
            return False
```

**Acceptance Criteria:**
- Implements all abstract methods
- Uses official Anthropic SDK
- Handles system prompts correctly
- Supports streaming
- Error handling works

---

### Task 3.4: Create Generic/Custom API Client
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `vibe_coder/api/generic_client.py`

**Steps:**
1. Create flexible client for any OpenAI-compatible API:

```python
from typing import AsyncIterator, Optional, Dict, Any
import httpx
from vibe_coder.api.base_client import BaseApiClient
from vibe_coder.types.api import ApiRequest, ApiResponse, ApiMessage, TokenUsage
from vibe_coder.types.config import AIProvider

class GenericClient(BaseApiClient):
    """Generic API client for OpenAI-compatible endpoints."""

    def __init__(self, provider: AIProvider):
        """Initialize generic client."""
        super().__init__(provider)
        self.http_client = httpx.AsyncClient(timeout=60.0)

    def _format_messages_openai(self, messages: list[ApiMessage]) -> list[dict]:
        """Format messages in OpenAI style."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Add custom headers if provided
        if self.provider.headers:
            headers.update(self.provider.headers)

        return headers

    async def send_request(self, request: ApiRequest) -> ApiResponse:
        """Send request to generic API endpoint."""
        try:
            # Build request payload (OpenAI format)
            payload = {
                "model": self._get_model(request.model),
                "messages": self._format_messages_openai(request.messages),
                "temperature": self._get_temperature(request.temperature),
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            # Make request
            response = await self.http_client.post(
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers=self._build_headers(),
            )
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Try to extract content (OpenAI format)
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                elif "text" in choice:
                    content = choice["text"]

            # Try to extract usage
            usage = None
            if "usage" in data:
                usage_data = data["usage"]
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )

            return ApiResponse(
                content=content,
                model=data.get("model"),
                usage=usage,
                finish_reason=data.get("choices", [{}])[0].get("finish_reason"),
            )

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(self.format_error(e))

    async def stream_request(self, request: ApiRequest) -> AsyncIterator[str]:
        """Stream response from generic API endpoint."""
        try:
            payload = {
                "model": self._get_model(request.model),
                "messages": self._format_messages_openai(request.messages),
                "temperature": self._get_temperature(request.temperature),
                "stream": True,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            async with self.http_client.stream(
                "POST",
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            import json
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            raise Exception(self.format_error(e))

    async def validate_connection(self) -> bool:
        """Validate generic API connection."""
        try:
            response = await self.http_client.get(
                self.endpoint,
                headers=self._build_headers(),
            )
            return response.status_code < 500
        except Exception:
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
```

**Acceptance Criteria:**
- Works with any OpenAI-compatible endpoint
- Handles custom headers
- Supports streaming
- Error handling comprehensive
- Async context manager support

---

### Task 3.5: Create API Client Factory
**Difficulty:** Medium
**Estimated Complexity:** Simple

**File:** `vibe_coder/api/client_factory.py`

**Steps:**
1. Create factory to instantiate correct client:

```python
from vibe_coder.api.base_client import BaseApiClient
from vibe_coder.api.openai_client import OpenAIClient
from vibe_coder.api.anthropic_client import AnthropicClient
from vibe_coder.api.generic_client import GenericClient
from vibe_coder.types.config import AIProvider

def create_client(provider: AIProvider) -> BaseApiClient:
    """
    Create appropriate API client based on provider configuration.

    Args:
        provider: Provider configuration

    Returns:
        Initialized API client
    """
    endpoint_lower = provider.endpoint.lower()

    # Detect provider type from endpoint
    if "openai.com" in endpoint_lower:
        return OpenAIClient(provider)
    elif "anthropic.com" in endpoint_lower:
        return AnthropicClient(provider)
    elif "localhost" in endpoint_lower or "127.0.0.1" in endpoint_lower:
        # Local endpoints (Ollama, LM Studio, etc.)
        return GenericClient(provider)
    else:
        # Default to generic client for unknown endpoints
        return GenericClient(provider)

def detect_provider_type(endpoint: str) -> str:
    """
    Detect provider type from endpoint URL.

    Args:
        endpoint: API endpoint URL

    Returns:
        Provider type: 'openai', 'anthropic', 'ollama', 'generic'
    """
    endpoint_lower = endpoint.lower()

    if "openai.com" in endpoint_lower:
        return "openai"
    elif "anthropic.com" in endpoint_lower:
        return "anthropic"
    elif "localhost:11434" in endpoint_lower or "ollama" in endpoint_lower:
        return "ollama"
    elif "localhost:1234" in endpoint_lower:
        return "lm-studio"
    elif "localhost" in endpoint_lower or "127.0.0.1" in endpoint_lower:
        return "local"
    else:
        return "generic"
```

**Acceptance Criteria:**
- Correctly identifies provider types
- Returns appropriate client
- Handles unknown providers
- Well-documented

---

## Phase 4: Interactive Prompts & User Interface

### Task 4.1: Create Setup Wizard
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/prompts/setup_wizard.py`

**Steps:**
1. Use questionary for interactive prompts:

```python
import questionary
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from vibe_coder.types.config import AIProvider
from vibe_coder.config.validator import validate_api_key, validate_endpoint

console = Console()

async def run_setup_wizard() -> AIProvider:
    """
    Run interactive setup wizard to configure a provider.

    Returns:
        Configured AIProvider
    """
    console.print(Panel.fit(
        "[bold cyan]Vibe Coder Setup Wizard[/bold cyan]\n"
        "Let's configure your AI provider",
        border_style="cyan"
    ))

    # Provider name
    name = await questionary.text(
        "Provider name (e.g., 'my-openai', 'local-ollama'):",
        validate=lambda x: len(x) > 0 or "Name cannot be empty"
    ).ask_async()

    # Provider type selection
    provider_type = await questionary.select(
        "Select provider type:",
        choices=[
            "OpenAI",
            "Anthropic (Claude)",
            "Ollama (Local)",
            "LM Studio (Local)",
            "Custom endpoint"
        ]
    ).ask_async()

    # Set default endpoint based on type
    default_endpoints = {
        "OpenAI": "https://api.openai.com/v1",
        "Anthropic (Claude)": "https://api.anthropic.com/v1",
        "Ollama (Local)": "http://localhost:11434/v1",
        "LM Studio (Local)": "http://localhost:1234/v1",
        "Custom endpoint": ""
    }

    endpoint = await questionary.text(
        "API endpoint:",
        default=default_endpoints.get(provider_type, ""),
        validate=lambda x: validate_endpoint(x) or "Invalid URL format"
    ).ask_async()

    # API key
    needs_key = not ("localhost" in endpoint or "127.0.0.1" in endpoint)
    api_key = ""

    if needs_key:
        api_key = await questionary.password(
            "API key:",
            validate=lambda x: validate_api_key(x) or "Invalid API key"
        ).ask_async()
    else:
        api_key = "not-needed"
        console.print("[dim]Local endpoint detected, API key not required[/dim]")

    # Model
    model = await questionary.text(
        "Default model (optional, press Enter to skip):",
    ).ask_async()

    # Temperature
    temperature_str = await questionary.text(
        "Temperature (0.0-2.0, default 0.7):",
        default="0.7",
        validate=lambda x: (
            0 <= float(x) <= 2.0 if x else True
        ) or "Must be between 0.0 and 2.0"
    ).ask_async()

    temperature = float(temperature_str) if temperature_str else 0.7

    # Max tokens
    max_tokens_str = await questionary.text(
        "Max tokens (optional, press Enter to skip):",
    ).ask_async()

    max_tokens = int(max_tokens_str) if max_tokens_str else None

    # Create provider
    provider = AIProvider(
        name=name,
        api_key=api_key,
        endpoint=endpoint,
        model=model or None,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Confirmation
    console.print("\n[bold]Configuration Summary:[/bold]")
    console.print(f"  Name: {provider.name}")
    console.print(f"  Endpoint: {provider.endpoint}")
    console.print(f"  Model: {provider.model or 'Not set'}")
    console.print(f"  Temperature: {provider.temperature}")
    console.print(f"  Max Tokens: {provider.max_tokens or 'Not set'}")

    confirm = await questionary.confirm(
        "Save this configuration?",
        default=True
    ).ask_async()

    if not confirm:
        console.print("[yellow]Configuration cancelled[/yellow]")
        raise KeyboardInterrupt()

    return provider
```

**Acceptance Criteria:**
- Wizard guides through all steps
- Validation on each input
- Confirmation before saving
- User-friendly prompts

---

Due to length constraints, I'll continue with the remaining phases in the next part. Would you like me to continue with the rest of the Python implementation plan?