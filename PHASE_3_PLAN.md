# Phase 3: API Integration - Detailed Plan

## Status: ⏳ IN PROGRESS

## Overview

Phase 3 focuses on building the API integration layer that allows Vibe Coder to communicate with different AI providers. This phase creates the foundation for connecting to OpenAI, Anthropic, Ollama, and any OpenAI-compatible endpoint.

**Duration:** Week 3 of development (Days 15-19)
**Deliverable:** API clients that can connect to 3+ different AI providers ✅
**Previous Phase:** Phase 2 ✅ Complete
**Current Phase:** Phase 3 🔄 In Progress

---

## Phase 2 Review

### What We Accomplished:
✅ Type system with dataclasses (AIProvider, AppConfig, API types)
✅ ConfigManager with persistent storage
✅ Environment variable support with .env files
✅ Comprehensive validation utilities
✅ 173 tests passing, 91% coverage
✅ Configuration persists to ~/.vibe/config.json

### Current State:
```
vibe-coder/
├── vibe_coder/
│   ├── cli.py              # ✓ Working with basic commands
│   ├── types/
│   │   ├── config.py       # ✓ AIProvider, AppConfig defined
│   │   └── api.py          # ✓ API message types defined
│   ├── config/
│   │   ├── manager.py      # ✓ ConfigManager working
│   │   ├── env_handler.py  # ✓ Environment variables supported
│   │   └── validator.py    # ✓ Validation utilities
│   ├── api/                # ← Phase 3 Focus
│   ├── commands/           # Phase 4+
│   ├── prompts/            # Phase 4+
│   └── utils/              # Phase 6+
├── tests/
│   └── test_config/        # ✓ 173 tests passing
├── pyproject.toml          # ✓ Complete with dependencies
├── Makefile                # ✓ Development commands ready
└── poetry.lock             # ✓ Locked dependencies
```

---

## Phase 3: API Integration

### Goal
Build an API integration layer that:
- Provides a unified interface for different AI providers
- Supports both streaming and non-streaming responses
- Handles provider-specific differences (system prompts, error formats)
- Includes connection validation and error handling
- Works with any OpenAI-compatible endpoint

### Architecture

```
API Client Architecture:
┌─────────────────────────────────────────┐
│         CLI Commands Layer              │
│      (uses ClientFactory)               │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         ClientFactory                   │
│  - Detects provider type                │
│  - Creates appropriate client           │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      BaseApiClient (Abstract)           │
│  - Common interface for all clients     │
│  - Async methods: send_request, etc.    │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┬─────────────────┐
    ▼         ▼         ▼                 ▼
┌─────────┐ ┌─────────┐ ┌─────────┐   ┌─────────────┐
│OpenAI   │ │Anthropic│ │Generic  │   │   Custom    │
│Client   │ │Client   │ │Client   │   │  Clients    │
└─────────┘ └─────────┘ └─────────┘   └─────────────┘
```

---

## Task Breakdown

### Task 3.1: Create BaseApiClient Abstract Class

**File:** `vibe_coder/api/base.py`
**Difficulty:** Medium
**Time Estimate:** 3-4 hours

#### What We're Building:
An abstract base class that defines the common interface for all AI provider clients. This ensures consistency across different providers and makes it easy to add new providers.

#### Implementation Steps:

1. **Create BaseApiClient abstract class** (lines 1-50)
   - Import ABC, abstractmethod from abc
   - Define __init__ method accepting AIProvider configuration
   - Store provider config and initialize httpx client

2. **Define abstract methods** (lines 51-150)
   - `send_request(messages: List[ApiMessage], **kwargs) -> ApiResponse`
   - `stream_request(messages: List[ApiMessage], **kwargs) -> AsyncIterator[str]`
   - `validate_connection() -> bool`
   - `estimate_tokens(text: str) -> int`

3. **Add utility methods** (lines 151-200)
   - `_format_error_response(error: Exception) -> ApiResponse`
   - `_get_headers() -> Dict[str, str]`
   - `_handle_rate_limit() -> None`

#### Code Structure:
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Optional
import httpx
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, ApiResponse, TokenUsage

