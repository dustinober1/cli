"""Test Anthropic Claude API client implementation."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Any, Dict, List

import anthropic
from anthropic.types import Message, ContentBlock, TextBlock, ToolUseBlock, Usage

from vibe_coder.api.anthropic_client import AnthropicClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


def create_mock_anthropic_error(error_class, message: str):
    """Helper to create mock Anthropic errors with proper parameters."""

    # Different error classes have different required parameters
    if error_class == anthropic.APIError:
        mock_request = Mock()
        return error_class(
            message=message,
            request=mock_request,
            body=None
        )
    else:
        # For AuthenticationError and other status errors
        mock_response = Mock()
        return error_class(
            message=message,
            response=mock_response,
            body=None
        )


# Integration tests - only run with ANTHROPIC_API_KEY
pytest.importorskip("anthropic")


def has_anthropic_key():
    """Check if Anthropic API key is available for integration tests."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


class TestAnthropicClientUnit:
    """Unit tests for AnthropicClient (mocked)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AIProvider(
            name="anthropic",
            api_key="sk-ant-test-key-1234567890",
            endpoint="https://api.anthropic.com",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=1000,
        )

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        with patch('vibe_coder.api.anthropic_client.AsyncAnthropic') as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.messages = AsyncMock()
            mock_instance.messages.create = AsyncMock()
            mock_instance.messages.stream = MagicMock()
            yield mock_instance

    @pytest.fixture
    def client(self, mock_anthropic_client):
        """Create AnthropicClient with mocked dependencies."""
        return AnthropicClient(self.provider)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization."""
        with patch('vibe_coder.api.anthropic_client.AsyncAnthropic') as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            client = AnthropicClient(self.provider)

            mock.assert_called_once_with(
                api_key=self.provider.api_key,
                base_url=self.provider.endpoint,
                timeout=60.0,
                max_retries=3
            )
            assert client.provider == self.provider

    @pytest.mark.asyncio
    async def test_send_request_success(self, client, mock_anthropic_client):
        """Test successful request sending."""
        # Mock response
        mock_response = MagicMock(spec=Message)
        mock_response.content = [
            TextBlock(text="Test response", type="text")
        ]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.content == "Test response"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.finish_reason == "stop"

        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]['system'] is None
        assert len(call_args[1]['messages']) == 1
        assert call_args[1]['max_tokens'] == 1000  # From provider

    @pytest.mark.asyncio
    async def test_send_request_with_system_message(self, client, mock_anthropic_client):
        """Test sending request with system message."""
        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Response", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="System prompt"),
            ApiMessage(role=MessageRole.USER, content="User message")
        ]
        await client.send_request(messages)

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]['system'] == "System prompt"
        assert len(call_args[1]['messages']) == 1  # System message is separate

    @pytest.mark.asyncio
    async def test_send_request_requires_max_tokens(self, client, mock_anthropic_client):
        """Test that max_tokens is required for Anthropic."""
        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Response", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        provider_no_max = AIProvider(
            name="anthropic",
            api_key="test-key",
            endpoint="https://api.anthropic.com",
            model="claude-3-sonnet",
            temperature=0.7,
            max_tokens=None,  # No max_tokens
        )
        client = AnthropicClient(provider_no_max)

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        await client.send_request(messages)

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]['max_tokens'] == 4096  # Default value

    @pytest.mark.asyncio
    async def test_send_request_with_tools(self, client, mock_anthropic_client):
        """Test sending request with tools."""
        mock_response = MagicMock(spec=Message)
        tool_use = ToolUseBlock(
            id="toolu_1",
            type="tool_use",
            name="test_function",
            input={"arg": "value"}
        )
        mock_response.content = [tool_use]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "tool_use"

        mock_anthropic_client.messages.create.return_value = mock_response

        tools = [{"type": "function", "function": {"name": "test", "description": "Test function"}}]
        messages = [ApiMessage(role=MessageRole.USER, content="Use tool")]
        response = await client.send_request(messages, tools=tools)

        assert response.tool_calls == [tool_use]
        assert response.finish_reason == "tool_calls"

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]['tools'] == tools

    @pytest.mark.asyncio
    async def test_send_request_with_assistant_tool_calls(self, client, mock_anthropic_client):
        """Test sending request with tool calls in assistant message."""
        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Final response", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        tool_calls = [{
            "type": "tool_use",
            "id": "toolu_1",
            "name": "test_function",
            "input": {"arg": "value"}
        }]
        messages = [
            ApiMessage(role=MessageRole.USER, content="Use tool"),
            ApiMessage(role=MessageRole.ASSISTANT, content="", tool_calls=tool_calls)
        ]
        await client.send_request(messages)

        call_args = mock_anthropic_client.messages.create.call_args
        claude_messages = call_args[1]['messages']
        assistant_msg = claude_messages[1]
        assert assistant_msg['role'] == 'assistant'
        assert tool_calls[0] in assistant_msg['content']

    @pytest.mark.asyncio
    async def test_send_request_with_tool_result(self, client, mock_anthropic_client):
        """Test sending request with tool result."""
        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Got the result", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 30
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        messages = [
            ApiMessage(role=MessageRole.USER, content="Use tool"),
            ApiMessage(role=MessageRole.TOOL, content="Tool result", tool_call_id="toolu_1")
        ]
        await client.send_request(messages)

        call_args = mock_anthropic_client.messages.create.call_args
        claude_messages = call_args[1]['messages']
        tool_msg = claude_messages[1]
        assert tool_msg['role'] == 'user'
        assert tool_msg['content'][0]['type'] == 'tool_result'
        assert tool_msg['content'][0]['tool_use_id'] == 'toolu_1'
        assert tool_msg['content'][0]['content'] == 'Tool result'

    @pytest.mark.asyncio
    async def test_send_request_with_openai_style_tool_calls(self, client, mock_anthropic_client):
        """Test converting OpenAI-style tool calls to Anthropic format."""
        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Response", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        # OpenAI-style tool call
        openai_tool_calls = [{
            "type": "function",
            "id": "call_1",
            "function": {
                "name": "test_function",
                "arguments": '{"arg": "value"}'
            }
        }]
        messages = [
            ApiMessage(role=MessageRole.USER, content="Use tool"),
            ApiMessage(role=MessageRole.ASSISTANT, content="", tool_calls=openai_tool_calls)
        ]
        await client.send_request(messages)

        call_args = mock_anthropic_client.messages.create.call_args
        claude_messages = call_args[1]['messages']
        assistant_msg = claude_messages[1]
        # Should convert to Anthropic format
        tool_use = None
        for content in assistant_msg['content']:
            if content.get('type') == 'tool_use':
                tool_use = content
                break
        assert tool_use is not None
        assert tool_use['id'] == 'call_1'
        assert tool_use['name'] == 'test_function'
        assert tool_use['input'] == '{"arg": "value"}'

    @pytest.mark.asyncio
    async def test_stream_request_success(self, client, mock_anthropic_client):
        """Test successful streaming request."""
        # Mock stream context manager
        mock_stream = AsyncMock()
        mock_stream.text_stream.__aiter__.return_value = ["Hello", " world", "!"]
        mock_anthropic_client.messages.stream.return_value.__aenter__.return_value = mock_stream

        messages = [ApiMessage(role=MessageRole.USER, content="Stream test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == ["Hello", " world", "!"]

        mock_anthropic_client.messages.stream.assert_called_once()
        call_args = mock_anthropic_client.messages.stream.call_args
        assert call_args[1]['system'] is None
        assert len(call_args[1]['messages']) == 1
        assert call_args[1]['max_tokens'] == 1000

    @pytest.mark.asyncio
    async def test_stream_request_with_system_message(self, client, mock_anthropic_client):
        """Test streaming with system message."""
        mock_stream = AsyncMock()
        mock_stream.text_stream.__aiter__.return_value = ["Response"]
        mock_anthropic_client.messages.stream.return_value.__aenter__.return_value = mock_stream

        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="System prompt"),
            ApiMessage(role=MessageRole.USER, content="Test")
        ]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        call_args = mock_anthropic_client.messages.stream.call_args
        assert call_args[1]['system'] == "System prompt"

    @pytest.mark.asyncio
    async def test_stream_request_error(self, mock_anthropic_client):
        """Test streaming with error."""
        mock_anthropic_client.messages.stream.side_effect = create_mock_anthropic_error(
            anthropic.APIError, "Stream error"
        )

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert len(result) == 1
        assert "[Error:" in result[0]

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, mock_anthropic_client):
        """Test successful connection validation."""
        mock_anthropic_client.messages.create.return_value = MagicMock()

        client = AnthropicClient(self.provider)
        result = await client.validate_connection()

        assert result is True
        mock_anthropic_client.messages.create.assert_called_once_with(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

    @pytest.mark.asyncio
    async def test_validate_connection_auth_error(self, mock_anthropic_client):
        """Test connection validation with auth error."""
        mock_anthropic_client.messages.create.side_effect = create_mock_anthropic_error(
            anthropic.AuthenticationError, "Invalid API key"
        )

        client = AnthropicClient(self.provider)
        result = await client.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_connection_network_error(self, mock_anthropic_client):
        """Test connection validation with network error."""
        mock_anthropic_client.messages.create.side_effect = anthropic.NetworkError("Connection failed")

        client = AnthropicClient(self.provider)
        result = await client.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test model listing (static list)."""
        client = AnthropicClient(self.provider)
        models = await client.list_models()

        assert len(models) > 0
        assert "claude-3-5-sonnet-20241022" in models
        assert "claude-3-opus-20240229" in models
        assert "claude-3-haiku-20240307" in models

    @pytest.mark.asyncio
    async def test_handle_anthropic_error_rate_limit(self, mock_anthropic_client):
        """Test Anthropic rate limit error handling."""
        mock_anthropic_client.messages.create.side_effect = anthropic.RateLimitError("Rate limit exceeded")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "rate_limit"

    @pytest.mark.asyncio
    async def test_handle_anthropic_error_authentication(self, mock_anthropic_client):
        """Test Anthropic authentication error handling."""
        mock_anthropic_client.messages.create.side_effect = anthropic.AuthenticationError("Invalid API key")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "authentication"

    @pytest.mark.asyncio
    async def test_handle_anthropic_error_network(self, mock_anthropic_client):
        """Test Anthropic network error handling."""
        mock_anthropic_client.messages.create.side_effect = anthropic.NetworkError("Connection failed")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "network"

    @pytest.mark.asyncio
    async def test_handle_anthropic_error_permission(self, mock_anthropic_client):
        """Test Anthropic permission error handling."""
        mock_anthropic_client.messages.create.side_effect = anthropic.APIError("Permission denied")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "permission_denied"

    @pytest.mark.asyncio
    async def test_handle_anthropic_error_api_error(self, mock_anthropic_client):
        """Test generic Anthropic API error handling."""
        mock_anthropic_client.messages.create.side_effect = anthropic.APIError("API error occurred")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "anthropic_error"

    @pytest.mark.asyncio
    async def test_handle_generic_error(self, mock_anthropic_client):
        """Test generic error handling."""
        mock_anthropic_client.messages.create.side_effect = Exception("Unexpected error")

        client = AnthropicClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "unknown"

    @pytest.mark.asyncio
    async def test_convert_response_with_text_and_tool_calls(self):
        """Test converting response with both text and tool calls."""
        client = AnthropicClient(self.provider)

        # Mock response with text and tool calls
        mock_response = MagicMock(spec=Message)
        text_block = TextBlock(text="Here's the result:", type="text")
        tool_block = ToolUseBlock(
            id="toolu_1",
            type="tool_use",
            name="search",
            input={"query": "test"}
        )
        mock_response.content = [text_block, tool_block]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "tool_use"

        response = client._convert_response_from_anthropic(mock_response)

        assert response.content == "Here's the result:"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["id"] == "toolu_1"
        assert response.tool_calls[0]["name"] == "search"
        assert response.finish_reason == "tool_calls"

    @pytest.mark.asyncio
    async def test_convert_response_dict_content(self):
        """Test converting response with dict content blocks."""
        client = AnthropicClient(self.provider)

        # Mock response with dict content (some SDK versions return dicts)
        mock_response = MagicMock(spec=Message)
        mock_response.content = [
            {"type": "text", "text": "Response from dict"},
            {"type": "tool_use", "id": "toolu_2", "name": "calc", "input": {"x": 1}}
        ]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 15
        mock_response.stop_reason = "end_turn"

        response = client._convert_response_from_anthropic(mock_response)

        assert response.content == "Response from dict"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["id"] == "toolu_2"

    @pytest.mark.asyncio
    async def test_convert_response_no_usage(self):
        """Test converting response without usage info."""
        client = AnthropicClient(self.provider)

        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Response", type="text")]
        mock_response.usage = None
        mock_response.stop_reason = "end_turn"

        response = client._convert_response_from_anthropic(mock_response)

        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0
        assert response.usage.total_tokens == 0

    @pytest.mark.asyncio
    async def test_convert_response_unknown_finish_reason(self):
        """Test converting response with unknown finish reason."""
        client = AnthropicClient(self.provider)

        mock_response = MagicMock(spec=Message)
        mock_response.content = [TextBlock(text="Response", type="text")]
        mock_response.usage = MagicMock(spec=Usage)
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "unknown_reason"

        response = client._convert_response_from_anthropic(mock_response)

        assert response.finish_reason == "unknown"

    @pytest.mark.asyncio
    async def test_convert_messages_empty(self):
        """Test converting messages with no user message."""
        client = AnthropicClient(self.provider)

        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="System only")
        ]

        with pytest.raises(ValueError, match="At least one user message is required"):
            client._convert_messages_to_anthropic(messages)

    @pytest.mark.asyncio
    async def test_close(self, mock_anthropic_client):
        """Test closing client."""
        client = AnthropicClient(self.provider)
        client.anthropic_client.close = AsyncMock()

        await client.close()

        client.anthropic_client.close.assert_called_once()


class TestAnthropicClientIntegration:
    """Integration tests for AnthropicClient (requires real API key)."""

    def setup_method(self):
        """Set up test fixtures."""
        if not has_anthropic_key():
            pytest.skip("ANTHROPIC_API_KEY not set")

        self.provider = AIProvider(
            name="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            endpoint="https://api.anthropic.com",
            model="claude-3-haiku-20240307",  # Use cheaper model for tests
            temperature=0.7,
            max_tokens=100,
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_send_request(self):
        """Integration test: send a real request to Anthropic."""
        client = AnthropicClient(self.provider)
        messages = [
            ApiMessage(role=MessageRole.USER, content="Say 'Hello, Claude!' in exactly those words.")
        ]

        response = await client.send_request(messages)

        assert response.content
        assert "Hello, Claude!" in response.content
        assert response.usage.total_tokens > 0
        assert response.finish_reason == "stop"

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_stream_request(self):
        """Integration test: stream a real response from Anthropic."""
        client = AnthropicClient(self.provider)
        messages = [
            ApiMessage(role=MessageRole.USER, content="Count from 1 to 5 slowly.")
        ]

        chunks = []
        async for chunk in client.stream_request(messages):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert full_response
        assert len(chunks) > 0  # Should have multiple chunks

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_validate_connection(self):
        """Integration test: validate connection to Anthropic."""
        client = AnthropicClient(self.provider)
        result = await client.validate_connection()
        assert result is True

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_with_system_message(self):
        """Integration test: send request with system message."""
        client = AnthropicClient(self.provider)
        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant. Always end with '🤖'."),
            ApiMessage(role=MessageRole.USER, content="Say hello.")
        ]

        response = await client.send_request(messages)

        assert response.content
        assert "🤖" in response.content

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_list_models(self):
        """Integration test: list available Claude models."""
        client = AnthropicClient(self.provider)
        models = await client.list_models()

        assert len(models) > 0
        assert all("claude" in model for model in models)

        await client.close()