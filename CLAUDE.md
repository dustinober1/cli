# CLAUDE.md - Vibe Coder Repository Guide

This file provides guidance for Claude Code instances operating on the Vibe Coder repository. Read this first for context about the project, architecture, and development workflow.

---

## 🎯 Project Overview

**Vibe Coder** is a Python CLI coding assistant that works with any AI provider (OpenAI, Anthropic, Ollama, custom endpoints). It provides a beautiful terminal interface for code generation, review, testing, and more.

- **Repository:** https://github.com/dustinober1/cli
- **Language:** Python 3.9+
- **Build Tool:** Poetry
- **Status:** Phase 3 Complete (API Integration) ✅, Phase 4 Pending (Interactive Prompts)

---

## 📋 Quick Reference

### Essential Development Commands

```bash
# Install dependencies
make install

# Run all tests
make test

# Run tests with coverage report (generates HTML)
make test-cov

# Run a specific test file
poetry run pytest tests/test_config/test_validator.py -v
poetry run pytest tests/test_api/test_factory.py -v

# Run a specific test
poetry run pytest tests/test_config/test_validator.py::TestValidateApiKey::test_valid_api_key -v
poetry run pytest tests/test_api/test_factory.py::TestClientFactory::test_create_openai_client_by_name -v

# Format code (black + isort)
make format

# Lint code (flake8 + mypy)
make lint

# Clean build artifacts
make clean

# Run the CLI
make run
```

### Current Project Status

**Phase Completion:**
- ✅ **Phase 1:** Project Setup (Complete)
- ✅ **Phase 2:** Configuration System (Complete)
- ✅ **Phase 3:** API Integration (Complete)
- 🔄 **Phase 4:** Interactive Prompts (Next)

**Latest Achievements (December 2024):**
- Complete API integration layer with multi-provider support
- OpenAI, Anthropic, and Generic (OpenAI-compatible) client implementations
- Automatic provider detection and connection validation
- Streaming response support for real-time chat
- 186 tests passing with 57% overall coverage
- All code formatted, linted, and type-checked

**Ready for Phase 4:** Interactive setup wizard and chat interface development.

### When Modifying Code

1. **Make changes** to the relevant files
2. **Run `make format`** to format with black/isort
3. **Run `make lint`** to check for issues
4. **Run `make test`** to verify tests pass
5. **Run `make test-cov`** if coverage concerns
6. **Commit with `git add . && git commit -m "..."`**
7. **Push with `git push`**

### Common Test Patterns

```bash
# Run only config-related tests
poetry run pytest tests/test_config/ -v

# Run tests matching a pattern
poetry run pytest -k "test_valid" -v

# Run tests with detailed output
poetry run pytest tests/test_config/test_validator.py -vv

# Stop on first failure
poetry run pytest -x

# Run with print statements visible
poetry run pytest -s
```

---

## 🏗️ Architecture

### Four-Layer Architecture (Current State)

```
┌─────────────────────────────────────────┐
│           CLI Interface                 │
│         (Typer + Rich)                  │
│  - Basic commands defined              │
│  - Rich terminal output                │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Command Layer                   │
│    (setup, chat, config, test)          │
│  - Ready for Phase 4 implementation    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         API Client Layer                │
│  (OpenAI, Anthropic, Generic)           │
│  - ClientFactory for auto-detection     │
│  - Streaming support                    │
│  - Error handling                      │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       Configuration Layer               │
│   (ConfigManager + Validation)          │
│  - Multi-provider support              │
│  - Environment variables               │
│  - Persistent storage                  │
└─────────────────────────────────────────┘
```

### Key Files and Their Purposes

#### Type Definitions (vibe_coder/types/)

- **config.py** (315 lines)
  - `AIProvider`: Dataclass defining a single AI provider configuration
    - Fields: name, api_key, endpoint, model, temperature, max_tokens, headers
    - Validation: temperature 0.0-2.0, max_tokens > 0
    - Methods: to_dict(), from_dict() for serialization
  - `AppConfig`: Root configuration container with provider management
    - Methods: get_provider(), set_provider(), list_providers(), delete_provider(), has_provider()
  - Enums: `InteractionMode` (code, architect, ask, audit), `ProviderType` (openai, anthropic, ollama, etc.)

