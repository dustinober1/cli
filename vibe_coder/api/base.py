"""Base API client for all AI providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from vibe_coder.types.api import ApiMessage, ApiResponse, TokenUsage
from vibe_coder.types.config import AIProvider


class BaseApiClient(ABC):
    """Abstract base class for AI provider clients."""

    def __init__(self, provider: AIProvider):
        """Initialize the API client with provider configuration.

        Args:
            provider: The AI provider configuration
        """
        self.provider = provider
        self.client = httpx.AsyncClient(
            base_url=provider.endpoint,
            headers=self._get_headers(),
            timeout=60.0,
            follow_redirects=True,
        )

    @abstractmethod
    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ApiResponse:
        """Send a request to the AI provider.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            tools: List of tools to provide to the model
            **kwargs: Additional provider-specific parameters

        Returns:
            ApiResponse with content and usage information
        """
        pass

    @abstractmethod
    async def stream_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from the AI provider.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional provider-specific parameters

        Yields:
            Response content chunks as they arrive
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the connection to the AI provider works.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text. Default implementation.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count (roughly 4 chars per token)
        """
        # Rough estimation: ~4 characters per token
        return max(1, len(text) // 4)

    def _get_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for requests.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {"Content-Type": "application/json", "User-Agent": "vibe-coder/0.1.0"}

        # Add custom headers from provider config
        if self.provider.headers:
            headers.update(self.provider.headers)

        return headers

    def _format_error_response(self, error: Exception, error_type: str = "unknown") -> ApiResponse:
        """Format an error as an ApiResponse.

        Args:
            error: The exception that occurred
            error_type: Type of error for categorization

        Returns:
            ApiResponse with error information
        """
        error_message = str(error)

        # Don't expose sensitive information in error messages
        if "api key" in error_message.lower():
            error_message = "Invalid API key or authentication failed"
        elif "rate limit" in error_message.lower():
            error_message = "Rate limit exceeded. Please try again later."
        elif "connection" in error_message.lower():
            error_message = "Connection failed. Please check your network and endpoint."

        return ApiResponse(
            content=f"Error: {error_message}",
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            finish_reason="error",
            error={"type": error_type, "message": error_message, "original": str(error)},
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _convert_messages_to_dict(self, messages: List[ApiMessage]) -> List[Dict[str, Any]]:
        """Convert ApiMessage objects to dictionary format.

        Args:
            messages: List of ApiMessage objects

        Returns:
            List of message dictionaries
        """
        return [message.to_dict() for message in messages]

    def _validate_messages(self, messages: List[ApiMessage]) -> None:
        """Validate that messages are properly formatted.

        Args:
            messages: List of messages to validate

        Raises:
            ValueError: If messages are invalid
        """
        if not messages:
            raise ValueError("At least one message is required")

        for i, message in enumerate(messages):
            if not isinstance(message, ApiMessage):
                raise ValueError(f"Message {i} is not a valid ApiMessage")
            # Relax validation for tool messages or messages with tool calls
            if (
                not message.content.strip()
                and not message.tool_calls
                and message.role.value != "tool"
            ):
                # Allow empty content if there are tool calls or if it is a tool response (though usually tool response has content)
                raise ValueError(f"Message {i} has empty content")

    def _prepare_request_params(
        self,
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs,
    ) -> Dict[str, Any]:
        """Prepare common request parameters.

        Args:
            model: Model override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional parameters

        Returns:
            Dictionary of prepared parameters
        """
        params = {
            "model": model or self.provider.model,
            "temperature": temperature if temperature is not None else self.provider.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.provider.max_tokens,
        }

        # Add any additional parameters
        params.update(kwargs)

        # Remove None values
        return {k: v for k, v in params.items() if v is not None}
