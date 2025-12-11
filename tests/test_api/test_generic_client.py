"""Test Generic OpenAI-compatible API client implementation."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List

from vibe_coder.api.generic_client import GenericClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


class TestGenericClient:
    """Unit tests for GenericClient (all mocked)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AIProvider(
            name="generic",
            api_key="test-key-1234567890",
            endpoint="https://api.generic.com/v1",
            model="generic-model",
            temperature=0.7,
            max_tokens=1000,
        )

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        with patch('httpx.AsyncClient') as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def client(self, mock_httpx_client):
        """Create GenericClient with mocked dependencies."""
        return GenericClient(self.provider)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization."""
        with patch('httpx.AsyncClient') as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            client = GenericClient(self.provider)

            mock.assert_called_once()
            assert client.provider == self.provider
            assert client._models_cache is None
            assert client._models_cache_time == 0

    @pytest.mark.asyncio
    async def test_initialization_with_custom_headers(self):
        """Test initialization with custom headers."""
        provider = AIProvider(
            name="generic",
            api_key="test-key",
            endpoint="https://api.generic.com",
            headers={"X-Custom": "value"},
        )

        with patch('httpx.AsyncClient') as mock:
            GenericClient(provider)

            call_kwargs = mock.call_args[1]
            assert call_kwargs['headers']['X-Custom'] == "value"

    @pytest.mark.asyncio
    async def test_send_request_success(self, client):
        """Test successful request sending."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Test response"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        client.client.post.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.content == "Test response"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.finish_reason == "stop"

        client.client.post.assert_called_once()
        call_args = client.client.post.call_args
        assert "chat/completions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_request_with_v1_endpoint(self, client):
        """Test request tries different endpoint paths."""
        # First call fails, second succeeds
        from httpx import HTTPStatusError

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 404
        mock_response_fail.raise_for_status.side_effect = HTTPStatusError("404 Not Found", request=MagicMock(), response=mock_response_fail)

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }

        client.client.post.side_effect = [mock_response_fail, mock_response_success]

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        await client.send_request(messages)

        assert client.client.post.call_count == 2
        # Should try "chat/completions" then "/v1/chat/completions"
        assert client.client.post.call_args_list[0][0][0] == "chat/completions"
        assert client.client.post.call_args_list[1][0][0] == "/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_send_request_with_api_endpoint(self, client):
        """Test request tries /api/ endpoint path."""
        # First two calls fail, third succeeds
        from httpx import HTTPStatusError

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 404
        mock_response_fail.raise_for_status.side_effect = HTTPStatusError("404 Not Found", request=MagicMock(), response=mock_response_fail)

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }

        client.client.post.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        await client.send_request(messages)

        assert client.client.post.call_count == 3
        # Should try all three endpoint variations
        assert client.client.post.call_args_list[0][0][0] == "chat/completions"
        assert client.client.post.call_args_list[1][0][0] == "/v1/chat/completions"
        assert client.client.post.call_args_list[2][0][0] == "/api/chat/completions"

    @pytest.mark.asyncio
    async def test_send_request_with_overrides(self, client):
        """Test sending request with parameter overrides."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        client.client.post.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        await client.send_request(
            messages,
            model="custom-model",
            temperature=0.3,
            max_tokens=500,
            top_p=0.9
        )

        call_args = client.client.post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "custom-model"
        assert payload['temperature'] == 0.3
        assert payload['max_tokens'] == 500
        assert payload['top_p'] == 0.9

    @pytest.mark.asyncio
    async def test_send_request_alternative_response_format(self, client):
        """Test handling alternative response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Direct content field",
            "usage": {"prompt_tokens": 5, "completion_tokens": 15, "total_tokens": 20}
        }

        client.client.post.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.content == "Direct content field"
        assert response.usage.total_tokens == 20

    @pytest.mark.asyncio
    async def test_send_request_with_text_choice(self, client):
        """Test response with 'text' field in choice."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "text": "Text from choice",
                    "finish_reason": "stop"
                }
            ]
        }

        client.client.post.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.content == "Text from choice"

    @pytest.mark.asyncio
    async def test_send_request_no_usage(self, client):
        """Test response without usage information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        client.client.post.return_value = mock_response

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0
        assert response.usage.total_tokens == 0

    @pytest.mark.asyncio
    async def test_send_request_error(self, client):
        """Test request with error."""
        client.client.post.side_effect = Exception("Network error")

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        response = await client.send_request(messages)

        assert "Error:" in response.content
        assert response.finish_reason == "error"
        assert response.error["type"] == "generic_error"

    @pytest.mark.asyncio
    async def test_stream_request_success(self, client):
        """Test successful streaming request."""
        # Create a proper mock for the streaming response
        class MockAsyncContextManager:
            def __init__(self, lines):
                self.lines = lines
                self.response = MagicMock()
                self.response.status_code = 200

            async def __aenter__(self):
                return self.response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

            async def mock_aiter_lines(self):
                for line in self.lines:
                    yield line

        # Set up the mock
        mock_context = MockAsyncContextManager([
            "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"!\"}]}",
            "data: [DONE]"
        ])
        mock_context.response.aiter_lines = mock_context.mock_aiter_lines
        client.client.stream.return_value = mock_context

        messages = [ApiMessage(role=MessageRole.USER, content="Stream test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == ["Hello", " world", "!"]
        client.client.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_request_with_v1_endpoint(self, client):
        """Test streaming tries different endpoint paths."""
        mock_stream_response = MagicMock()
        mock_stream_response.status_code = 200
        mock_lines = AsyncMock()
        mock_lines.__aiter__ = AsyncMock(return_value=iter([]))
        mock_stream_response.aiter_lines.return_value = mock_lines

        # First stream call fails, second succeeds
        mock_context_manager1 = MagicMock()
        mock_context_manager1.__aenter__.side_effect = Exception("404 Not Found")

        mock_context_manager2 = AsyncMock()
        mock_context_manager2.__aenter__.return_value = mock_stream_response
        mock_context_manager2.__aexit__ = AsyncMock(return_value=None)

        client.client.stream.side_effect = [mock_context_manager1, mock_context_manager2]

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert client.client.stream.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_request_extract_content_variants(self, client):
        """Test extracting content from different chunk formats."""
        async def mock_aiter_lines():
            lines = [
                "data: {\"choices\":[{\"delta\":{\"content\":\"Standard\"}]}",
                "data: {\"content\":\"Direct field\"}",
                "data: {\"text\":\"Text field\"}",
                "data: [DONE]"
            ]
            for line in lines:
                yield line

        mock_stream_response = MagicMock()
        mock_stream_response.status_code = 200
        mock_stream_response.aiter_lines = mock_aiter_lines

        # Mock the async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_stream_response
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        client.client.stream.return_value = mock_context_manager

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == ["Standard", "Direct field", "Text field"]

    @pytest.mark.asyncio
    async def test_stream_request_malformed_json(self, client):
        """Test streaming with malformed JSON."""
        async def mock_aiter_lines():
            lines = [
                "data: {\"choices\":[{\"delta\":{\"content\":\"Valid\"}]}",
                "data: invalid json",
                "data: {\"choices\":[{\"delta\":{\"content\":\"Still valid\"}]}",
                "data: [DONE]"
            ]
            for line in lines:
                yield line

        mock_stream_response = MagicMock()
        mock_stream_response.status_code = 200
        mock_stream_response.aiter_lines = mock_aiter_lines

        # Mock the async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_stream_response
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        client.client.stream.return_value = mock_context_manager

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert result == ["Valid", "Still valid"]  # Skips invalid JSON

    @pytest.mark.asyncio
    async def test_stream_request_error(self, client):
        """Test streaming with error."""
        client.client.stream.side_effect = Exception("Stream error")

        messages = [ApiMessage(role=MessageRole.USER, content="Test")]
        result = []
        async for chunk in client.stream_request(messages):
            result.append(chunk)

        assert len(result) == 1
        assert "[Error:" in result[0]

    @pytest.mark.asyncio
    async def test_validate_connection_with_models(self, client):
        """Test connection validation via models endpoint."""
        # Mock successful models response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "model1"},
                {"id": "model2"}
            ]
        }
        client.client.get.return_value = mock_response

        result = await client.validate_connection()
        assert result is True
        client.client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_connection_fallback_to_request(self, client):
        """Test connection validation fallback to request."""
        # Models endpoint fails
        client.client.get.side_effect = Exception("Models endpoint not found")

        # Mock successful request through _try_request_endpoints
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OK"}}]
        }
        # Mock raise_for_status to not raise an exception
        mock_response.raise_for_status.return_value = None

        # Mock the successful POST request
        client.client.post.return_value = mock_response

        result = await client.validate_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, client):
        """Test connection validation failure."""
        client.client.get.side_effect = Exception("Models failed")
        client.client.post.side_effect = Exception("Request failed")

        result = await client.validate_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models_success(self, client):
        """Test successful model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-model"},
                {"id": "llama-model"},
                {"id": "custom-model"}
            ]
        }
        client.client.get.return_value = mock_response

        models = await client.list_models()
        assert len(models) == 3
        assert "gpt-model" in models
        assert "llama-model" in models
        assert "custom-model" in models

    @pytest.mark.asyncio
    async def test_list_models_with_v1_endpoint(self, client):
        """Test models listing with different endpoints."""
        # First endpoint fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 404

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "data": [{"id": "model1"}]
        }

        client.client.get.side_effect = [mock_response_fail, mock_response_success]

        models = await client.list_models()
        assert len(models) == 1
        assert models[0] == "model1"

        assert client.client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_list_models_alternative_format(self, client):
        """Test models listing with alternative response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "model1"},
            {"id": "model2"},
            "model3"  # String instead of dict
        ]
        client.client.get.return_value = mock_response

        models = await client.list_models()
        assert len(models) == 3
        assert "model1" in models
        assert "model2" in models
        assert "model3" in models

    @pytest.mark.asyncio
    async def test_list_models_caching(self, client):
        """Test models caching."""
        import time

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "cached-model"}]
        }
        client.client.get.return_value = mock_response

        # First call
        models1 = await client.list_models()
        time1 = client._models_cache_time

        # Second call immediately (should use cache)
        models2 = await client.list_models()
        time2 = client._models_cache_time

        assert models1 == models2
        assert time1 == time2
        assert client.client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_list_models_cache_expires(self, client):
        """Test models cache expires after 5 minutes."""
        import time

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "model"}]
        }
        client.client.get.return_value = mock_response

        # First call
        await client.list_models()

        # Simulate time passing (6 minutes)
        client._models_cache_time = time.time() - 360

        # Second call (cache expired)
        await client.list_models()

        assert client.client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_list_models_no_endpoint(self, client):
        """Test models listing when no endpoint works."""
        client.client.get.side_effect = Exception("No models endpoint")

        models = await client.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_build_payload_defaults(self, client):
        """Test building payload with provider defaults."""
        messages = [{"role": "user", "content": "Test"}]
        payload = client._build_payload(
            messages,
            model=None,
            temperature=None,
            max_tokens=None,
            stream=False
        )

        assert payload["model"] == self.provider.model
        assert payload["temperature"] == self.provider.temperature
        assert payload["max_tokens"] == self.provider.max_tokens
        assert payload["stream"] is False
        assert payload["messages"] == messages

    @pytest.mark.asyncio
    async def test_build_payload_with_overrides(self, client):
        """Test building payload with parameter overrides."""
        messages = [{"role": "user", "content": "Test"}]
        payload = client._build_payload(
            messages,
            model="override-model",
            temperature=0.1,
            max_tokens=2000,
            stream=True,
            custom_param="value",
            none_param=None
        )

        assert payload["model"] == "override-model"
        assert payload["temperature"] == 0.1
        assert payload["max_tokens"] == 2000
        assert payload["stream"] is True
        assert payload["custom_param"] == "value"
        assert "none_param" not in payload

    @pytest.mark.asyncio
    async def test_build_payload_no_provider_model(self, client):
        """Test building payload when provider has no model."""
        provider = AIProvider(
            name="generic",
            api_key="test-key",
            endpoint="https://api.test.com",
            model=None,  # No model
        )
        client = GenericClient(provider)

        messages = [{"role": "user", "content": "Test"}]
        payload = client._build_payload(messages, None, None, None, False)

        assert payload["model"] == "default"

    @pytest.mark.asyncio
    async def test_extract_models_from_response_standard(self, client):
        """Test extracting models from standard OpenAI format."""
        data = {
            "data": [
                {"id": "model1"},
                {"id": "model2"}
            ]
        }

        models = client._extract_models_from_response(data)
        assert models == ["model1", "model2"]

    @pytest.mark.asyncio
    async def test_extract_models_from_response_list(self, client):
        """Test extracting models from list response."""
        data = [
            {"id": "model1"},
            {"id": "model2"},
            "model3"  # String
        ]

        models = client._extract_models_from_response(data)
        assert models == ["model1", "model2", "model3"]

    @pytest.mark.asyncio
    async def test_extract_models_from_response_malformed(self, client):
        """Test extracting models from malformed response."""
        data = {
            "invalid": "format"
        }

        models = client._extract_models_from_response(data)
        assert models == []

    @pytest.mark.asyncio
    async def test_extract_content_from_chunk_standard(self, client):
        """Test extracting content from standard chunk format."""
        chunk = {
            "choices": [
                {
                    "delta": {
                        "content": "Hello world"
                    }
                }
            ]
        }

        content = client._extract_content_from_chunk(chunk)
        assert content == "Hello world"

    @pytest.mark.asyncio
    async def test_extract_content_from_chunk_direct(self, client):
        """Test extracting content from direct content field."""
        chunk = {
            "content": "Direct content"
        }

        content = client._extract_content_from_chunk(chunk)
        assert content == "Direct content"

    @pytest.mark.asyncio
    async def test_extract_content_from_chunk_text(self, client):
        """Test extracting content from text field."""
        chunk = {
            "text": "Text content"
        }

        content = client._extract_content_from_chunk(chunk)
        assert content == "Text content"

    @pytest.mark.asyncio
    async def test_extract_content_from_chunk_no_content(self, client):
        """Test extracting content when no content exists."""
        chunk = {
            "other": "field"
        }

        content = client._extract_content_from_chunk(chunk)
        assert content is None