- **api.py** (173 lines)
  - `MessageRole`: Enum (SYSTEM, USER, ASSISTANT)
  - `ApiMessage`: role + content pair
  - `TokenUsage`: prompt_tokens, completion_tokens, total_tokens
  - `ApiRequest`: Request with messages, optional model/temperature/max_tokens
  - `ApiResponse`: Response with content, usage, finish_reason

#### Configuration Management (vibe_coder/config/)

- **manager.py** (280 lines)
  - `ConfigManager` class: Handles persistence to ~/.vibe/config.json
  - Public API: get_provider(), set_provider(), list_providers(), delete_provider(), get_current_provider(), set_current_provider(), reset_config()
  - Auto-persistence: Config saves to disk after each modification
  - Graceful error handling: Corrupted files return default config
  - Singleton: Exported as `config_manager` for module-level import

- **env_handler.py** (217 lines)
  - `load_env_config()`: Loads VIBE_CODER_* environment variables
  - `get_env_provider()`: Creates AIProvider from environment config with validation
  - `save_to_env()`: Saves configuration to .env file
  - `has_env_config()`: Boolean check for env config availability
  - Supported vars: VIBE_CODER_API_KEY, VIBE_CODER_ENDPOINT, VIBE_CODER_MODEL, VIBE_CODER_TEMPERATURE, VIBE_CODER_MAX_TOKENS, VIBE_CODER_PROVIDER_NAME

- **validator.py** (290 lines)
  - `validate_api_key()`: String, 10+ chars, no spaces
  - `validate_endpoint()`: Valid URL with http/https scheme
  - `validate_temperature()`: Float in range 0.0-2.0
  - `validate_max_tokens()`: Positive integer
  - `validate_provider()`: Returns list of error messages for AIProvider
  - `validate_provider_config()`: Validates raw config values
  - Helper functions: `is_localhost()`, `is_valid_url()`

#### API Client Layer (vibe_coder/api/)

- **base.py** (206 lines)
  - `BaseApiClient`: Abstract base class for all AI provider clients
  - Defines common interface: send_request(), stream_request(), validate_connection()
  - HTTP client setup with proper headers and timeout handling
  - Error formatting and validation utilities
  - Async context manager support for proper resource cleanup

- **factory.py** (221 lines)
  - `ClientFactory`: Automatic provider detection and client creation
  - Detects providers by name pattern matching and endpoint URL analysis
  - Support for OpenAI, Anthropic, and generic OpenAI-compatible endpoints
  - Configuration validation and helpful error messages
  - Provider registration system for extensibility

- **openai_client.py** (244 lines)
  - `OpenAIClient`: Complete OpenAI SDK integration
  - Streaming and non-streaming response support
  - Proper system message handling and temperature control
  - OpenAI-specific error handling and rate limit detection
  - Token usage tracking and response formatting

- **anthropic_client.py** (264 lines)
  - `AnthropicClient`: Complete Claude SDK integration
  - Proper system prompt separation per Anthropic API requirements
  - Streaming support with text_stream integration
  - Claude-specific error handling and retry logic
  - Message format conversion and stop reason mapping

- **generic_client.py** (367 lines)
  - `GenericClient`: Universal client for OpenAI-compatible endpoints
  - Works with Ollama, LM Studio, vLLM, LocalAI, and custom endpoints
  - Automatic endpoint path detection (/v1, /api, etc.)
  - Server-sent events parsing for streaming
  - Model endpoint discovery and caching

#### CLI Entry Point (vibe_coder/cli.py)

- 110 lines with Typer framework
- Commands: chat, setup, config (list/show/add/edit/delete), test
- Uses Rich for colored terminal output
- Dispatches to future command implementations

### Data Flow Example

