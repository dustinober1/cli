"""Factory for creating appropriate API clients."""

from typing import Optional, Type
from urllib.parse import urlparse

from vibe_coder.api.anthropic_client import AnthropicClient
from vibe_coder.api.base import BaseApiClient
from vibe_coder.api.generic_client import GenericClient
from vibe_coder.api.openai_client import OpenAIClient
from vibe_coder.types.config import AIProvider


class ClientFactory:
    """Factory for creating appropriate API clients based on provider configuration."""

    # Mapping of known provider patterns to client classes
    _PROVIDER_PATTERNS = {
        # Name-based patterns
        "openai": OpenAIClient,
        "gpt": OpenAIClient,
        "anthropic": AnthropicClient,
        "claude": AnthropicClient,
        "ollama": GenericClient,
        "lmstudio": GenericClient,
        "vllm": GenericClient,
        "localai": GenericClient,
        "together": GenericClient,
        "groq": GenericClient,
        "mistral": GenericClient,
        "cohere": GenericClient,
        "ai21": GenericClient,
    }

    # Endpoint URL patterns
    _ENDPOINT_PATTERNS = {
        "openai.com": OpenAIClient,
        "api.openai.com": OpenAIClient,
        "anthropic.com": AnthropicClient,
        "api.anthropic.com": AnthropicClient,
    }

    @classmethod
    def create_client(cls, provider: AIProvider) -> BaseApiClient:
        """Create the appropriate client for the given provider.

        Args:
            provider: AI provider configuration

        Returns:
            Instantiated API client

        Raises:
            ValueError: If provider configuration is invalid
        """
        if not provider or not provider.endpoint:
            raise ValueError("Provider must have endpoint configured")

        # Try detection by provider name first (most reliable)
        client_class = cls._detect_from_provider_name(provider.name)

        # If name detection fails, try endpoint detection
        if not client_class:
            client_class = cls._detect_from_endpoint(provider.endpoint)

        # Default to generic client if no specific detection works
        if not client_class:
            client_class = GenericClient

        return client_class(provider)

    @classmethod
    def _detect_from_provider_name(cls, provider_name: str) -> Optional[Type[BaseApiClient]]:
        """Detect client type from provider name.

        Args:
            provider_name: Name of the provider

        Returns:
            Client class or None if no match found
        """
        if not provider_name:
            return None

        name_lower = provider_name.lower()

        # Check exact matches
        for pattern, client_class in cls._PROVIDER_PATTERNS.items():
            if name_lower == pattern:
                return client_class

        # Check partial matches
        for pattern, client_class in cls._PROVIDER_PATTERNS.items():
            if pattern in name_lower:
                return client_class

        return None

    @classmethod
    def _detect_from_endpoint(cls, endpoint: str) -> Optional[Type[BaseApiClient]]:
        """Detect client type from endpoint URL.

        Args:
            endpoint: Endpoint URL

        Returns:
            Client class or None if no match found
        """
        try:
            parsed = urlparse(endpoint)
            domain = parsed.netloc.lower()

            # Check for exact domain matches
            if domain in cls._ENDPOINT_PATTERNS:
                return cls._ENDPOINT_PATTERNS[domain]

            # Check for partial domain matches
            for pattern, client_class in cls._ENDPOINT_PATTERNS.items():
                if pattern in domain:
                    return client_class

            # Check for localhost/local development (likely generic)
            if any(local in domain for local in ["localhost", "127.0.0.1", "0.0.0.1"]):
                return GenericClient

            # Check for common patterns
            if "openai" in domain:
                return OpenAIClient
            elif "anthropic" in domain:
                return AnthropicClient
            elif "ollama" in domain:
                return GenericClient

        except Exception:
            pass

        return None

    @classmethod
    def get_supported_providers(cls) -> dict:
        """Get a dictionary of supported provider types.

        Returns:
            Dictionary mapping provider types to descriptions
        """
        return {
            "OpenAI": "Official OpenAI API (GPT models)",
            "Anthropic": "Official Anthropic API (Claude models)",
            "Generic": "OpenAI-compatible endpoints (Ollama, LM Studio, vLLM, etc.)",
        }

    @classmethod
    def validate_provider_config(cls, provider: AIProvider) -> list[str]:
        """Validate provider configuration and return list of issues.

        Args:
            provider: Provider configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not provider.name:
            errors.append("Provider name is required")

        if not provider.endpoint:
            errors.append("Endpoint URL is required")

        # Validate endpoint format
        is_localhost = False
        try:
            parsed = urlparse(provider.endpoint)
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid endpoint URL format")
            elif parsed.scheme not in ["http", "https"]:
                errors.append("Endpoint must use http or https protocol")

            # Check if localhost
            if any(
                local in parsed.netloc.lower() for local in ["localhost", "127.0.0.1", "0.0.0.0"]
            ):
                is_localhost = True
        except Exception:
            errors.append("Invalid endpoint URL")

        # API key is required unless it's a local endpoint
        if not provider.api_key and not is_localhost:
            errors.append("API key is required for non-local endpoints")

        # Check for common issues based on detected client type
        try:
            client_class = cls._detect_from_provider_name(provider.name)
            if not client_class:
                client_class = cls._detect_from_endpoint(provider.endpoint)

            if client_class == OpenAIClient:
                if not provider.api_key.startswith("sk-"):
                    errors.append("OpenAI API keys should start with 'sk-'")
            elif client_class == AnthropicClient:
                if not provider.api_key.startswith("sk-ant-"):
                    errors.append("Anthropic API keys should start with 'sk-ant-'")

        except Exception:
            pass

        return errors

    @classmethod
    def get_default_models(cls, client_class: Type[BaseApiClient]) -> list[str]:
        """Get default models for a given client class.

        Args:
            client_class: The client class

        Returns:
            List of default model names
        """
        if client_class == OpenAIClient:
            return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        elif client_class == AnthropicClient:
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
        else:  # GenericClient
            return ["llama2", "llama3", "mistral", "codellama", "qwen", "deepseek-coder"]
