"""Test OpenAI API client implementation."""

import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import openai
import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from vibe_coder.api.openai_client import OpenAIClient
from vibe_coder.types.api import ApiMessage, MessageRole
from vibe_coder.types.config import AIProvider

# Integration tests - only run with OPENAI_API_KEY
pytest.importorskip("openai")


def has_openai_key():
    """Check if OpenAI API key is available for integration tests."""
    return bool(os.getenv("OPENAI_API_KEY"))


def create_mock_openai_error(error_class, message: str):
    """Helper to create mock OpenAI errors with proper parameters for SDK v1.x."""
    from httpx import Request, Response

    # Create a mock request and response for errors that need them
    request = Request("POST", "https://api.openai.com/v1/chat/completions")
    response = Response(
        status_code=400,
        request=request,
        json={"error": {"message": message, "type": error_class.__name__}},
    )
    body = response.json()

    # Different error classes have different required parameters
    if error_class == openai.APIStatusError:
        # APIStatusError requires response and body as keyword-only arguments
        return error_class(message=message, response=response, body=body)
    elif error_class == openai.APIError:
        # APIError requires request and body as keyword-only arguments
        return error_class(request=request, message=message, body=body)
    elif error_class == openai.APIConnectionError:
        # APIConnectionError requires request as keyword-only argument
        return error_class(request=request, message=message)
    elif error_class == openai.RateLimitError:
        # RateLimitError is a subclass of APIStatusError, needs response and body
        return error_class(message=message, response=response, body=body)
    elif error_class == openai.AuthenticationError:
        # AuthenticationError is a subclass of APIStatusError, needs response and body
        return error_class(message=message, response=response, body=body)
    else:
        # For other errors, try with just the message
        try:
            return error_class(message=message)
        except TypeError:
            # Fallback: create a mock object with the message
            mock_error = Mock()
            mock_error.message = message
            mock_error.__class__ = error_class
            return mock_error


async def mock_async_stream(chunks):
    """Create an async iterator from a list of chunks."""
    for chunk in chunks:
        yield chunk