```
User: vibe-coder chat --provider my-openai
  ↓
cli.py receives command
  ↓
ConfigManager.get_provider("my-openai") → AIProvider
  ↓
validator.validate_provider() → confirms valid
  ↓
[Phase 3] API client created with provider details
  ↓
Chat interface connects to AI
```

---

## 🧪 Test Suite

Total: 186 tests passing, 57% overall coverage

### Test Organization (tests/test_config/)

1. **test_types.py** (338 lines, 29 tests, 100% coverage)
   - TestAIProvider: Creation, validation, boundaries
   - TestAppConfig: CRUD operations, serialization, persistence
   - TestEnums: Value verification

2. **test_api_types.py** (320 lines, 32 tests, 100% coverage)
   - API message and request/response types
   - Real workflow scenarios with conversation history

3. **test_manager.py** (438 lines, 30 tests, 98% coverage)
   - ConfigManager initialization and directory creation
   - Provider CRUD operations and persistence
   - Cross-instance data persistence verification
   - Edge cases and error handling

4. **test_env_handler.py** (380 lines, 29 tests, 100% coverage)
   - Loading/saving environment configuration
   - Provider creation from env vars
   - .env file handling
   - Validation and error cases

5. **test_validator.py** (480 lines, 53 tests, 91% coverage)
   - Individual validator functions
   - Boundary testing (temperature 0.0-2.0, max_tokens > 0)
   - URL parsing edge cases
   - Real provider configurations (OpenAI, Anthropic, Ollama)

### Test Organization (tests/test_api/)

5. **test_factory.py** (247 lines, 13 tests, 81% coverage)
   - ClientFactory provider detection and creation
   - OpenAI, Anthropic, and Generic client instantiation
   - Provider configuration validation
   - Endpoint and name pattern matching
   - Error handling for invalid configurations

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific file
poetry run pytest tests/test_config/test_manager.py -v
poetry run pytest tests/test_api/test_factory.py -v

# Single test
poetry run pytest tests/test_config/test_manager.py::TestConfigManagerInitialization::test_creates_config_directory -v
poetry run pytest tests/test_api/test_factory.py::TestClientFactory::test_create_openai_client_by_name -v

# Tests matching pattern
poetry run pytest -k "provider" -v
```

---

## 📁 Project Structure

```
vibe-coder/
├── vibe_coder/
│   ├── __init__.py
│   ├── cli.py                 # Main Typer CLI entry point
│   ├── types/
│   │   ├── config.py          # AIProvider, AppConfig, Enums
│   │   └── api.py             # API message types
│   ├── config/
│   │   ├── manager.py         # ConfigManager for persistence
│   │   ├── env_handler.py     # Environment variable support
│   │   └── validator.py       # Validation utilities
│   ├── api/                   # API client implementations
│   │   ├── __init__.py
│   │   ├── base.py            # BaseApiClient abstract class
│   │   ├── factory.py         # ClientFactory for auto-detection
│   │   ├── openai_client.py   # OpenAI SDK integration
│   │   ├── anthropic_client.py # Anthropic SDK integration
│   │   └── generic_client.py  # OpenAI-compatible endpoint client
│   ├── commands/              # [Phase 4+] Command implementations
│   ├── prompts/               # [Phase 4+] Prompt templates
│   └── utils/                 # [Phase 6] Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_config/           # Configuration tests
│   │   ├── test_types.py
│   │   ├── test_api_types.py
│   │   ├── test_manager.py
│   │   ├── test_env_handler.py
│   │   └── test_validator.py
│   └── test_api/              # API client tests
│       └── test_factory.py
├── pyproject.toml             # Poetry project config
├── Makefile                   # Development commands
├── README.md                  # Project documentation
├── CLAUDE.md                  # This file
├── plans/                     # Planning documentation
│   ├── PHASE_1_PLAN.md        # Project setup details
│   ├── PHASE_2_PLAN.md        # Configuration system design
│   ├── PHASE_3_PLAN.md        # API integration architecture
│   ├── PHASE_4_PLAN.md        # Interactive prompts plan
│   ├── PROGRESS_OVERVIEW.md   # Current project status
│   └── ROADMAP_PYTHON.md      # Full 20-week roadmap
└── poetry.lock                # Locked dependencies
```

---

## 🔧 Important Design Patterns

### 1. Configuration Dataclasses

AIProvider and AppConfig use Python dataclasses for type-safe configuration:

```python
@dataclass
class AIProvider:
    name: str
    api_key: str
    endpoint: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"Temperature must be 0.0-2.0, got {self.temperature}")
