"""Tests for configuration type definitions (dataclasses)."""

import pytest

from vibe_coder.types.config import AIProvider, AppConfig, InteractionMode, ProviderType


class TestAIProvider:
    """Test suite for AIProvider dataclass."""

    def test_create_provider_with_valid_values(self):
        """Test creating an AIProvider with valid values."""
        provider = AIProvider(
            name="test-openai",
            api_key="sk-test-key-1234567890",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
        )
        assert provider.name == "test-openai"
        assert provider.api_key == "sk-test-key-1234567890"
        assert provider.endpoint == "https://api.openai.com/v1"
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 2000

    def test_create_provider_with_minimal_values(self):
        """Test creating an AIProvider with only required fields."""
        provider = AIProvider(
            name="minimal",
            api_key="sk-minimal-key-123",
            endpoint="https://api.example.com",
        )
        assert provider.name == "minimal"
        assert provider.temperature == 0.7  # Default
        assert provider.max_tokens is None  # Default
        assert provider.model is None  # Default

    def test_temperature_validation_too_high(self):
        """Test that temperature > 2.0 raises ValueError."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            AIProvider(
                name="bad",
                api_key="sk-test-key-1234567890",
                endpoint="https://api.openai.com/v1",
                temperature=2.1,
            )

    def test_temperature_validation_too_low(self):
        """Test that temperature < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            AIProvider(
                name="bad",
                api_key="sk-test-key-1234567890",
                endpoint="https://api.openai.com/v1",
                temperature=-0.1,
            )

    def test_temperature_validation_boundaries(self):
        """Test that temperature boundaries (0.0 and 2.0) are valid."""
        provider_cold = AIProvider(
            name="cold",
            api_key="sk-test-key-1234567890",
            endpoint="https://api.openai.com/v1",
            temperature=0.0,
        )
        assert provider_cold.temperature == 0.0

        provider_hot = AIProvider(
            name="hot",
            api_key="sk-test-key-1234567890",
            endpoint="https://api.openai.com/v1",
            temperature=2.0,
        )
        assert provider_hot.temperature == 2.0

    def test_max_tokens_validation_negative(self):
        """Test that negative max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            AIProvider(
                name="bad",
                api_key="sk-test-key-1234567890",
                endpoint="https://api.openai.com/v1",
                max_tokens=-100,
            )

    def test_max_tokens_validation_zero(self):
        """Test that max_tokens=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            AIProvider(
                name="bad",
                api_key="sk-test-key-1234567890",
                endpoint="https://api.openai.com/v1",
                max_tokens=0,
            )

    def test_max_tokens_validation_valid(self):
        """Test that positive max_tokens values are accepted."""
        provider = AIProvider(
            name="valid",
            api_key="sk-test-key-1234567890",
            endpoint="https://api.openai.com/v1",
            max_tokens=1,
        )
        assert provider.max_tokens == 1

    def test_provider_to_dict(self):
        """Test AIProvider.to_dict() serialization."""
        provider = AIProvider(
            name="test",
            api_key="sk-test-key",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.8,
            max_tokens=1500,
            headers={"X-Custom": "value"},
        )
        result = provider.to_dict()
        assert result["name"] == "test"
        assert result["api_key"] == "sk-test-key"
        assert result["endpoint"] == "https://api.openai.com/v1"
        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.8
        assert result["max_tokens"] == 1500
        assert result["headers"] == {"X-Custom": "value"}

    def test_provider_from_dict(self):
        """Test AIProvider.from_dict() deserialization."""
        data = {
            "name": "test",
            "api_key": "sk-test-key",
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4",
            "temperature": 0.8,
            "max_tokens": 1500,
            "headers": {"X-Custom": "value"},
        }
        provider = AIProvider.from_dict(data)
        assert provider.name == "test"
        assert provider.api_key == "sk-test-key"
        assert provider.temperature == 0.8
        assert provider.headers == {"X-Custom": "value"}

    def test_provider_round_trip(self):
        """Test that provider survives to_dict -> from_dict round trip."""
        original = AIProvider(
            name="round-trip",
            api_key="sk-test-key",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.9,
            max_tokens=2000,
        )
        restored = AIProvider.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.api_key == original.api_key
        assert restored.endpoint == original.endpoint
        assert restored.model == original.model
        assert restored.temperature == original.temperature
        assert restored.max_tokens == original.max_tokens


