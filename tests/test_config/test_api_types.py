"""Tests for API type definitions (dataclasses)."""
import pytest

from vibe_coder.types.api import ApiMessage, ApiRequest, ApiResponse, MessageRole, TokenUsage


class TestMessageRole:
    """Test suite for MessageRole enum."""

    def test_message_role_values(self):
        """Test that MessageRole enum has correct values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_message_role_by_value(self):
        """Test that MessageRole can be looked up by value."""
        system = MessageRole("system")
        assert system == MessageRole.SYSTEM

        user = MessageRole("user")
        assert user == MessageRole.USER

        assistant = MessageRole("assistant")
        assert assistant == MessageRole.ASSISTANT


class TestApiMessage:
    """Test suite for ApiMessage dataclass."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = ApiMessage(role=MessageRole.USER, content="Hello, AI!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, AI!"

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = ApiMessage(role=MessageRole.ASSISTANT, content="Hello, human!")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hello, human!"

    def test_create_system_message(self):
        """Test creating a system message."""
        msg = ApiMessage(
            role=MessageRole.SYSTEM, content="You are a helpful assistant."
        )
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant."

    def test_message_to_dict(self):
        """Test ApiMessage.to_dict() serialization."""
        msg = ApiMessage(role=MessageRole.USER, content="Test content")
        result = msg.to_dict()
        assert result == {"role": "user", "content": "Test content"}

    def test_message_from_dict(self):
        """Test ApiMessage.from_dict() deserialization."""
        data = {"role": "assistant", "content": "Response text"}
        msg = ApiMessage.from_dict(data)
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Response text"

    def test_message_round_trip(self):
        """Test that message survives to_dict -> from_dict round trip."""
        original = ApiMessage(role=MessageRole.USER, content="Original content")
        restored = ApiMessage.from_dict(original.to_dict())
        assert restored.role == original.role
        assert restored.content == original.content

    def test_message_with_empty_content(self):
        """Test creating a message with empty content."""
        msg = ApiMessage(role=MessageRole.USER, content="")
        assert msg.content == ""

    def test_message_with_multiline_content(self):
        """Test creating a message with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        msg = ApiMessage(role=MessageRole.USER, content=content)
        assert msg.content == content

    def test_message_with_special_characters(self):
        """Test creating a message with special characters."""
        content = "Hello! @#$%^&*() <tags> 'quotes' \"double\""
        msg = ApiMessage(role=MessageRole.USER, content=content)
        assert msg.content == content


class TestTokenUsage:
    """Test suite for TokenUsage dataclass."""

    def test_create_token_usage(self):
        """Test creating TokenUsage with valid values."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_token_usage_to_dict(self):
        """Test TokenUsage.to_dict() serialization."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        result = usage.to_dict()
        assert result == {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }

    def test_token_usage_with_zero_values(self):
        """Test TokenUsage with zero token counts."""
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        assert usage.prompt_tokens == 0
        assert usage.total_tokens == 0

    def test_token_usage_with_large_values(self):
        """Test TokenUsage with large token counts."""
        usage = TokenUsage(
            prompt_tokens=100000, completion_tokens=50000, total_tokens=150000
        )
        assert usage.prompt_tokens == 100000
        assert usage.total_tokens == 150000


class TestApiRequest:
    """Test suite for ApiRequest dataclass."""

    def test_create_basic_request(self):
        """Test creating a basic API request."""
        messages = [ApiMessage(role=MessageRole.USER, content="Hello")]
        request = ApiRequest(messages=messages)
        assert request.messages == messages
        assert request.model is None
        assert request.temperature is None
        assert request.max_tokens is None
        assert request.stream is False

    def test_create_request_with_all_parameters(self):
        """Test creating a request with all parameters."""
        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="Be helpful"),
            ApiMessage(role=MessageRole.USER, content="Hello"),
        ]
        request = ApiRequest(
            messages=messages,
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            stream=True,
        )
        assert len(request.messages) == 2
        assert request.model == "gpt-4"
        assert request.temperature == 0.7
        assert request.max_tokens == 2000
        assert request.stream is True

    def test_request_with_multiple_messages(self):
        """Test request with conversation history."""
        messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
            ApiMessage(role=MessageRole.USER, content="How are you?"),
        ]
        request = ApiRequest(messages=messages)
        assert len(request.messages) == 3

    def test_request_with_empty_messages(self):
        """Test that request allows empty message list."""
        request = ApiRequest(messages=[])
        assert request.messages == []

    def test_request_stream_default_false(self):
        """Test that stream defaults to False."""
        request = ApiRequest(messages=[])
        assert request.stream is False

    def test_request_with_streaming_enabled(self):
        """Test request with streaming enabled."""
        request = ApiRequest(messages=[], stream=True)
        assert request.stream is True


class TestApiResponse:
    """Test suite for ApiResponse dataclass."""

    def test_create_basic_response(self):
        """Test creating a basic API response."""
        response = ApiResponse(content="Hello, human!")
        assert response.content == "Hello, human!"
        assert response.model is None
        assert response.usage is None
        assert response.finish_reason is None

    def test_create_response_with_all_fields(self):
        """Test creating a response with all fields."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        response = ApiResponse(
            content="Response text",
            model="gpt-4",
            usage=usage,
            finish_reason="stop",
        )
        assert response.content == "Response text"
        assert response.model == "gpt-4"
        assert response.usage == usage
        assert response.finish_reason == "stop"

    def test_response_with_different_finish_reasons(self):
        """Test response with different finish reasons."""
        response_stop = ApiResponse(content="Text", finish_reason="stop")
        assert response_stop.finish_reason == "stop"

        response_length = ApiResponse(content="Text", finish_reason="length")
        assert response_length.finish_reason == "length"

        response_max_tokens = ApiResponse(content="Text", finish_reason="max_tokens")
        assert response_max_tokens.finish_reason == "max_tokens"

    def test_response_to_dict(self):
        """Test ApiResponse.to_dict() serialization."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        response = ApiResponse(
            content="Test response",
            model="gpt-4",
            usage=usage,
            finish_reason="stop",
        )
        result = response.to_dict()
        assert result["content"] == "Test response"
        assert result["model"] == "gpt-4"
        assert result["usage"]["total_tokens"] == 15
        assert result["finish_reason"] == "stop"

    def test_response_to_dict_with_none_usage(self):
        """Test response serialization when usage is None."""
        response = ApiResponse(content="Text", usage=None)
        result = response.to_dict()
        assert result["usage"] is None

    def test_response_with_multiline_content(self):
        """Test response with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        response = ApiResponse(content=content)
        assert response.content == content

    def test_response_with_empty_content(self):
        """Test response with empty content."""
        response = ApiResponse(content="")
        assert response.content == ""

    def test_response_with_special_characters(self):
        """Test response with special characters in content."""
        content = "Special chars: !@#$%^&*() <html> 'quote' \"double\""
        response = ApiResponse(content=content)
        assert response.content == content