```

**Pattern:** Validation in `__post_init__()` + separate validator functions for pre-creation validation

### 2. Persistent Configuration Storage

ConfigManager handles reading/writing to ~/.vibe/config.json:

```python
# Single instance usage (singleton pattern)
from vibe_coder.config.manager import config_manager

provider = config_manager.get_provider("openai")
config_manager.set_provider("openai", new_provider)
```

**Pattern:** JSON persistence with auto-save on modifications, graceful error handling for corrupted files

### 3. Environment Variable Configuration

Two-mode support: file-based AND environment-based:

```bash
# Mode 1: .env file
VIBE_CODER_API_KEY=sk-...
VIBE_CODER_ENDPOINT=https://api.openai.com/v1

# Mode 2: Direct environment variables (CI/CD, Docker)
export VIBE_CODER_API_KEY=sk-...
export VIBE_CODER_ENDPOINT=https://api.openai.com/v1
```

**Pattern:** Flexible configuration supporting development, CI/CD, and containerized environments

### 4. Validation Layer

Separate validation functions return error lists (not booleans):

```python
# Returns list of error messages (empty = valid)
errors = validate_provider(provider)
if errors:
    for error in errors:
        print(f"Error: {error}")
```

**Pattern:** User-friendly error reporting without raising exceptions during setup

### 4. Abstract API Client Pattern

All AI providers implement the same abstract interface for consistency:

```python
from vibe_coder.api.factory import ClientFactory

# Factory automatically detects provider type
client = ClientFactory.create_client(provider)

# Unified interface regardless of provider
response = await client.send_request(messages)
async for chunk in client.stream_request(messages):
    print(chunk, end='')
```

**Pattern:** Consistent interface with provider-specific optimizations

### 5. Async Resource Management Pattern

Proper cleanup of HTTP clients and resources:

```python
async with client as api_client:
    response = await api_client.send_request(messages)
    # Client automatically cleaned up