class BaseApiClient(ABC):
    """Abstract base class for AI provider clients."""

    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.client = httpx.AsyncClient(
            base_url=provider.endpoint,
            headers=self._get_headers(),
            timeout=60.0
        )

    @abstractmethod
    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ApiResponse:
        """Send a request to the AI provider."""
        pass

    @abstractmethod
    async def stream_request(
        self,
        messages: List[ApiMessage],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream a response from the AI provider."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the connection works."""
        pass
```

#### Acceptance Criteria:
- ✅ Abstract class defined with all required methods
- ✅ httpx client initialized with proper headers
- ✅ Type hints for all methods
- ✅ Docstrings explaining each method
- ✅ No instantiation possible (abstract)

---

### Task 3.2: Create OpenAI Client

**File:** `vibe_coder/api/openai_client.py`
**Difficulty:** Medium
**Time Estimate:** 4-5 hours

#### What We're Building:
A complete OpenAI API client using the official OpenAI SDK. This will handle OpenAI-specific message formatting, error responses, and streaming.

#### Implementation Steps:

1. **Create OpenAIClient class** (lines 1-50)
   - Import openai library
   - Inherit from BaseApiClient
   - Initialize OpenAI client with API key and base URL

2. **Implement send_request()** (lines 51-100)
   - Convert ApiMessage to OpenAI message format
   - Handle system messages correctly
   - Call OpenAI API with parameters
   - Convert response to ApiResponse format
   - Handle OpenAI-specific errors

3. **Implement stream_request()** (lines 101-150)
   - Use OpenAI streaming API
   - Yield chunks as they arrive
   - Handle streaming errors
   - Convert OpenAI chunks to text

4. **Implement validate_connection()** (lines 151-180)
   - Call OpenAI models endpoint
   - Check for valid API key
   - Return True/False

5. **Add utility methods** (lines 181-220)
   - `_convert_messages()` - Convert ApiMessage to OpenAI format
   - `_convert_response()` - Convert OpenAI response to ApiResponse
   - `_handle_openai_error()` - Handle OpenAI-specific errors

#### Code Structure:
```python
import openai
from typing import AsyncIterator, List, Optional
from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, ApiResponse

class OpenAIClient(BaseApiClient):
    """OpenAI API client using official SDK."""

    def __init__(self, provider: AIProvider):
        super().__init__(provider)
        self.openai_client = openai.AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.endpoint
        )

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ApiResponse:
        """Send request to OpenAI API."""
        try:
            openai_messages = self._convert_messages(messages)

            response = await self.openai_client.chat.completions.create(
                model=model or self.provider.model or "gpt-3.5-turbo",
                messages=openai_messages,
                temperature=temperature or self.provider.temperature,
                max_tokens=max_tokens or self.provider.max_tokens,
                **kwargs
            )

            return self._convert_response(response)

        except openai.APIError as e:
            return self._handle_openai_error(e)
```

#### Acceptance Criteria:
- ✅ Inherits from BaseApiClient correctly
- ✅ All abstract methods implemented
- ✅ OpenAI SDK initialized properly
- ✅ Message conversion works
- ✅ Streaming implemented
- ✅ Error handling for all OpenAI errors

---

### Task 3.3: Create Anthropic Client

**File:** `vibe_coder/api/anthropic_client.py`
**Difficulty:** Medium
**Time Estimate:** 4-5 hours

#### What We're Building:
A complete Anthropic Claude API client using the official Anthropic SDK. This handles Anthropic's unique system prompt format and requirements.

#### Implementation Steps:

1. **Create AnthropicClient class** (lines 1-50)
   - Import anthropic library
   - Inherit from BaseApiClient
   - Initialize Anthropic client with API key

2. **Implement send_request()** (lines 51-100)
   - Handle Anthropic's system+messages format
   - Convert ApiMessage to Claude format
   - Call Claude API with parameters
   - Convert response to ApiResponse

3. **Implement stream_request()** (lines 101-150)
   - Use Anthropic streaming API
   - Handle Claude's streaming format
   - Yield text chunks appropriately

4. **Implement validate_connection()** (lines 151-180)
   - Call Anthropic messages endpoint
   - Validate API key access

5. **Add utility methods** (lines 181-220)
   - `_convert_messages()` - Handle system prompt separation
   - `_convert_response()` - Convert Claude response
   - `_handle_anthropic_error()` - Handle Claude-specific errors

#### Code Structure:
```python
import anthropic
from typing import AsyncIterator, List, Optional
from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, ApiResponse

