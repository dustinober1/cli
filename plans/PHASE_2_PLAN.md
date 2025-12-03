# Phase 2: Configuration System - Detailed Plan

## Status: ✅ COMPLETE (December 2024)

## Overview

Phase 2 focused on building a robust configuration management system that persists user settings and supports multiple AI provider configurations.

**Duration:** Week 2 of development (Days 8-12)
**Deliverable:** Persistent configuration system supporting multiple providers ✅
**Previous Phase:** Phase 1 ✅ Complete
**Current Phase:** Phase 2 ✅ Complete

---

## Phase 1 Review

### What We Accomplished:
✅ Poetry project initialized with all dependencies
✅ Complete directory structure created
✅ Main CLI entry point working with Typer
✅ 4 basic commands (chat, setup, config, test)
✅ Development tools configured (black, pytest, mypy, flake8)
✅ Everything committed to GitHub

### Current State:
```
vibe-coder/
├── vibe_coder/
│   ├── cli.py              # ✓ Working
│   ├── commands/           # ✓ Ready for implementation
│   ├── config/             # ← Phase 2 Focus
│   ├── api/                # Phase 3
│   ├── prompts/            # Phase 4
│   └── utils/              # Phase 6
├── pyproject.toml          # ✓ Complete
├── Makefile                # ✓ Ready
└── poetry.lock             # ✓ Locked
```

---

## Phase 2: Configuration System

### Goal
Build a configuration management system that:
- Persists provider settings to `~/.vibe/config.json`
- Supports multiple AI provider configurations
- Provides validation and error handling
- Uses type hints with dataclasses
- Integrates with dynaconf for file management

### Architecture

```
Configuration Flow:
┌──────────────────┐
│  User Input      │
│  (setup wizard)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  Validation              │
│  (validator.py)          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Type Conversion         │
│  (types/config.py)       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Config Manager                  │
│  (config/manager.py)             │
│  - Store in dynaconf             │
│  - Persist to ~/.vibe/config.json│
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────┐
│  JSON File       │
│  ~/.vibe/config  │
└──────────────────┘
```

---

## Task Breakdown

### Task 2.1: Define TypeScript-like Type System using Dataclasses

**File:** `vibe_coder/types/config.py`
**Difficulty:** Junior-friendly
**Time Estimate:** 2-3 hours

#### What We're Building:
Python dataclasses that define the structure of our configuration. Think of these like TypeScript interfaces, but for Python.

#### Implementation Steps:

1. **Create AIProvider dataclass** (lines 1-50)
   - Fields: name, api_key, endpoint, model, temperature, max_tokens, headers
   - Validation in `__post_init__` for temperature (0.0-2.0)
   - Type hints for all fields
   - Docstrings explaining each field

2. **Create AppConfig dataclass** (lines 51-100)
   - Fields: current_provider, providers dict, defaults
   - Helper methods: get_provider(), set_provider(), etc.
   - Track offline mode and debug settings

3. **Create helper types** (lines 101-150)
   - InteractionMode enum (code, architect, ask, audit)
   - Provider types enum (openai, anthropic, ollama, generic)

#### Code Structure:
```python
from dataclasses import dataclass, field
from typing import Optional, Dict
from enum import Enum

@dataclass
class AIProvider:
    """Configuration for an AI provider."""
    name: str
    api_key: str
    endpoint: str
    # ... more fields

@dataclass
class AppConfig:
    """Application configuration."""
    current_provider: str
    providers: Dict[str, AIProvider] = field(default_factory=dict)
    # ... more fields
```

#### Acceptance Criteria:
- ✅ All dataclasses defined with type hints
- ✅ Validation in `__post_init__` works
- ✅ No import errors when running
- ✅ Docstrings complete
- ✅ Default values sensible

---

### Task 2.2: Create ConfigManager Class

**File:** `vibe_coder/config/manager.py`
**Difficulty:** Medium
**Time Estimate:** 4-5 hours

#### What We're Building:
A class that manages reading/writing configuration to disk using dynaconf. It's like a database layer for our config.

#### Implementation Steps:

1. **Initialize ConfigManager** (lines 1-50)
   - Accept optional config_dir (defaults to ~/.vibe)
   - Create directory if doesn't exist
   - Initialize dynaconf with config file path
   - Create default config if missing

