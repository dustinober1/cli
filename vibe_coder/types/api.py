"""
Type definitions for AI API interactions.

This module defines the data structures for API requests, responses,
and messages that flow between the CLI and AI providers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class MessageRole(Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    """System instruction message that guides AI behavior"""

    USER = "user"
    """User message (input from the human)"""

    ASSISTANT = "assistant"
    """Assistant response from the AI"""


@dataclass
class ApiMessage:
    """
    A single message in a conversation.

    Attributes:
        role: Who sent this message (system, user, or assistant)
        content: The text content of the message

    Examples:
        >>> msg = ApiMessage(role=MessageRole.USER, content="Hello!")
        >>> msg.role
        <MessageRole.USER: 'user'>
    """

    role: MessageRole
    """Role: system, user, or assistant"""

    content: str
    """Message text content"""

    def to_dict(self) -> dict:
        """Convert message to dictionary for API requests."""
        return {
            "role": self.role.value,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApiMessage":
        """Create message from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
        )


@dataclass
class TokenUsage:
    """
    Token usage statistics from an API response.

    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used

    Examples:
        >>> usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        >>> usage.total_tokens
        15
    """

    prompt_tokens: int
    """Tokens in the prompt (input)"""

    completion_tokens: int
    """Tokens in the completion (output)"""

    total_tokens: int
    """Total tokens used"""

    def to_dict(self) -> dict:
        """Convert usage to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class ApiRequest:
    """
    Request to send to an AI API.

    This represents a request to be sent to the AI provider.
    It gets converted to the provider-specific format by the API client.

    Attributes:
        messages: List of messages in the conversation
        model: Model to use (optional, uses provider default if not specified)
        temperature: Response temperature (optional)
        max_tokens: Maximum response length (optional)
        stream: If True, stream the response

    Examples:
        >>> request = ApiRequest(
        ...     messages=[ApiMessage(role=MessageRole.USER, content="Hello")],
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
    """

    messages: List[ApiMessage]
    """Messages in the conversation"""

    model: Optional[str] = None
    """Model to use (optional)"""

    temperature: Optional[float] = None
    """Temperature setting (optional)"""

    max_tokens: Optional[int] = None
    """Max tokens in response (optional)"""

    stream: bool = False
    """Whether to stream the response"""


@dataclass
class ApiResponse:
    """
    Response from an AI API.

    This represents the structured response from an AI provider.
    API clients convert provider-specific responses to this format.

    Attributes:
        content: The text content of the response
        model: The model that generated this response
        usage: Token usage statistics (optional)
        finish_reason: Why the response ended (e.g., 'stop', 'length')

    Examples:
        >>> response = ApiResponse(
        ...     content="Hello! How can I help?",
        ...     model="gpt-4",
        ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ...     finish_reason="stop"
        ... )
    """

    content: str
    """The actual response text"""

    model: Optional[str] = None
    """Model that generated the response"""

    usage: Optional[TokenUsage] = None
    """Token usage statistics"""

    finish_reason: Optional[str] = None
    """Why the response stopped (e.g., 'stop', 'length')"""

    error: Optional[Dict[str, str]] = None
    """Error information if the request failed"""

    def to_dict(self) -> dict:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage.to_dict() if self.usage else None,
            "finish_reason": self.finish_reason,
        }