class AnthropicClient(BaseApiClient):
    """Anthropic Claude API client using official SDK."""

    def __init__(self, provider: AIProvider):
        super().__init__(provider)
        self.anthropic_client = anthropic.AsyncAnthropic(
            api_key=provider.api_key,
            base_url=provider.endpoint
        )

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ApiResponse:
        """Send request to Anthropic API."""
        try:
            system_message, claude_messages = self._convert_messages(messages)

            response = await self.anthropic_client.messages.create(
                model=model or self.provider.model or "claude-3-5-sonnet-20241022",
                messages=claude_messages,
                system=system_message,
                temperature=temperature or self.provider.temperature,
                max_tokens=max_tokens or self.provider.max_tokens,
                **kwargs
            )

            return self._convert_response(response)

        except anthropic.APIError as e:
            return self._handle_anthropic_error(e)
```

#### Acceptance Criteria:
- ✅ Inherits from BaseApiClient correctly
- ✅ System prompt handled according to Anthropic spec
- ✅ All abstract methods implemented
- ✅ Claude SDK initialized properly
- ✅ Streaming implemented
- ✅ Error handling for all Claude errors

---

### Task 3.4: Create Generic Client

**File:** `vibe_coder/api/generic_client.py`
**Difficulty:** Medium
**Time Estimate:** 3-4 hours

#### What We're Building:
A generic client that works with any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, LocalAI, custom providers). This provides maximum flexibility for users.

#### Implementation Steps:

1. **Create GenericClient class** (lines 1-50)
   - Inherit from BaseApiClient
   - Use httpx directly (no official SDK)
   - Add endpoint compatibility checks

2. **Implement send_request()** (lines 51-100)
   - Use OpenAI-compatible API format
   - Send POST request to /chat/completions
   - Handle different response formats
   - Support custom headers from provider config

3. **Implement stream_request()** (lines 101-150)
   - Server-sent events (SSE) parsing
   - Handle different streaming formats
   - Robust error handling for incomplete streams

4. **Implement validate_connection()** (lines 151-180)
   - Try /models or /v1/models endpoint
   - Check for OpenAI-compatible response
   - Return appropriate boolean

5. **Add flexibility features** (lines 181-220)
   - Custom header support
   - Endpoint path detection
   - Model list caching

#### Code Structure:
```python
import json
from typing import AsyncIterator, List, Optional
import httpx
from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, ApiResponse

class GenericClient(BaseApiClient):
    """Generic client for OpenAI-compatible endpoints."""

    def __init__(self, provider: AIProvider):
        super().__init__(provider)
        # Add custom headers from provider config
        if provider.headers:
            self.client.headers.update(provider.headers)

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ApiResponse:
        """Send request to generic OpenAI-compatible endpoint."""
        try:
            payload = {
                "model": model or self.provider.model or "default",
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": temperature or self.provider.temperature,
                "max_tokens": max_tokens or self.provider.max_tokens,
                **kwargs
            }

            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()

            data = response.json()
            return self._convert_response(data)

        except httpx.HTTPError as e:
            return self._handle_http_error(e)
```

#### Acceptance Criteria:
- ✅ Works with Ollama, LM Studio, vLLM, LocalAI
- ✅ Custom headers supported
- ✅ Streaming with SSE parsing
- ✅ Robust error handling
- ✅ Model detection and validation

---

### Task 3.5: Create Client Factory

**File:** `vibe_coder/api/factory.py`
**Difficulty:** Easy-Medium
**Time Estimate:** 2-3 hours

#### What We're Building:
A factory class that automatically detects the provider type and creates the appropriate client instance. This handles the complexity of provider selection from the user.

#### Implementation Steps:

1. **Create ClientFactory class** (lines 1-50)
   - Implement static method `create_client()`
   - Add provider detection logic
   - Import all client classes

2. **Implement provider detection** (lines 51-100)
   - Check endpoint URL patterns
   - Check provider name for known types
   - Default to GenericClient for unknown providers
   - Handle custom provider types

3. **Add utility methods** (lines 101-150)
   - `_is_openai_endpoint()` - URL pattern matching
   - `_is_anthropic_endpoint()` - URL pattern matching
   - `_detect_from_provider_name()` - Name-based detection

#### Code Structure:
```python
from typing import Optional
from vibe_coder.types.config import AIProvider
from vibe_coder.api.base import BaseApiClient
from vibe_coder.api.openai_client import OpenAIClient
from vibe_coder.api.anthropic_client import AnthropicClient
from vibe_coder.api.generic_client import GenericClient