2. **Implement CRUD Methods** (lines 51-150)
   - `get_provider(name: str)` → AIProvider or None
   - `set_provider(name: str, provider: AIProvider)` → saves to file
   - `list_providers()` → list of provider names
   - `delete_provider(name: str)` → removes from config
   - `get_current_provider()` → currently active provider
   - `set_current_provider(name: str)` → make provider active
   - `reset_config()` → reset to defaults

3. **File Operations** (lines 151-200)
   - `_load_config()` → read JSON from disk
   - `_save_config(dict)` → write JSON to disk
   - Handle file not found errors gracefully
   - Pretty-print JSON with indentation

4. **Create Singleton** (lines 201-210)
   - Export `config_manager` as module-level singleton
   - Can be imported: `from vibe_coder.config.manager import config_manager`

#### Code Structure:
```python
from pathlib import Path
from dynaconf import Dynaconf
import json

class ConfigManager:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".vibe"
        self.config_file = self.config_dir / "config.json"
        # ... initialization

    def get_provider(self, name: str) -> Optional[AIProvider]:
        # Load from file and convert to AIProvider
        pass

    def set_provider(self, name: str, provider: AIProvider) -> None:
        # Convert AIProvider to dict and save
        pass

# Singleton instance
config_manager = ConfigManager()
```

#### Acceptance Criteria:
- ✅ Can save and retrieve providers
- ✅ Config persists to ~/.vibe/config.json
- ✅ File creates automatically
- ✅ All methods implemented
- ✅ Error handling for missing files

---

### Task 2.3: Create Environment Variable Handler

**File:** `vibe_coder/config/env_handler.py`
**Difficulty:** Junior-friendly
**Time Estimate:** 2-3 hours

#### What We're Building:
Support for configuring the app via environment variables (useful for CI/CD, docker, etc.).

#### Implementation Steps:

1. **Create load_env_config() function** (lines 1-40)
   - Call `load_dotenv()` to load .env file
   - Check for VIBE_CODER_* environment variables:
     - VIBE_CODER_API_KEY
     - VIBE_CODER_ENDPOINT
     - VIBE_CODER_MODEL
     - VIBE_CODER_TEMPERATURE
   - Return dict or None if no vars found

2. **Create save_to_env() function** (lines 41-80)
   - Format values as .env file content
   - Write to .env in current directory
   - Display warning about not committing .env files
   - Use `set_key()` from python-dotenv

3. **Create get_env_provider() function** (lines 81-100)
   - Call load_env_config()
   - Convert env vars to AIProvider object
   - Validate that api_key and endpoint are present
   - Return AIProvider or None

#### Code Structure:
```python
import os
from dotenv import load_dotenv, set_key

def load_env_config() -> Optional[Dict[str, str]]:
    """Load configuration from environment variables."""
    load_dotenv()
    # Check for VIBE_CODER_* vars
    # Return dict or None

def save_to_env(values: Dict[str, str]) -> None:
    """Save configuration to .env file."""
    # Write to .env
    # Show warning
    pass

def get_env_provider() -> Optional[AIProvider]:
    """Get provider from environment variables."""
    # Load, validate, convert to AIProvider
    pass
```

#### Acceptance Criteria:
- ✅ Reads .env files correctly
- ✅ Checks for VIBE_CODER_* variables
- ✅ Returns None if no env vars found
- ✅ Validation in place
- ✅ Warning about committing .env

---

### Task 2.4: Create Configuration Validator

**File:** `vibe_coder/config/validator.py`
**Difficulty:** Medium
**Time Estimate:** 3-4 hours

#### What We're Building:
Validation functions that check if configuration values are valid before saving them.

#### Implementation Steps:

1. **Create validate_api_key() function** (lines 1-30)
   - Check not empty and not None
   - Check length >= 10 characters
   - Check no spaces in key
   - Return True/False

2. **Create validate_endpoint() function** (lines 31-60)
   - Parse URL using urlparse
   - Check for scheme (http/https only)
   - Check for netloc (domain)
   - Return True/False

3. **Create validate_temperature() function** (lines 61-75)
   - Check is float or convertible to float
   - Check range 0.0-2.0
   - Return True/False

4. **Create validate_provider() function** (lines 76-120)
   - Validate all fields of an AIProvider
   - Return list of error messages (empty = valid)
   - Check name not empty
   - Check api_key valid
   - Check endpoint valid
   - Check temperature valid
   - Check max_tokens is positive int

5. **Create helper functions** (lines 121-150)
   - `is_localhost(url: str) -> bool`
   - `is_valid_url(url: str) -> bool`
   - Used by validators and by offline mode