class TestIntegration:
    """Integration tests for API types working together."""

    def test_request_response_workflow(self):
        """Test a complete request-response workflow."""
        # Build request
        messages = [
            ApiMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ApiMessage(role=MessageRole.USER, content="What is 2+2?"),
        ]
        request = ApiRequest(
            messages=messages, model="gpt-4", temperature=0.0, stream=False
        )

        # Simulate response
        usage = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        response = ApiResponse(
            content="2+2 equals 4", model="gpt-4", usage=usage, finish_reason="stop"
        )

        # Verify they work together
        assert len(request.messages) == 2
        assert request.model == response.model
        assert response.usage.total_tokens == 30

    def test_conversation_history(self):
        """Test building and maintaining conversation history."""
        conversation = []

        # First turn
        user_msg1 = ApiMessage(role=MessageRole.USER, content="Hello")
        assistant_msg1 = ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        conversation.extend([user_msg1, assistant_msg1])

        # Second turn
        user_msg2 = ApiMessage(role=MessageRole.USER, content="How are you?")
        assistant_msg2 = ApiMessage(role=MessageRole.ASSISTANT, content="Great!")
        conversation.extend([user_msg2, assistant_msg2])

        # Create request with full history
        request = ApiRequest(messages=conversation)
        assert len(request.messages) == 4
        assert request.messages[0].content == "Hello"
        assert request.messages[-1].content == "Great!"

    def test_serialization_workflow(self):
        """Test serializing and deserializing API objects."""
        # Create request
        messages = [
            ApiMessage(role=MessageRole.USER, content="Test"),
        ]
        original_request = ApiRequest(
            messages=messages, model="gpt-4", temperature=0.8
        )

        # Create response
        original_response = ApiResponse(
            content="Response",
            model="gpt-4",
            usage=TokenUsage(10, 5, 15),
            finish_reason="stop",
        )

        # Serialize (would be sent to API)
        request_for_api = {
            "messages": [msg.to_dict() for msg in original_request.messages],
            "model": original_request.model,
            "temperature": original_request.temperature,
        }

        # Deserialize response (would come from API)
        response_from_api = ApiResponse(
            content=original_response.content,
            model=original_response.model,
            usage=TokenUsage(
                original_response.usage.prompt_tokens,
                original_response.usage.completion_tokens,
                original_response.usage.total_tokens,
            ),
            finish_reason=original_response.finish_reason,
        )

        # Verify data integrity
        assert response_from_api.content == original_response.content
        assert response_from_api.model == original_response.model