class ClientFactory:
    """Factory for creating appropriate API clients."""

    @staticmethod
    def create_client(provider: AIProvider) -> BaseApiClient:
        """Create the appropriate client for the provider."""
        # Check provider name first
        if ClientFactory._detect_from_name(provider.name):
            return ClientFactory._detect_from_name(provider.name)(provider)

        # Check endpoint URL
        if ClientFactory._is_openai_endpoint(provider.endpoint):
            return OpenAIClient(provider)
        elif ClientFactory._is_anthropic_endpoint(provider.endpoint):
            return AnthropicClient(provider)

        # Default to generic client
        return GenericClient(provider)

    @staticmethod
    def _detect_from_name(name: str) -> Optional[type]:
        """Detect client type from provider name."""
        name_lower = name.lower()
        if "openai" in name_lower or "gpt" in name_lower:
            return OpenAIClient
        elif "anthropic" in name_lower or "claude" in name_lower:
            return AnthropicClient
        elif "ollama" in name_lower:
            return GenericClient  # Ollama works with generic
        return None
```

#### Acceptance Criteria:
- ✅ Correctly detects OpenAI endpoints
- ✅ Correctly detects Anthropic endpoints
- ✅ Falls back to GenericClient appropriately
- ✅ Provider name detection works
- ✅ Easy to extend for new providers

---

## Testing Strategy for Phase 3

### Test Files to Create:

1. **tests/test_api/test_base.py** (lines 1-50)
   - Test BaseApiClient is abstract
   - Test httpx client initialization
   - Test utility methods

2. **tests/test_api/test_openai_client.py** (lines 1-150)
   - Test message conversion
   - Test API request/response handling
   - Test streaming functionality
   - Test error handling
   - Use pytest-asyncio for async tests

3. **tests/test_api/test_anthropic_client.py** (lines 1-150)
   - Test system prompt handling
   - Test message conversion
   - Test Claude API integration
   - Test streaming

4. **tests/test_api/test_generic_client.py** (lines 1-150)
   - Test with different endpoint formats
   - Test custom header support
   - Test SSE streaming
   - Test error handling

5. **tests/test_api/test_factory.py** (lines 1-50)
   - Test provider detection
   - Test client creation
   - Test edge cases

### Mocking Strategy:
- Use pytest-mock for mocking HTTP responses
- Create fixtures for different provider configurations
- Mock OpenAI and Anthropic SDKs for unit tests
- Integration tests with real endpoints (optional)

### Running Tests:
```bash
make test                    # Run all tests
make test-cov              # Run with coverage
poetry run pytest tests/test_api/  # Run API tests only
```

---

## Development Workflow

### Step-by-Step:

**Day 1 (Task 3.1 & 3.2):**
1. Create BaseApiClient abstract class
2. Define all abstract methods and interfaces
3. Start OpenAIClient implementation
4. Test with mock responses

**Day 2 (Task 3.3):**
1. Complete OpenAIClient
2. Create AnthropicClient
3. Handle Claude-specific requirements
4. Test both clients with mocking

**Day 3 (Task 3.4):**
1. Create GenericClient
2. Test with Ollama endpoint
3. Test SSE streaming
4. Add custom header support

**Day 4 (Task 3.5 & Testing):**
1. Create ClientFactory
2. Test provider detection
3. Write comprehensive tests
4. Fix any issues found

**Day 5 (Integration & Polish):**
1. Integration tests with real APIs (optional)
2. Error handling improvements
3. Documentation
4. Run full test suite
5. Code formatting and linting

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

### How Phase 3 Connects to Other Phases:

**Phase 3 → Phase 4 (Interactive Prompts):**
- Chat interface will use ClientFactory to create clients
- Pass conversation history to API clients
- Display streaming responses in terminal

**Phase 3 → CLI (commands/cli.py):**
- Commands will create clients through ClientFactory
- Handle API errors gracefully
- Show connection status to users

**Phase 3 → Configuration (Phase 2):**
- Use AIProvider config from ConfigManager
- Validate connections during setup
- Handle environment variable providers

### Data Flow Example:
```
User runs: vibe-coder chat --provider my-claude
    ↓