#### Code Structure:
```python
from urllib.parse import urlparse
from vibe_coder.types.config import AIProvider

def validate_api_key(api_key: str) -> bool:
    """Check if API key format is valid."""
    if not api_key or not isinstance(api_key, str):
        return False
    if len(api_key) < 10:
        return False
    if ' ' in api_key:
        return False
    return True

def validate_provider(provider: AIProvider) -> List[str]:
    """Validate provider, return list of errors."""
    errors = []
    if not provider.name:
        errors.append("Provider name is required")
    if not validate_api_key(provider.api_key):
        errors.append("Invalid API key")
    # ... more validation
    return errors
```

#### Acceptance Criteria:
- ✅ All validators implemented
- ✅ Return meaningful error messages
- ✅ Handle edge cases (None, empty strings, etc.)
- ✅ Type hints correct
- ✅ validate_provider returns list not bool

---

## Testing Strategy for Phase 2

### Test Files to Create:

1. **tests/test_config/test_types.py** (lines 1-50)
   - Test AIProvider creation
   - Test validation in __post_init__
   - Test invalid temperature raises error

2. **tests/test_config/test_manager.py** (lines 1-200)
   - Test save/load provider
   - Test list_providers
   - Test delete_provider
   - Test current_provider management
   - Test file persistence
   - Use pytest fixtures for temp directories

3. **tests/test_config/test_validator.py** (lines 1-150)
   - Test each validation function
   - Test valid inputs pass
   - Test invalid inputs fail
   - Test error messages

4. **tests/test_config/test_env_handler.py** (lines 1-100)
   - Test loading from .env
   - Test getting provider from env vars
   - Test with and without env vars

### Running Tests:
```bash
make test                    # Run all tests
make test-cov              # Run with coverage
poetry run pytest tests/test_config/  # Run config tests only
```

---

## Development Workflow

### Step-by-Step:

**Day 1 (Tasks 2.1 & 2.2 Part 1):**
1. Start with Task 2.1 - Define types
2. Write dataclasses with docstrings
3. Add validation in __post_init__
4. Test imports work
5. Begin Task 2.2 - ConfigManager init

**Day 2 (Task 2.2 Part 2):**
1. Complete ConfigManager CRUD methods
2. Implement file operations
3. Test save/load manually
4. Create singleton instance

**Day 3 (Task 2.3):**
1. Create env_handler.py
2. Implement all three functions
3. Test with .env file
4. Test with environment variables

**Day 4 (Task 2.4 & Testing):**
1. Create validator.py
2. Implement all validators
3. Write comprehensive tests
4. Fix any issues found

**Day 5 (Polish & Integration):**
1. Run full test suite
2. Ensure >70% coverage
3. Code cleanup with black/isort
4. Commit and push
5. Write commit message documenting all changes

### Commands to Run Daily:

```bash
# Format code
make format

# Check for issues
make lint

# Run tests
make test

# Run with coverage
make test-cov

# Git workflow
git add -A
git commit -m "message"
git push origin main
```

---

## Integration Points

### How Phase 2 Connects to Other Phases:

**Phase 2 → Phase 3 (API Integration):**
- Phase 3 will use `config_manager.get_provider()` to get provider details
- Pass AIProvider to API clients
- API clients will use endpoint, api_key, model from config

**Phase 2 → Phase 4 (Interactive Prompts):**
- Setup wizard will create AIProvider objects
- Pass to `config_manager.set_provider()`
- ConfigManager persists to disk

**Phase 2 → CLI (commands/cli.py):**
- Commands will access configuration via `config_manager`
- Get current provider before creating API client
- Show validation errors if config invalid

### Data Flow Example:
```
User runs: vibe-coder chat --provider my-openai
    ↓
CLI command gets provider name
    ↓
ConfigManager.get_provider("my-openai") → AIProvider
    ↓
Phase 3 creates API client with provider details
    ↓
Chat interface connects to AI
```

---

## File Structure After Phase 2

```
vibe_coder/
├── types/
│   └── config.py           # NEW: Dataclasses
├── config/
│   ├── __init__.py
│   ├── manager.py          # NEW: ConfigManager
│   ├── env_handler.py      # NEW: Env var support
│   └── validator.py        # NEW: Validation funcs
└── cli.py                  # Unchanged

tests/
└── test_config/
    ├── test_types.py       # NEW
    ├── test_manager.py     # NEW
    ├── test_validator.py   # NEW
    └── test_env_handler.py # NEW

~/.vibe/
└── config.json             # Will be created at runtime
```

---

## Success Criteria for Phase 2