```

**Pattern:** Context managers for resource safety

---

## 🚀 Current Implementation Status

### Phase 1: Project Setup ✅ COMPLETE (December 2024)
- Poetry project initialized with all dependencies
- Complete directory structure created
- CLI entry point working with Typer
- Development tools configured (black, pytest, mypy, flake8)
- Makefile with common development commands
- All code formatted, linted, type-checked
- Committed to GitHub

### Phase 2: Configuration System ✅ COMPLETE (December 2024)
- Type system with dataclasses (AIProvider, AppConfig, API types)
- ConfigManager with CRUD operations and persistence
- Environment variable support with .env file integration
- Comprehensive validation with meaningful error messages
- 173 tests passing, 91% coverage
- Supports multiple AI providers (OpenAI, Anthropic, Ollama, custom)
- All code formatted, linted, type-checked
- Committed to GitHub

### Phase 3: API Integration ✅ COMPLETE (December 2024)
- Complete API integration layer with multi-provider support
- OpenAI client using official SDK with streaming
- Anthropic client using official SDK with proper system prompts
- Generic client for any OpenAI-compatible endpoint
- ClientFactory for automatic provider detection
- Streaming and non-streaming response support
- Robust error handling and connection validation
- 13 new tests (186 total tests passing)
- All code formatted, linted, type-checked
- Committed to GitHub

### Phase 4: Interactive Prompts 🔄 READY TO START
Will implement:
- Setup wizard with Questionary for provider configuration
- Basic chat interface with Rich terminal formatting
- Interactive configuration management commands
- Connection testing and validation utilities

### Phase 5: Slash Commands ⏳ PENDING
Will implement:
- 40+ slash commands (/code, /fix, /test, /review, etc.)
- Enhanced chat features with history management
- Git integration

### Phase 6: Utilities & Polish ⏳ PENDING
Will implement:
- AST-based repository mapping
- Auto-healing and code application
- Cost tracking and token counting

---

## 🔍 Key Technical Details

### Python Version Compatibility

- **Target:** Python 3.9+
- **Testing:** Verified with type hints and mypy
- **Key note:** Uses `Optional[T]` instead of `T | None` for Python 3.9 compatibility

### Dependencies

| Purpose | Package | Version |
|---------|---------|---------|
| CLI Framework | typer | ^0.12.0 |
| Terminal Output | rich | ^13.0.0 |
| Interactive Prompts | questionary | ^2.0.0 |
| HTTP Client | httpx | ^0.27.0 |
| Config Files | python-dotenv | ^1.0.0 |
| Config Management | dynaconf | ^3.2.0 |
| Testing | pytest | ^8.0.0 |
| Code Formatting | black | ^24.0.0 |
| Import Sorting | isort | ^5.13.0 |
| Linting | flake8 | ^7.0.0 |
| Type Checking | mypy | ^1.8.0 |

### Code Quality Standards

- **Line Length:** 100 characters (black)
- **Formatting:** black + isort
- **Linting:** flake8 (0 issues)
- **Type Checking:** mypy (0 errors)
- **Test Coverage:** 91% overall, >98% per module

---

## 🐛 Known Issues & Fixes

### Issue 1: Python 3.9 Compatibility (FIXED)
**Problem:** Using `X | Y` union syntax (Python 3.10+)
**Fix:** Changed to `Optional[X]` with `from typing import Optional`
**Files:** env_handler.py

### Issue 2: IPv6 Localhost Detection (FIXED)
**Problem:** is_localhost("http://[::1]:8000") failing
**Fix:** Updated string parsing to handle IPv6 bracket notation
**Files:** validator.py, test_validator.py

### Issue 3: Corrupted Config File Handling (FIXED)
**Problem:** JSONDecodeError crashes app when config.json corrupted
**Fix:** Wrapped in try/except, returns default config
**Files:** manager.py

---

## 💡 Development Tips

### Adding New Tests

Follow existing patterns in test files:

```python
class TestNewFeature:
    """Test description."""

    def test_valid_case(self):
        """What should happen."""
        result = function(valid_input)
        assert result == expected_value

    def test_invalid_case(self):
        """What should happen with bad input."""
        with pytest.raises(ValueError, match="error pattern"):
            function(invalid_input)
```

### Adding New Configuration Fields

1. Update `AIProvider` dataclass in types/config.py
2. Add validation in `__post_init__()` if needed
3. Add validator function in validator.py
4. Update serialization in to_dict()/from_dict()
5. Add tests to test_types.py
6. Update env_handler.py if environment variable support needed

### Running Tests During Development

```bash
# Watch mode with pytest-watch (not installed, use loop)
while true; do make test; sleep 2; done

# Stop on first failure
poetry run pytest -x

# Show print statements
poetry run pytest -s

# Detailed failure info
poetry run pytest -vv
```

---

## 📚 Documentation Files

- **README.md** - User-facing project overview and features
- **PHASE_2_PLAN.md** - Detailed Phase 2 implementation guide
- **CLAUDE.md** - This file, for Claude Code instances
- **pyproject.toml** - Project metadata and dependencies
- **Makefile** - Development command shortcuts

---

## 🎓 Key Concepts for Junior Developers

### Dataclasses

Python dataclasses are like TypeScript interfaces + constructors:

```python
# Simple type definition
@dataclass
class AIProvider:
    name: str
    api_key: str
    endpoint: str
```

This automatically creates `__init__`, `__repr__`, `__eq__` methods.

### Type Hints

All functions have type hints for better IDE support and mypy checking:

```python
def validate_api_key(api_key: str) -> bool:
    """Returns True if valid, False otherwise."""