CLI command gets provider from ConfigManager
    ↓
ClientFactory.create_client(provider) → AnthropicClient
    ↓
Chat interface calls client.send_request(messages)
    ↓
Claude API returns response
    ↓
Response displayed in terminal with Rich formatting
```

---

## File Structure After Phase 3

```
vibe_coder/
├── api/
│   ├── __init__.py
│   ├── base.py             # NEW: BaseApiClient abstract class
│   ├── openai_client.py    # NEW: OpenAI API client
│   ├── anthropic_client.py # NEW: Anthropic Claude client
│   ├── generic_client.py   # NEW: Generic OpenAI-compatible client
│   └── factory.py          # NEW: Client factory for auto-detection
├── types/
│   ├── config.py           # ✅ From Phase 2
│   └── api.py              # ✅ From Phase 2
├── config/
│   ├── manager.py          # ✅ From Phase 2
│   ├── env_handler.py      # ✅ From Phase 2
│   └── validator.py        # ✅ From Phase 2
└── cli.py                  # ✅ From Phase 1

tests/
├── test_config/            # ✅ From Phase 2
└── test_api/               # NEW: API client tests
    ├── test_base.py
    ├── test_openai_client.py
    ├── test_anthropic_client.py
    ├── test_generic_client.py
    └── test_factory.py
```

---

## Success Criteria for Phase 3

By end of this phase:
- ✅ BaseApiClient abstract class defined
- ✅ OpenAI client working with official SDK
- ✅ Anthropic client working with official SDK
- ✅ Generic client working with Ollama/LM Studio
- ✅ ClientFactory automatically detects providers
- ✅ All clients support streaming
- ✅ Comprehensive error handling
- ✅ All tests passing (>80% coverage)
- ✅ Code formatted and linted
- ✅ Integration with Phase 2 configuration system

---

## Known Challenges & Solutions

### Challenge 1: Different Message Formats
**Problem:** OpenAI uses messages array, Anthropic separates system prompt
**Solution:** Convert in each client's _convert_messages() method

### Challenge 2: Streaming Formats
**Problem:** Each provider streams differently
**Solution:** Abstract streaming interface, provider-specific implementations

### Challenge 3: Error Response Formats
**Problem:** Different error structures from each provider
**Solution:** Provider-specific error handlers, unified ApiResponse format

### Challenge 4: Rate Limiting
**Problem:** Different rate limits and headers
**Solution:** Client-specific rate limit detection and handling

### Challenge 5: Model Names
**Problem:** Different models per provider
**Solution:** Provider defaults, allow overrides in API calls

---

## Dependencies to Add

Update pyproject.toml:
```toml
[tool.poetry.dependencies]
# ... existing dependencies
openai = "^1.0.0"
anthropic = "^0.25.0"

[tool.poetry.group.dev.dependencies]
# ... existing dependencies
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
```

Run: `poetry add openai anthropic` and `poetry add --group dev pytest-asyncio pytest-mock`

---

## Questions to Answer Before Starting:

1. **Real API Testing:** Will you test with real API keys?
   - Recommended: Mock for unit tests, real for manual verification

2. **Streaming Priority:** Implement streaming first or basic requests?
   - Recommended: Basic requests first, then add streaming

3. **Error Handling:** How much error detail to show users?
   - Recommended: User-friendly messages, detailed errors in debug mode

4. **Timeout Values:** What timeouts for different operations?
   - Recommended: 60s for requests, 30s for connection validation

---

## Related Documentation

- **PHASE_2_PLAN.md** - Configuration system details
- **ROADMAP_PYTHON.md** - Full project timeline
- **README.md** - Project overview
- **OpenAI API Docs:** https://platform.openai.com/docs/api-reference
- **Anthropic API Docs:** https://docs.anthropic.com/claude/reference

---

Phase 3 will transform the configuration system from Phase 2 into a working API integration layer. By the end of this phase, Vibe Coder will be able to connect to multiple AI providers and send/receive messages, setting the foundation for the interactive chat interface in Phase 4.

Let's build Phase 3! 🚀