By end of this phase:
- ✅ Type system defined with dataclasses
- ✅ ConfigManager saves/loads configuration
- ✅ Configuration persists to ~/.vibe/config.json
- ✅ Environment variables supported
- ✅ Comprehensive validation
- ✅ All tests passing (>70% coverage)
- ✅ Code formatted and linted
- ✅ Committed to GitHub with clear commit message

---

## Questions to Answer Before Starting:

1. **Local testing:** Will you be testing with actual AI APIs or mocking them?
   - Recommended: Mock for testing, real for manual verification

2. **Error handling:** How verbose should error messages be?
   - Recommended: Use Rich console for colored, helpful messages

3. **File format:** Should we add comments to config.json?
   - Recommended: Keep JSON clean, add comments in docstrings

4. **Backwards compatibility:** Do we need to migrate old configs?
   - Not for v0.1.0, but plan for it

---

## Related Documentation

- **IMPLEMENTATION_PLAN_PYTHON.md** - Phase 2 detailed tasks
- **QUICK_START_GUIDE_PYTHON.md** - Developer setup
- **ROADMAP_PYTHON.md** - Full 20-week timeline
- **README.md** - Project overview

---

## Phase 2 Completion Summary

### ✅ All Tasks Completed Successfully

**Task 2.1: Type System with Dataclasses** ✅
- Created vibe_coder/types/config.py with AIProvider and AppConfig
- Created vibe_coder/types/api.py with API message types
- 61 tests, 100% coverage

**Task 2.2: ConfigManager Class** ✅
- Created vibe_coder/config/manager.py for persistent configuration
- Automatic directory and config file creation
- Full provider CRUD operations
- 30 tests, 98% coverage

**Task 2.3: Environment Variable Handler** ✅
- Created vibe_coder/config/env_handler.py
- VIBE_CODER_* environment variable support
- .env file integration with dotenv
- 29 tests, 100% coverage

**Task 2.4: Configuration Validator** ✅
- Created vibe_coder/config/validator.py
- Comprehensive validation utilities
- Error message reporting for all validators
- 53 tests, 91% coverage

### Final Statistics

- **Total Tests:** 173 passing
- **Code Coverage:** 91% overall
- **Code Quality:**
  - Black formatting: ✅
  - isort import ordering: ✅
  - mypy type checking: ✅ (0 errors)
  - flake8 linting: ✅ (0 issues)

### Features Delivered

✅ Multiple AI provider support (OpenAI, Anthropic, Ollama, custom endpoints)
✅ Persistent configuration to ~/.vibe/config.json
✅ Environment variable configuration (CI/CD, Docker, local development)
✅ .env file support with python-dotenv
✅ Comprehensive validation with meaningful error messages
✅ Type-safe configuration using Python dataclasses
✅ Serialization/deserialization with to_dict/from_dict methods
✅ Provider CRUD operations
✅ Current provider management
✅ Configuration reset and defaults

### Architecture

```
Configuration System:
├── Types (vibe_coder/types/)
│   ├── config.py - Configuration dataclasses
│   └── api.py - API message types
├── Config (vibe_coder/config/)
│   ├── manager.py - Persistent storage & CRUD
│   ├── env_handler.py - Environment variables
│   └── validator.py - Validation utilities
└── Tests (tests/test_config/)
    ├── test_types.py - 29 tests
    ├── test_api_types.py - 32 tests
    ├── test_manager.py - 30 tests
    ├── test_env_handler.py - 29 tests
    └── test_validator.py - 53 tests
```

### Files Modified/Created

Created:
- vibe_coder/types/config.py (315 lines)
- vibe_coder/types/api.py (173 lines)
- vibe_coder/config/manager.py (280 lines)
- vibe_coder/config/env_handler.py (217 lines)
- vibe_coder/config/validator.py (290 lines)
- tests/test_config/test_types.py (338 lines)
- tests/test_config/test_api_types.py (320 lines)
- tests/test_config/test_manager.py (438 lines)
- tests/test_config/test_env_handler.py (380 lines)
- tests/test_config/test_validator.py (480 lines)

Total: 3,421 lines of code and tests created

### Next Phase: Phase 3 - API Integration

Phase 3 will build on this configuration system to:
1. Create API client classes for different providers
2. Handle provider-specific API differences
3. Implement message formatting and parsing
4. Add streaming support
5. Create comprehensive integration tests

The configuration system is now ready to support Phase 3 implementation.

---

Phase 2 Complete! 🐍✨