class TestOpenAIClientUnit:
    """Unit tests for OpenAIClient (mocked)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AIProvider(
            name="openai",
            api_key="sk-test-key-1234567890",
            endpoint="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
        )

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        with patch("vibe_coder.api.openai_client.AsyncOpenAI") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.chat = AsyncMock()
            mock_instance.chat.completions = AsyncMock()
            mock_instance.models = AsyncMock()
            yield mock_instance

    @pytest.fixture
    def client(self, mock_openai_client):
        """Create OpenAIClient with mocked dependencies."""
        return OpenAIClient(self.provider)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization."""
        with patch("vibe_coder.api.openai_client.AsyncOpenAI") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            client = OpenAIClient(self.provider)

            mock.assert_called_once_with(
                api_key=self.provider.api_key,
                base_url=self.provider.endpoint,
                timeout=60.0,
                max_retries=3,
            )
            assert client.provider == self.provider

    @pytest.mark.asyncio
    async def test_send_request_success(self, client, mock_openai_client):
        """Test successful request sending."""
        # Mock response
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content="Test response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_openai_client.chat.completions.create.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.content == "Test response"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.finish_reason == "stop"

        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_request_with_system_message(self, client, mock_openai_client):
        """Test sending request with system message."""
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content="Response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)

        mock_openai_client.chat.completions.create.return_value = mock_response

        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="System prompt"),
            ApiMessage(role=MessageRole.USER, content="User message"),
        ]
        await client.send_request(messages)

        # Verify system message is first
        call_args = mock_openai_client.chat.completions.create.call_args
        openai_messages = call_args[1]["messages"]
        assert openai_messages[0]["role"] == "system"
        assert openai_messages[0]["content"] == "System prompt"
        assert openai_messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_send_request_with_tools(self, client, mock_openai_client):
        """Test sending request with tools."""
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content=""),
                finish_reason="tool_calls",
            )
        ]
        mock_response.choices[0].message.tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "test_func", "arguments": "{}"},
            }
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        mock_openai_client.chat.completions.create.return_value = mock_response

        tools = [{"type": "function", "function": {"name": "test", "description": "Test function"}}]
        messages = [ApiMessage(role=MessageRole.USER, content="Use tool")]
        response = await client.send_request(messages, tools=tools)

        assert response.tool_calls == [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "test_func", "arguments": "{}"},
            }
        ]

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["tools"] == tools

    @pytest.mark.asyncio
    async def test_send_request_with_overrides(self, client, mock_openai_client):
        """Test sending request with parameter overrides."""
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content="Response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        mock_openai_client.chat.completions.create.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        await client.send_request(
            messages, model="gpt-4", temperature=0.5, max_tokens=2000, custom_param="value"
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 2000
        assert call_args[1]["custom_param"] == "value"

    @pytest.mark.asyncio
    async def test_send_request_with_tool_calls_in_message(self, client, mock_openai_client):
        """Test sending request with tool calls in assistant message."""
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content=""),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        mock_openai_client.chat.completions.create.return_value = mock_response

        tool_calls = [
            {"id": "call_1", "type": "function", "function": {"name": "test", "arguments": "{}"}}
        ]
        messages = [
            ApiMessage(role=MessageRole.USER, content="Use tool"),
            ApiMessage(role=MessageRole.ASSISTANT, content="", tool_calls=tool_calls),
        ]
        await client.send_request(messages)

        call_args = mock_openai_client.chat.completions.create.call_args
        openai_messages = call_args[1]["messages"]
        assistant_msg = openai_messages[1]  # Skip system if present
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["tool_calls"] == tool_calls

    @pytest.mark.asyncio
    async def test_send_request_with_tool_message(self, client, mock_openai_client):
        """Test sending request with tool response message."""
        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content="Final response"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)

        mock_openai_client.chat.completions.create.return_value = mock_response

        messages = [
            ApiMessage(role=MessageRole.USER, content="Use tool"),
            ApiMessage(role=MessageRole.TOOL, content="Tool result", tool_call_id="call_1"),
        ]
        await client.send_request(messages)

        call_args = mock_openai_client.chat.completions.create.call_args
        openai_messages = call_args[1]["messages"]
        tool_msg = openai_messages[-1]
        assert tool_msg["role"] == "tool"
        assert tool_msg["content"] == "Tool result"
        assert tool_msg["tool_call_id"] == "call_1"

    @pytest.mark.asyncio
    async def test_stream_request_success(self, client, mock_openai_client):
        """Test successful streaming request."""
        # Create mock stream chunks
        chunks = []
        for i, content in enumerate(["Hello", " world", "!"]):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta = MagicMock()
            chunk.choices[0].delta.content = content
            chunks.append(chunk)

        mock_openai_client.chat.completions.create.return_value = mock_async_stream(chunks)

        messages = [ApiMessage(role=MessageRole.USER, content="Stream test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == ["Hello", " world", "!"]

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["stream"] is True

    @pytest.mark.asyncio
    async def test_stream_request_with_empty_chunks(self, client, mock_openai_client):
        """Test streaming request with empty chunks."""
        chunks = []
        for i in range(3):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta = MagicMock()
            chunk.choices[0].delta.content = None  # No content
            chunks.append(chunk)

        mock_openai_client.chat.completions.create.return_value = mock_async_stream(chunks)

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == []  # Should not yield anything for empty chunks

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, mock_openai_client):
        """Test successful connection validation."""
        mock_openai_client.models.list.return_value = ["gpt-3.5-turbo", "gpt-4"]

        client = OpenAIClient(self.provider)
        result = await client.validate_connection()

        assert result is True
        mock_openai_client.models.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_connection_auth_error(self, mock_openai_client):
        """Test connection validation with auth error."""
        mock_openai_client.models.list.side_effect = create_mock_openai_error(
            openai.AuthenticationError, "Invalid API key"
        )

        client = OpenAIClient(self.provider)
        result = await client.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_connection_network_error(self, mock_openai_client):
        """Test connection validation with network error."""
        mock_openai_client.models.list.side_effect = create_mock_openai_error(
            openai.APIConnectionError, "Connection failed"
        )

        client = OpenAIClient(self.provider)
        result = await client.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_list_models_success(self, mock_openai_client):
        """Test successful model listing."""
        mock_models = []
        for model_id in ["gpt-3.5-turbo", "text-davinci-003", "gpt-4"]:
            model = MagicMock()
            model.id = model_id
            mock_models.append(model)

        mock_openai_client.models.list.return_value = MagicMock(data=mock_models)

        client = OpenAIClient(self.provider)
        result = await client.list_models()

        assert result == ["gpt-3.5-turbo", "gpt-4"]  # Only gpt models

    @pytest.mark.asyncio
    async def test_list_models_error(self, mock_openai_client):
        """Test model listing with error."""
        mock_openai_client.models.list.side_effect = Exception("API error")

        client = OpenAIClient(self.provider)
        result = await client.list_models()

        assert result == []

    @pytest.mark.asyncio
    async def test_handle_openai_error_rate_limit(self, mock_openai_client):
        """Test OpenAI rate limit error handling."""
        mock_openai_client.chat.completions.create.side_effect = create_mock_openai_error(
            openai.RateLimitError, "Rate limit exceeded"
        )

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "rate_limit"

    @pytest.mark.asyncio
    async def test_handle_openai_error_authentication(self, mock_openai_client):
        """Test OpenAI authentication error handling."""
        mock_openai_client.chat.completions.create.side_effect = create_mock_openai_error(
            openai.AuthenticationError, "Invalid API key"
        )

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "authentication"

    @pytest.mark.asyncio
    async def test_handle_openai_error_network(self, mock_openai_client):
        """Test OpenAI network error handling."""
        mock_openai_client.chat.completions.create.side_effect = create_mock_openai_error(
            openai.APIConnectionError, "Connection failed"
        )

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "network"

    @pytest.mark.asyncio
    async def test_handle_openai_error_api_error(self, mock_openai_client):
        """Test OpenAI API error handling."""
        mock_openai_client.chat.completions.create.side_effect = create_mock_openai_error(
            openai.APIError, "API error occurred"
        )

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_handle_generic_error(self, mock_openai_client):
        """Test generic error handling."""
        mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected error")

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "unknown"

    @pytest.mark.asyncio
    async def test_stream_request_error(self, mock_openai_client):
        """Test streaming with error."""
        mock_openai_client.chat.completions.create.side_effect = create_mock_openai_error(
            openai.APIError, "Stream error"
        )

        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert len(result) == 1
        assert "[Error:" in result[0]

    @pytest.mark.asyncio
    async def test_convert_tool_calls_with_model_dump(self):
        """Test converting tool calls that have model_dump method."""
        client = OpenAIClient(self.provider)

        # Mock tool call with model_dump
        tool_call = MagicMock()
        tool_call.model_dump.return_value = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "test"},
        }

        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content=""),
                finish_reason="stop",
            )
        ]
        mock_response.choices[0].message.tool_calls = [tool_call]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        response = client._convert_response_from_openai(mock_response)
        assert response.tool_calls == [
            {"id": "call_1", "type": "function", "function": {"name": "test"}}
        ]

    @pytest.mark.asyncio
    async def test_convert_tool_calls_fallback(self):
        """Test converting tool calls with fallback method."""
        client = OpenAIClient(self.provider)

        # Create a proper mock tool call without model_dump or to_dict
        tool_call = Mock()
        tool_call.model_dump = None  # Explicitly set to None instead of deleting
        tool_call.to_dict = None
        tool_call.id = "call_1"
        tool_call.type = "function"

        # Create function mock
        func = Mock()
        func.name = "test_func"
        func.arguments = '{"arg": "value"}'
        tool_call.function = func

        mock_response = MagicMock(spec=ChatCompletion)
        mock_response.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content=""),
                finish_reason="stop",
            )
        ]
        mock_response.choices[0].message.tool_calls = [tool_call]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        response = client._convert_response_from_openai(mock_response)
        assert response.tool_calls[0]["id"] == "call_1"
        assert response.tool_calls[0]["function"]["name"] == "test_func"

    @pytest.mark.asyncio
    async def test_estimate_tokens(self):
        """Test token estimation."""
        client = OpenAIClient(self.provider)
        text = "This is a test message for token estimation"
        result = await client.estimate_tokens(text)
        assert result == max(1, len(text) // 4)

    @pytest.mark.asyncio
    async def test_close(self, mock_openai_client):
        """Test closing client."""
        client = OpenAIClient(self.provider)
        client.openai_client.close = AsyncMock()

        await client.close()

        client.openai_client.close.assert_called_once()


class TestOpenAIClientIntegration:
    """Integration tests for OpenAIClient (requires real API key)."""

    def setup_method(self):
        """Set up test fixtures."""
        if not has_openai_key():
            pytest.skip("OPENAI_API_KEY not set")

        self.provider = AIProvider(
            name="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            endpoint="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100,
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_send_request(self):
        """Integration test: send a real request to OpenAI."""
        client = OpenAIClient(self.provider)
        messages = [
            ApiMessage(
                role=MessageRole.USER, content="Say 'Hello, OpenAI!' in exactly those words."
            )
        ]

        response = await client.send_request(messages)

        assert response.content
        assert "Hello, OpenAI!" in response.content
        assert response.usage.total_tokens > 0
        assert response.finish_reason == "stop"

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_stream_request(self):
        """Integration test: stream a real response from OpenAI."""
        client = OpenAIClient(self.provider)
        messages = [ApiMessage(role=MessageRole.USER, content="Count from 1 to 5 slowly.")]

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
        """Integration test: validate connection to OpenAI."""
        client = OpenAIClient(self.provider)
        result = await client.validate_connection()
        assert result is True

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_list_models(self):
        """Integration test: list available models from OpenAI."""
        client = OpenAIClient(self.provider)
        models = await client.list_models()

        assert len(models) > 0
        assert any("gpt" in model for model in models)

        await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_with_system_message(self):
        """Integration test: send request with system message."""
        client = OpenAIClient(self.provider)
        messages = [
            ApiMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant. Always end with '😊'.",
            ),
            ApiMessage(role=MessageRole.USER, content="Say hello."),
        ]

        response = await client.send_request(messages)

        assert response.content
        assert "😊" in response.content

        await client.close()
