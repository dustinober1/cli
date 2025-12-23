"""Generic OpenAI-compatible API client implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


class GenericClient(BaseApiClient):
    """Generic client for OpenAI-compatible endpoints (Ollama, LM Studio, etc.)."""

    def __init__(self, provider: AIProvider):
        """Initialize Generic client.

        Args:
            provider: AI provider configuration
        """
        super().__init__(provider)
        self._models_cache: Optional[List[str]] = None
        self._models_cache_time: float = 0

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ApiResponse:
        """Send a request to a generic OpenAI-compatible endpoint.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional provider-specific parameters

        Returns:
            ApiResponse with content and usage information
        """
        try:
            self._validate_messages(messages)

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages_to_dict(messages)

            # Prepare request payload
            payload = self._build_payload(
                openai_messages, model, temperature, max_tokens, stream=False, **kwargs
            )

            # Try different endpoints
            response_data = await self._try_request_endpoints("chat/completions", payload)

            return self._convert_response_from_generic(response_data)

        except Exception as e:
            return self._format_error_response(e, "generic_error")

    async def stream_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from a generic OpenAI-compatible endpoint.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional provider-specific parameters

        Yields:
            Response content chunks as they arrive
        """
        try:
            self._validate_messages(messages)

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages_to_dict(messages)

            # Prepare request payload
            payload = self._build_payload(
                openai_messages, model, temperature, max_tokens, stream=True, **kwargs
            )

            # Try streaming endpoints
            async for chunk in self._try_stream_endpoints("chat/completions", payload):
                yield chunk

        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def validate_connection(self) -> bool:
        """Validate that the generic endpoint connection works.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list models first
            models = await self.list_models()
            if len(models) > 0:
                return True
        except Exception:
            pass

        # If no models found or models endpoint doesn't work, try a simple chat request
        try:
            response = await self.send_request([ApiMessage(role=MessageRole.USER, content="test")])
            # Check if response is valid (not an error response)
            return response.finish_reason != "error" and not response.error
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models from the generic endpoint.

        Returns:
            List of model names
        """
        # Cache models for 5 minutes
        import time

        current_time = time.time()
        if self._models_cache and (current_time - self._models_cache_time) < 300:
            return self._models_cache

        try:
            # Try different model endpoints
            for endpoint in ["models", "v1/models"]:
                try:
                    response = await self.client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        models = self._extract_models_from_response(data)
                        if models:
                            self._models_cache = models
                            self._models_cache_time = current_time
                            return models
                except Exception:
                    continue

            # If no models endpoint, return empty list
            return []

        except Exception:
            return []

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool,
        **kwargs,
    ) -> Dict[str, Any]:
        """Build request payload for generic endpoint.

        Args:
            messages: List of message dictionaries
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            stream: Whether to stream response
            **kwargs: Additional parameters

        Returns:
            Request payload dictionary
        """
        payload = {
            "model": model or self.provider.model or "default",
            "messages": messages,
            "stream": stream,
        }

        # Add temperature if specified
        if temperature is not None:
            payload["temperature"] = temperature
        elif self.provider.temperature is not None:
            payload["temperature"] = self.provider.temperature

        # Add max_tokens if specified
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        elif self.provider.max_tokens is not None:
            payload["max_tokens"] = self.provider.max_tokens

        # Add additional parameters
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        return payload

    async def _try_request_endpoints(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try different endpoint variations for the request.

        Args:
            endpoint: Base endpoint path
            payload: Request payload

        Returns:
            Response data

        Raises:
            Exception: If all endpoints fail
        """
        endpoints_to_try = [
            endpoint,
            f"/v1/{endpoint}",
            f"/api/{endpoint}",
        ]

        last_error = None
        for ep in endpoints_to_try:
            try:
                response = await self.client.post(ep, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_error = e
                continue

        raise last_error or Exception("All endpoints failed")

    async def _try_stream_endpoints(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Try different streaming endpoints.

        Args:
            endpoint: Base endpoint path
            payload: Request payload

        Yields:
            Response content chunks
        """
        endpoints_to_try = [
            endpoint,
            f"/v1/{endpoint}",
            f"/api/{endpoint}",
        ]

        for ep in endpoints_to_try:
            try:
                async with self.client.stream("POST", ep, json=payload) as response:
                    if response.status_code != 200:
                        continue

                    # Parse server-sent events
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data)
                                content = self._extract_content_from_chunk(chunk_data)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

                return  # Success, stop trying other endpoints

            except Exception:
                continue

        raise Exception("All streaming endpoints failed")

    def _extract_content_from_chunk(self, chunk: Dict[str, Any]) -> Optional[str]:
        """Extract content from a streaming response chunk.

        Args:
            chunk: Chunk data from response

        Returns:
            Content string or None if no content
        """
        try:
            # Standard OpenAI format
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {})
                return delta.get("content", "")
            # Some providers use different formats
            elif "content" in chunk:
                return chunk["content"]
            elif "text" in chunk:
                return chunk["text"]
        except Exception:
            pass
        return None

    def _extract_models_from_response(self, data: Dict[str, Any]) -> List[str]:
        """Extract model names from models endpoint response.

        Args:
            data: Response data from models endpoint

        Returns:
            List of model names
        """
        models = []
        try:
            # Standard OpenAI format
            if "data" in data:
                for model in data["data"]:
                    if isinstance(model, dict) and "id" in model:
                        models.append(model["id"])
            # Alternative formats
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item:
                        models.append(item["id"])
                    elif isinstance(item, str):
                        models.append(item)
        except Exception:
            pass
        return models

    def _convert_response_from_generic(self, response_data: Dict[str, Any]) -> ApiResponse:
        """Convert generic response to ApiResponse.

        Args:
            response_data: Raw response data from endpoint

        Returns:
            ApiResponse object
        """
        # Extract content
        content = ""
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            if "message" in choice:
                content = choice["message"].get("content", "")
            elif "text" in choice:
                content = choice["text"]
        elif "content" in response_data:
            content = response_data["content"]
        elif "text" in response_data:
            content = response_data["text"]

        # Extract usage information
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        if "usage" in response_data:
            usage_data = response_data["usage"]
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        # Extract finish reason
        finish_reason = "unknown"
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            finish_reason = choice.get("finish_reason", "unknown")

        return ApiResponse(content=content, usage=usage, finish_reason=finish_reason)
