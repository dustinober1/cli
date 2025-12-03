"""OpenAI API client implementation."""

from typing import AsyncIterator, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from openai.types import chat

from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


class OpenAIClient(BaseApiClient):
    """OpenAI API client using official OpenAI SDK."""

    def __init__(self, provider: AIProvider):
        """Initialize OpenAI client.

        Args:
            provider: AI provider configuration
        """
        super().__init__(provider)
        self.openai_client = AsyncOpenAI(
            api_key=provider.api_key, base_url=provider.endpoint, timeout=60.0, max_retries=3
        )

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ApiResponse:
        """Send a request to OpenAI API.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            ApiResponse with content and usage information
        """
        try:
            self._validate_messages(messages)

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages_to_openai(messages)

            # Prepare request parameters
            params = self._prepare_request_params(model, temperature, max_tokens, **kwargs)

            response = await self.openai_client.chat.completions.create(
                messages=openai_messages, **params
            )

            return self._convert_response_from_openai(response)

        except openai.APIError as e:
            return self._handle_openai_error(e)
        except openai.RateLimitError as e:
            return self._format_error_response(e, "rate_limit")
        except openai.AuthenticationError as e:
            return self._format_error_response(e, "authentication")
        except openai.NetworkError as e:
            return self._format_error_response(e, "network")
        except Exception as e:
            return self._format_error_response(e, "unknown")

    async def stream_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from OpenAI API.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional OpenAI-specific parameters

        Yields:
            Response content chunks as they arrive
        """
        try:
            self._validate_messages(messages)

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages_to_openai(messages)

            # Prepare request parameters
            params = self._prepare_request_params(model, temperature, max_tokens, **kwargs)
            params["stream"] = True

            stream = await self.openai_client.chat.completions.create(
                messages=openai_messages, **params
            )

            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        except openai.APIError as e:
            yield f"\n[Error: {str(e)}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def validate_connection(self) -> bool:
        """Validate that the OpenAI connection works.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list models as a connection test
            await self.openai_client.models.list()
            return True
        except openai.AuthenticationError:
            # API key is invalid
            return False
        except openai.NetworkError:
            # Network or endpoint issue
            return False
        except Exception:
            # Any other error
            return False

    async def list_models(self) -> List[str]:
        """List available models from OpenAI.

        Returns:
            List of model names
        """
        try:
            models = await self.openai_client.models.list()
            return [model.id for model in models.data if model.id.startswith("gpt")]
        except Exception:
            return []

    def _convert_messages_to_openai(self, messages: List[ApiMessage]) -> List[Dict[str, str]]:
        """Convert ApiMessage objects to OpenAI format.

        Args:
            messages: List of ApiMessage objects

        Returns:
            List of OpenAI message dictionaries
        """
        openai_messages = []
        system_message = None

        # Find system message (OpenAI expects it at the beginning)
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                system_message = {"role": "system", "content": message.content}
                break

        # Add system message first if exists
        if system_message:
            openai_messages.append(system_message)

        # Add other messages
        for message in messages:
            if message.role != MessageRole.SYSTEM:
                openai_messages.append({"role": message.role.value, "content": message.content})

        # Ensure we have at least one message
        if not openai_messages:
            raise ValueError("No valid messages to send")

        return openai_messages

    def _convert_response_from_openai(self, response: chat.ChatCompletion) -> ApiResponse:
        """Convert OpenAI response to ApiResponse.

        Args:
            response: OpenAI chat completion response

        Returns:
            ApiResponse object
        """
        choice = response.choices[0]
        content = choice.message.content or ""

        # Extract usage information
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        return ApiResponse(
            content=content, usage=usage, finish_reason=choice.finish_reason or "unknown"
        )

    def _handle_openai_error(self, error: openai.APIError) -> ApiResponse:
        """Handle OpenAI-specific errors.

        Args:
            error: OpenAI API error

        Returns:
            ApiResponse with error information
        """
        error_type = "openai_error"

        # Categorize error types
        if "rate" in str(error).lower():
            error_type = "rate_limit"
        elif "token" in str(error).lower():
            error_type = "token_limit"
        elif "model" in str(error).lower():
            error_type = "model_not_found"

        return self._format_error_response(error, error_type)

    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count using OpenAI's tokenizer if available.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        # For OpenAI, we can use tiktoken if available
        # For now, fall back to the base implementation
        return await super().estimate_tokens(text)

    async def close(self):
        """Close both the base client and OpenAI client."""
        await super().close()
        await self.openai_client.close()
