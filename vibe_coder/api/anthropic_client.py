"""Anthropic Claude API client implementation."""

from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import Message

from vibe_coder.api.base import BaseApiClient
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage
from vibe_coder.types.config import AIProvider


class AnthropicClient(BaseApiClient):
    """Anthropic Claude API client using official Anthropic SDK."""

    def __init__(self, provider: AIProvider):
        """Initialize Anthropic client.

        Args:
            provider: AI provider configuration
        """
        super().__init__(provider)
        self.anthropic_client = AsyncAnthropic(
            api_key=provider.api_key, base_url=provider.endpoint, timeout=60.0, max_retries=3
        )

    async def send_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ApiResponse:
        """Send a request to Anthropic API.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            tools: List of tools to provide to the model
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            ApiResponse with content and usage information
        """
        try:
            self._validate_messages(messages)

            # Convert messages to Anthropic format
            system_message, claude_messages = self._convert_messages_to_anthropic(messages)

            # Prepare request parameters
            params = self._prepare_request_params(model, temperature, max_tokens, **kwargs)

            # Anthropic requires max_tokens
            if params.get("max_tokens") is None:
                params["max_tokens"] = 4096

            if tools:
                params["tools"] = tools

            response = await self.anthropic_client.messages.create(
                messages=claude_messages, system=system_message, **params
            )

            return self._convert_response_from_anthropic(response)

        except anthropic.APIError as e:
            return self._handle_anthropic_error(e)
        except anthropic.RateLimitError as e:
            return self._format_error_response(e, "rate_limit")
        except anthropic.AuthenticationError as e:
            return self._format_error_response(e, "authentication")
        except anthropic.NetworkError as e:
            return self._format_error_response(e, "network")
        except Exception as e:
            return self._format_error_response(e, "unknown")

    async def stream_request(
        self,
        messages: List[ApiMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from Anthropic API.

        Args:
            messages: List of conversation messages
            model: Model name override
            temperature: Temperature override
            max_tokens: Max tokens override
            tools: List of tools to provide to the model
            **kwargs: Additional Anthropic-specific parameters

        Yields:
            Response content chunks as they arrive
        """
        try:
            self._validate_messages(messages)

            # Convert messages to Anthropic format
            system_message, claude_messages = self._convert_messages_to_anthropic(messages)

            # Prepare request parameters
            params = self._prepare_request_params(model, temperature, max_tokens, **kwargs)

            # Anthropic requires max_tokens
            if params.get("max_tokens") is None:
                params["max_tokens"] = 4096

            if tools:
                params["tools"] = tools

            async with self.anthropic_client.messages.stream(
                messages=claude_messages, system=system_message, **params
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.APIError as e:
            yield f"\n[Error: {str(e)}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def validate_connection(self) -> bool:
        """Validate that the Anthropic connection works.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try a simple message as a connection test
            await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except anthropic.NetworkError:
            return False
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available Claude models.

        Returns:
            List of model names
        """
        # Anthropic doesn't have a models endpoint, so return known models
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def _convert_messages_to_anthropic(
        self, messages: List[ApiMessage]
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert ApiMessage objects to Anthropic format.

        Args:
            messages: List of ApiMessage objects

        Returns:
            Tuple of (system_message, conversation_messages)
        """
        system_message = None
        claude_messages = []

        # Find system message (Anthropic handles this separately)
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                system_message = message.content
                break

        # Convert conversation messages
        for message in messages:
            if message.role == MessageRole.USER:
                claude_messages.append({"role": "user", "content": message.content})
            elif message.role == MessageRole.ASSISTANT:
                content = []
                if message.content:
                    content.append({"type": "text", "text": message.content})

                if message.tool_calls:
                    # Convert tool calls to Anthropic format if they match expected structure
                    # We might need to ensure they match Anthropic's 'tool_use' block format
                    for tc in message.tool_calls:
                        if isinstance(tc, dict):
                             # Assuming tc is already in a compatible dict format or we convert it
                             # Anthropic expects: {type: "tool_use", id: "...", name: "...", input: {...}}
                             if tc.get("type") == "tool_use":
                                 content.append(tc)
                             elif tc.get("type") == "function": # OpenAI style
                                 content.append({
                                     "type": "tool_use",
                                     "id": tc.get("id"),
                                     "name": tc["function"]["name"],
                                     "input": tc["function"]["arguments"] # Note: arguments in OpenAI is string, Anthropic needs dict
                                     # This conversion is complex if arguments is string JSON.
                                     # For now, we assume if we are using Anthropic, tool_calls came from Anthropic
                                     # and are already in correct format, OR we need JSON parsing.
                                 })

                if not content:
                    # Fallback for simple content string if no tool calls processed
                     claude_messages.append({"role": "assistant", "content": message.content})
                else:
                    claude_messages.append({"role": "assistant", "content": content})

            elif message.role == MessageRole.TOOL:
                # Tool result
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": message.tool_call_id,
                        "content": message.content
                    }]
                })

        # Ensure we have at least one user message
        if not claude_messages:
            raise ValueError("At least one user message is required")

        # Ensure last message is from user (Anthropic requirement for API calls, but checking here might be strict)
        # Actually Anthropic allows Assistant message if prefilling.
        # But for 'messages.create' usually we end with user.
        # However, if we are looping tool calls, the last message might be a tool result (which acts as user).

        # Check if last message is from user (or tool result which is user role)
        if claude_messages[-1]["role"] != "user":
            # If the last message is assistant, we might be continuing?
            # But usually we send request after user input.
            pass

        return system_message, claude_messages

    def _convert_response_from_anthropic(self, response: Message) -> ApiResponse:
        """Convert Anthropic response to ApiResponse.

        Args:
            response: Anthropic message response

        Returns:
            ApiResponse object
        """
        content = ""
        tool_calls = []

        if response.content:
            # Claude returns content as a list, concatenate text blocks
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
                elif isinstance(block, dict) and block.get("type") == "text":
                    content += block.get("text", "")

                # Check for tool usage
                if hasattr(block, "type") and block.type == "tool_use":
                    # Convert object to dict if needed
                    tool_calls.append(block.to_dict() if hasattr(block, "to_dict") else block)
                elif isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_calls.append(block)

        # Extract usage information
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=(
                (response.usage.input_tokens + response.usage.output_tokens)
                if response.usage
                else 0
            ),
        )

        # Map Anthropic stop reasons to our format
        finish_reason = "unknown"
        if response.stop_reason:
            reason_map = {
                "end_turn": "stop",
                "max_tokens": "length",
                "stop_sequence": "stop",
                "tool_use": "tool_calls",
            }
            finish_reason = reason_map.get(response.stop_reason, "unknown")

        result = ApiResponse(
            content=content,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls
        )

        return result

    def _handle_anthropic_error(self, error: anthropic.APIError) -> ApiResponse:
        """Handle Anthropic-specific errors.

        Args:
            error: Anthropic API error

        Returns:
            ApiResponse with error information
        """
        error_type = "anthropic_error"

        # Categorize error types
        error_str = str(error).lower()
        if "rate" in error_str:
            error_type = "rate_limit"
        elif "token" in error_str:
            error_type = "token_limit"
        elif "model" in error_str:
            error_type = "model_not_found"
        elif "permission" in error_str:
            error_type = "permission_denied"

        return self._format_error_response(error, error_type)

    async def close(self):
        """Close both the base client and Anthropic client."""
        await super().close()
        await self.anthropic_client.close()
