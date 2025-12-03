"""Tests for the ClientFactory."""

import pytest

from vibe_coder.api.anthropic_client import AnthropicClient
from vibe_coder.api.factory import ClientFactory
from vibe_coder.api.generic_client import GenericClient
from vibe_coder.api.openai_client import OpenAIClient
from vibe_coder.types.config import AIProvider


class TestClientFactory:
    """Test ClientFactory functionality."""

    def test_create_openai_client_by_name(self):
        """Test creating OpenAI client by provider name."""
        provider = AIProvider(
            name="openai",
            api_key="sk-test123456",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, OpenAIClient)
        assert client.provider.name == "openai"

    def test_create_anthropic_client_by_name(self):
        """Test creating Anthropic client by provider name."""
        provider = AIProvider(
            name="anthropic",
            api_key="sk-ant-test123456",
            endpoint="https://api.anthropic.com",
            model="claude-3-5-sonnet-20241022",
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, AnthropicClient)
        assert client.provider.name == "anthropic"

    def test_create_generic_client_by_name(self):
        """Test creating generic client by provider name."""
        provider = AIProvider(
            name="ollama", api_key="not-needed", endpoint="http://localhost:11434", model="llama3"
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, GenericClient)
        assert client.provider.name == "ollama"

    def test_create_openai_client_by_endpoint(self):
        """Test creating OpenAI client by endpoint URL."""
        provider = AIProvider(
            name="my-custom-gpt",
            api_key="sk-test123456",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, OpenAIClient)

    def test_create_anthropic_client_by_endpoint(self):
        """Test creating Anthropic client by endpoint URL."""
        provider = AIProvider(
            name="my-claude",
            api_key="sk-ant-test123456",
            endpoint="https://api.anthropic.com",
            model="claude-3-5-sonnet-20241022",
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, AnthropicClient)

    def test_fallback_to_generic_client(self):
        """Test fallback to generic client for unknown providers."""
        provider = AIProvider(
            name="unknown-llm",
            api_key="test-key",
            endpoint="https://api.unknown.com/v1",
            model="unknown-model",
        )

        client = ClientFactory.create_client(provider)
        assert isinstance(client, GenericClient)

    def test_partial_name_matching(self):
        """Test partial name matching works."""
        # Test GPT matching
        provider = AIProvider(
            name="my-gpt-provider",
            api_key="sk-test123456",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
        )
        client = ClientFactory.create_client(provider)
        assert isinstance(client, OpenAIClient)

        # Test Claude matching
        provider = AIProvider(
            name="custom-claude",
            api_key="sk-ant-test123456",
            endpoint="https://api.anthropic.com",
            model="claude-3-5-sonnet-20241022",
        )
        client = ClientFactory.create_client(provider)
        assert isinstance(client, AnthropicClient)

    def test_invalid_provider_config(self):
        """Test validation of provider configuration."""
        # Missing API key
        provider = AIProvider(name="openai", api_key="", endpoint="https://api.openai.com/v1")
        with pytest.raises(ValueError, match="api_key and endpoint"):
            ClientFactory.create_client(provider)

        # Missing endpoint
        provider = AIProvider(name="openai", api_key="sk-test123456", endpoint="")
        with pytest.raises(ValueError, match="api_key and endpoint"):
            ClientFactory.create_client(provider)

    def test_get_supported_providers(self):
        """Test getting supported provider types."""
        supported = ClientFactory.get_supported_providers()
        assert "OpenAI" in supported
        assert "Anthropic" in supported
        assert "Generic" in supported
        assert len(supported) == 3

    def test_get_default_models(self):
        """Test getting default models for each client type."""
        openai_models = ClientFactory.get_default_models(OpenAIClient)
        assert "gpt-4o" in openai_models
        assert "gpt-3.5-turbo" in openai_models

        anthropic_models = ClientFactory.get_default_models(AnthropicClient)
        assert "claude-3-5-sonnet-20241022" in anthropic_models
        assert "claude-3-haiku-20240307" in anthropic_models

        generic_models = ClientFactory.get_default_models(GenericClient)
        assert "llama2" in generic_models
        assert "mistral" in generic_models

    def test_validate_provider_config(self):
        """Test provider configuration validation."""
        # Valid configuration
        provider = AIProvider(
            name="openai", api_key="sk-test123456789", endpoint="https://api.openai.com/v1"
        )
        errors = ClientFactory.validate_provider_config(provider)
        assert len(errors) == 0

        # Invalid configuration
        provider = AIProvider(name="openai", api_key="short", endpoint="invalid-url")
        errors = ClientFactory.validate_provider_config(provider)
        assert len(errors) > 0
        assert any("API key" in error for error in errors)
        assert any("endpoint" in error for error in errors)

    def test_validate_openai_api_key_pattern(self):
        """Test OpenAI API key validation."""
        provider = AIProvider(
            name="openai", api_key="invalid-key", endpoint="https://api.openai.com/v1"
        )
        errors = ClientFactory.validate_provider_config(provider)
        assert any("API keys should start with 'sk-'" in error for error in errors)

    def test_validate_anthropic_api_key_pattern(self):
        """Test Anthropic API key validation."""
        provider = AIProvider(
            name="anthropic", api_key="invalid-key", endpoint="https://api.anthropic.com"
        )
        errors = ClientFactory.validate_provider_config(provider)
        assert any("API keys should start with 'sk-ant-'" in error for error in errors)
