"""Test BaseApiClient abstract class and common functionality."""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


# Create a concrete implementation for testing
class TestClient(BaseApiClient):
    """Test implementation of BaseApiClient."""

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> ApiResponse:
        """Test implementation."""
        return ApiResponse(
            content="Test response",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            finish_reason="stop",
        )

    async def stream_request(
        self,
        messages: List[ApiMessage],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Test implementation."""
        yield "Streamed chunk 1"
        yield "Streamed chunk 2"

    async def validate_connection(self) -> bool:
        """Test implementation."""
        return True


class TestBaseApiClient:
    """Test BaseApiClient base class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AIProvider(
            name="test",
            api_key="test-key-1234567890",
            endpoint="https://api.test.com/v1",
            model="test-model",
            temperature=0.7,
            max_tokens=1000,
        )
        self.client = TestClient(self.provider)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization with provider config."""
        assert self.client.provider == self.provider
        assert str(self.client.client.base_url) == self.provider.endpoint + "/"
        assert "Authorization" not in self.client.client.headers  # No auth in base
        assert self.client.client.headers["Content-Type"] == "application/json"
        assert self.client.client.headers["User-Agent"] == "vibe-coder/0.1.0"

    @pytest.mark.asyncio
    async def test_initialization_with_custom_headers(self):
        """Test initialization with custom provider headers."""
        provider = AIProvider(
            name="test",
            api_key="test-key",
            endpoint="https://api.test.com",
            headers={"X-Custom": "value", "Authorization": "Bearer token"},
        )
        client = TestClient(provider)

        assert client.client.headers["X-Custom"] == "value"
        assert client.client.headers["Authorization"] == "Bearer token"

    def test_get_headers(self):
        """Test default headers generation."""
        headers = self.client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "vibe-coder/0.1.0"
        assert "X-Custom" not in headers

    def test_get_headers_with_provider_headers(self):
        """Test headers with provider custom headers."""
        provider = AIProvider(
            name="test",
            api_key="test-key",
            endpoint="https://api.test.com",
            headers={"X-API-Version": "v1", "X-Debug": "true"},
        )
        client = TestClient(provider)

        headers = client._get_headers()
        assert headers["X-API-Version"] == "v1"
        assert headers["X-Debug"] == "true"
        assert headers["Content-Type"] == "application/json"  # Still includes defaults

    @pytest.mark.asyncio
    async def test_estimate_tokens(self):
        """Test token estimation."""
        text = "Hello, world! This is a test."
        # Rough estimation: ~4 chars per token
        expected = max(1, len(text) // 4)

        result = await self.client.estimate_tokens(text)
        assert result == expected

    @pytest.mark.asyncio
    async def test_estimate_tokens_empty_string(self):
        """Test token estimation with empty string."""
        result = await self.client.estimate_tokens("")
        assert result == 1  # Minimum is 1

    @pytest.mark.asyncio
    async def test_estimate_tokens_short_text(self):
        """Test token estimation with very short text."""
        result = await self.client.estimate_tokens("Hi")
        assert result == 1  # Minimum is 1

    def test_format_error_response_api_key_error(self):
        """Test error response formatting for API key errors."""
        error = Exception("Invalid API key provided")

        response = self.client._format_error_response(error, "auth")

        assert "Error: Invalid API key or authentication failed" in response.content
        assert response.usage.total_tokens == 0
        assert response.finish_reason == "error"
        assert response.error["type"] == "auth"
        # Note: The error message sanitization happens at the response content level

    def test_format_error_response_rate_limit_error(self):
        """Test error response formatting for rate limit errors."""
        error = Exception("Rate limit exceeded")

        response = self.client._format_error_response(error, "rate_limit")

        assert "Error: Rate limit exceeded" in response.content
        assert response.error["type"] == "rate_limit"

    def test_format_error_response_connection_error(self):
        """Test error response formatting for connection errors."""
        error = Exception("Connection failed")

        response = self.client._format_error_response(error, "network")

        assert "Error: Connection failed" in response.content
        assert "network" in response.error["message"]

    def test_format_error_response_generic_error(self):
        """Test error response formatting for generic errors."""
        error = Exception("Something went wrong")

        response = self.client._format_error_response(error, "unknown")

        assert "Error: Something went wrong" in response.content
        assert response.error["original"] == "Something went wrong"

    def test_convert_messages_to_dict(self):
        """Test converting ApiMessage objects to dictionaries."""
        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="System prompt"),
            ApiMessage(role=MessageRole.USER, content="User message"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Assistant response"),
        ]

        result = self.client._convert_messages_to_dict(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "System prompt"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_validate_messages_success(self):
        """Test successful message validation."""
        messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
        ]

        # Should not raise
        self.client._validate_messages(messages)

    def test_validate_messages_empty(self):
        """Test validation fails with empty messages."""
        with pytest.raises(ValueError, match="At least one message is required"):
            self.client._validate_messages([])

    def test_validate_messages_invalid_type(self):
        """Test validation fails with invalid message type."""
        messages = ["not a message"]

        with pytest.raises(ValueError, match="Message 0 is not a valid ApiMessage"):
            self.client._validate_messages(messages)

    def test_validate_messages_empty_content(self):
        """Test validation fails with empty content."""
        messages = [
            ApiMessage(role=MessageRole.USER, content="   "),
        ]

        with pytest.raises(ValueError, match="Message 0 has empty content"):
            self.client._validate_messages(messages)

    def test_validate_messages_tool_message_allowed_empty(self):
        """Test that tool messages can have empty content."""
        messages = [
            ApiMessage(role=MessageRole.TOOL, content="", tool_call_id="test"),
        ]

        # Should not raise for tool messages
        self.client._validate_messages(messages)

    def test_prepare_request_params(self):
        """Test preparing request parameters."""
        result = self.client._prepare_request_params(
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
            custom_param="value",
            none_param=None,
        )

        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.5
        assert result["max_tokens"] == 2000
        assert result["custom_param"] == "value"
        assert "none_param" not in result  # None values should be removed

    def test_prepare_request_params_defaults(self):
        """Test preparing request parameters with provider defaults."""
        result = self.client._prepare_request_params(
            model=None,
            temperature=None,
            max_tokens=None,
        )

        assert result["model"] == self.provider.model
        assert result["temperature"] == self.provider.temperature
        assert result["max_tokens"] == self.provider.max_tokens

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with TestClient(self.provider) as client:
            assert isinstance(client, TestClient)

        # client.close() should have been called
        # In a real scenario, we'd mock close to verify it was called

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the HTTP client."""
        with patch.object(self.client.client, "aclose", new_callable=AsyncMock) as mock_close:
            await self.client.close()
            mock_close.assert_called_once()