class TestAppConfig:
    """Test suite for AppConfig dataclass."""

    def test_create_default_config(self):
        """Test creating AppConfig with defaults."""
        config = AppConfig(current_provider="")
        assert config.current_provider == ""
        assert config.providers == {}
        assert config.default_model is None
        assert config.default_temperature == 0.7
        assert config.offline_mode is False
        assert config.debug_mode is False

    def test_set_and_get_provider(self):
        """Test setting and getting providers."""
        config = AppConfig(current_provider="test")
        provider = AIProvider(
            name="test",
            api_key="sk-test",
            endpoint="https://api.openai.com/v1",
        )
        config.set_provider("test", provider)
        retrieved = config.get_provider("test")
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_get_current_provider(self):
        """Test getting the current provider."""
        provider = AIProvider(
            name="current",
            api_key="sk-test",
            endpoint="https://api.openai.com/v1",
        )
        config = AppConfig(current_provider="current")
        config.set_provider("current", provider)
        current = config.get_provider()
        assert current is not None
        assert current.name == "current"

    def test_get_nonexistent_provider(self):
        """Test getting a provider that doesn't exist returns None."""
        config = AppConfig(current_provider="")
        result = config.get_provider("nonexistent")
        assert result is None

    def test_list_providers(self):
        """Test listing all configured providers."""
        config = AppConfig(current_provider="")
        provider1 = AIProvider(name="p1", api_key="sk-1", endpoint="https://api1.com")
        provider2 = AIProvider(name="p2", api_key="sk-2", endpoint="https://api2.com")
        config.set_provider("p1", provider1)
        config.set_provider("p2", provider2)

        providers_list = config.list_providers()
        assert set(providers_list) == {"p1", "p2"}
        assert len(providers_list) == 2

    def test_list_providers_empty(self):
        """Test listing providers when none are configured."""
        config = AppConfig(current_provider="")
        assert config.list_providers() == []

    def test_delete_provider(self):
        """Test deleting a provider."""
        provider = AIProvider(name="to-delete", api_key="sk-test", endpoint="https://api.com")
        config = AppConfig(current_provider="to-delete")
        config.set_provider("to-delete", provider)
        assert config.has_provider("to-delete")

        config.delete_provider("to-delete")
        assert not config.has_provider("to-delete")

    def test_delete_current_provider_clears_current(self):
        """Test that deleting current provider clears current_provider."""
        provider = AIProvider(name="current", api_key="sk-test", endpoint="https://api.com")
        config = AppConfig(current_provider="current")
        config.set_provider("current", provider)
        config.delete_provider("current")
        assert config.current_provider == ""

    def test_delete_non_current_provider(self):
        """Test deleting a non-current provider doesn't affect current."""
        provider1 = AIProvider(name="p1", api_key="sk-1", endpoint="https://api1.com")
        provider2 = AIProvider(name="p2", api_key="sk-2", endpoint="https://api2.com")
        config = AppConfig(current_provider="p1")
        config.set_provider("p1", provider1)
        config.set_provider("p2", provider2)

        config.delete_provider("p2")
        assert config.current_provider == "p1"
        assert config.has_provider("p1")
        assert not config.has_provider("p2")

    def test_has_provider(self):
        """Test checking if a provider exists."""
        provider = AIProvider(name="exists", api_key="sk-test", endpoint="https://api.com")
        config = AppConfig(current_provider="")
        config.set_provider("exists", provider)

        assert config.has_provider("exists") is True
        assert config.has_provider("missing") is False

    def test_config_to_dict(self):
        """Test AppConfig.to_dict() serialization."""
        provider = AIProvider(
            name="test",
            api_key="sk-test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
        )
        config = AppConfig(
            current_provider="test",
            default_model="gpt-3.5-turbo",
            default_temperature=0.8,
            default_max_tokens=1000,
            offline_mode=True,
            debug_mode=False,
        )
        config.set_provider("test", provider)

        result = config.to_dict()
        assert result["current_provider"] == "test"
        assert result["default_model"] == "gpt-3.5-turbo"
        assert result["default_temperature"] == 0.8
        assert result["default_max_tokens"] == 1000
        assert result["offline_mode"] is True
        assert result["debug_mode"] is False
        assert "test" in result["providers"]

    def test_config_from_dict(self):
        """Test AppConfig.from_dict() deserialization."""
        data = {
            "current_provider": "test",
            "providers": {
                "test": {
                    "name": "test",
                    "api_key": "sk-test",
                    "endpoint": "https://api.openai.com/v1",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": None,
                    "headers": None,
                }
            },
            "default_model": "gpt-4",
            "default_temperature": 0.8,
            "default_max_tokens": 1000,
            "offline_mode": False,
            "debug_mode": True,
        }
        config = AppConfig.from_dict(data)
        assert config.current_provider == "test"
        assert config.has_provider("test")
        assert config.default_model == "gpt-4"
        assert config.default_temperature == 0.8
        assert config.debug_mode is True

    def test_config_round_trip(self):
        """Test that config survives to_dict -> from_dict round trip."""
        provider = AIProvider(
            name="test",
            api_key="sk-test",
            endpoint="https://api.openai.com/v1",
            temperature=0.9,
        )
        original = AppConfig(current_provider="test")
        original.set_provider("test", provider)

        restored = AppConfig.from_dict(original.to_dict())
        assert restored.current_provider == original.current_provider
        assert restored.has_provider("test")
        restored_provider = restored.get_provider("test")
        assert restored_provider is not None
        assert restored_provider.name == provider.name

    def test_config_default(self):
        """Test AppConfig.default() factory method."""
        config = AppConfig.default()
        assert config.current_provider == ""
        assert config.providers == {}
        assert config.offline_mode is False


class TestEnums:
    """Test suite for configuration enums."""

    def test_interaction_mode_values(self):
        """Test that InteractionMode enum has correct values."""
        assert InteractionMode.CODE.value == "code"
        assert InteractionMode.ARCHITECT.value == "architect"
        assert InteractionMode.ASK.value == "ask"
        assert InteractionMode.AUDIT.value == "audit"

    def test_provider_type_values(self):
        """Test that ProviderType enum has correct values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.OLLAMA.value == "ollama"
        assert ProviderType.LM_STUDIO.value == "lm-studio"
        assert ProviderType.VLLM.value == "vllm"
        assert ProviderType.LOCAL_AI.value == "local-ai"
        assert ProviderType.GENERIC.value == "generic"

    def test_interaction_mode_by_value(self):
        """Test that InteractionMode can be looked up by value."""
        mode = InteractionMode("code")
        assert mode == InteractionMode.CODE

    def test_provider_type_by_value(self):
        """Test that ProviderType can be looked up by value."""
        provider = ProviderType("anthropic")
        assert provider == ProviderType.ANTHROPIC