```

### Serialization Pattern

Objects converted to/from dicts for JSON storage:

```python
provider = AIProvider(name="openai", api_key="sk-...", endpoint="https://...")
data = provider.to_dict()  # → dict
provider2 = AIProvider.from_dict(data)  # → AIProvider
```

### Error Lists vs Exceptions

Validators return lists of error messages (no exceptions):

```python
# Good for setup/configuration validation
errors = validate_provider(provider)
if errors:
    for error in errors:
        console.print(f"[red]{error}[/red]")
```

---

## 🔗 Related Resources

- **GitHub Issues:** https://github.com/dustinober1/cli/issues
- **Python Docs:** https://docs.python.org/3.9/
- **Poetry Docs:** https://python-poetry.org/docs/
- **Typer Docs:** https://typer.tiangolo.com/
- **Rich Docs:** https://rich.readthedocs.io/
- **Pytest Docs:** https://docs.pytest.org/

---

## ❓ Quick FAQ

**Q: How do I run a single test?**
A: `poetry run pytest tests/test_config/test_file.py::TestClass::test_method -v`

**Q: Where is configuration stored?**
A: `~/.vibe/config.json` (created automatically)

**Q: How do I add a new provider?**
A: Use `config_manager.set_provider("name", AIProvider(...))`

**Q: Can I use environment variables?**
A: Yes! Set `VIBE_CODER_API_KEY`, `VIBE_CODER_ENDPOINT`, etc.

**Q: How much coverage is required?**
A: Aim for 90%+. Check with `make test-cov`

**Q: What Python version?**
A: 3.9+ (use `Optional[T]` not `T | None`)

---

## 📝 Notes for Future Work

1. **Phase 3 Preparation:** API integration layer is next. Consider:
   - How to handle different API response formats
   - Streaming vs non-streaming responses
   - Timeout and retry logic

2. **Configuration Migration:** As features add config fields:
   - Keep version number in config.json
   - Plan for config file migrations
   - Maintain backwards compatibility

3. **Performance:** Current implementation prioritizes clarity:
   - ConfigManager reads from disk on each operation
   - Consider caching for frequently accessed providers
   - Profile before optimizing

4. **Error Messages:** Currently using generic validation messages:
   - Consider more context-specific messages
   - Use Rich for colored, formatted output
   - Plan for i18n/translations

---

**Last Updated:** Phase 3 Complete, December 2024
**Next Phase:** Phase 4 - Interactive Prompts
**Maintainer:** Dustin Ober (dustin@example.com)

## 📊 Current Project Statistics

### Code Metrics:
- **Total Lines of Code:** ~6,000 lines (production + tests)
- **Production Code:** ~3,500 lines across 13 main files
- **Test Code:** ~2,500 lines across 6 test files
- **Test Coverage:** 57% overall (Phase 2: 91%, Phase 3: factory 81%)
- **All Tests:** 186 tests passing

### Completed Features:
- ✅ Multi-provider support (OpenAI, Anthropic, OpenAI-compatible)
- ✅ Streaming responses for real-time interaction
- ✅ Automatic provider detection by name and endpoint
- ✅ Robust configuration management with persistence
- ✅ Environment variable support for CI/CD and Docker
- ✅ Comprehensive validation with meaningful error messages
- ✅ Async HTTP clients with proper resource management
- ✅ Type-safe implementation with full mypy compliance

### Development Infrastructure:
- ✅ Poetry dependency management
- ✅ Automated code formatting (black + isort)
- ✅ Comprehensive linting (flake8 + mypy)
- ✅ Test coverage reporting
- ✅ Makefile for common development tasks
- ✅ Git workflow with proper commit standards

### Architecture Quality:
- ✅ Clean separation of concerns (4-layer architecture)
- ✅ Abstract interfaces for extensibility
- ✅ Factory pattern for provider creation
- ✅ Repository pattern for configuration
- ✅ Error handling throughout the stack
- ✅ Resource management with context managers

The project has a solid, production-ready foundation that supports the full roadmap through v1.0.0 and beyond.
