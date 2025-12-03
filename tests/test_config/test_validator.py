"""Tests for configuration validator functions."""

from vibe_coder.config.validator import (
    is_localhost,
    is_valid_url,
    validate_api_key,
    validate_endpoint,
    validate_max_tokens,
    validate_provider,
    validate_provider_config,
    validate_temperature,
)
from vibe_coder.types.config import AIProvider


class TestValidateApiKey:
    """Test API key validation."""

    def test_valid_api_key(self):
        """Test valid API keys."""
        assert validate_api_key("sk-1234567890") is True
        assert validate_api_key("sk-very-long-api-key-12345") is True
        assert validate_api_key("test-key-minimum10") is True

    def test_valid_api_key_exactly_10_chars(self):
        """Test API key with exactly 10 characters."""
        assert validate_api_key("1234567890") is True

    def test_invalid_api_key_too_short(self):
        """Test API key shorter than 10 characters."""
        assert validate_api_key("short") is False
        assert validate_api_key("123456789") is False

    def test_invalid_api_key_with_spaces(self):
        """Test API key containing spaces."""
        assert validate_api_key("has space") is False
        assert validate_api_key("sk-test key") is False

    def test_invalid_api_key_empty(self):
        """Test empty API key."""
        assert validate_api_key("") is False

    def test_invalid_api_key_not_string(self):
        """Test non-string API key."""
        assert validate_api_key(None) is False
        assert validate_api_key(123) is False


class TestValidateEndpoint:
    """Test endpoint URL validation."""

    def test_valid_https_endpoint(self):
        """Test valid HTTPS endpoints."""
        assert validate_endpoint("https://api.openai.com/v1") is True
        assert validate_endpoint("https://api.anthropic.com") is True
        assert validate_endpoint("https://example.com:8443") is True

    def test_valid_http_endpoint(self):
        """Test valid HTTP endpoints."""
        assert validate_endpoint("http://localhost:8000") is True
        assert validate_endpoint("http://127.0.0.1:5000") is True
        assert validate_endpoint("http://example.com") is True

    def test_valid_endpoint_with_path(self):
        """Test endpoints with paths."""
        assert validate_endpoint("https://api.openai.com/v1/chat") is True
        assert validate_endpoint("http://localhost:8000/api") is True

    def test_invalid_endpoint_no_scheme(self):
        """Test endpoint without scheme."""
        assert validate_endpoint("api.openai.com") is False
        assert validate_endpoint("example.com") is False

    def test_invalid_endpoint_invalid_scheme(self):
        """Test endpoint with invalid scheme."""
        assert validate_endpoint("ftp://example.com") is False
        assert validate_endpoint("file:///path/to/file") is False

    def test_invalid_endpoint_no_domain(self):
        """Test endpoint without domain."""
        assert validate_endpoint("https://") is False
        assert validate_endpoint("http://") is False

    def test_invalid_endpoint_empty(self):
        """Test empty endpoint."""
        assert validate_endpoint("") is False

    def test_invalid_endpoint_not_string(self):
        """Test non-string endpoint."""
        assert validate_endpoint(None) is False
        assert validate_endpoint(123) is False


class TestValidateTemperature:
    """Test temperature validation."""

    def test_valid_temperature_default(self):
        """Test default temperature."""
        assert validate_temperature(0.7) is True

    def test_valid_temperature_boundaries(self):
        """Test temperature boundaries."""
        assert validate_temperature(0.0) is True
        assert validate_temperature(2.0) is True

    def test_valid_temperature_mid_range(self):
        """Test temperatures in valid range."""
        assert validate_temperature(0.5) is True
        assert validate_temperature(1.0) is True
        assert validate_temperature(1.5) is True

    def test_invalid_temperature_too_high(self):
        """Test temperature above 2.0."""
        assert validate_temperature(2.1) is False
        assert validate_temperature(3.0) is False
        assert validate_temperature(100.0) is False

    def test_invalid_temperature_too_low(self):
        """Test temperature below 0.0."""
        assert validate_temperature(-0.1) is False
        assert validate_temperature(-1.0) is False

    def test_invalid_temperature_not_numeric(self):
        """Test non-numeric temperature."""
        assert validate_temperature(None) is False
        assert validate_temperature("0.7") is False
        assert validate_temperature([]) is False

    def test_valid_temperature_as_int(self):
        """Test temperature as integer."""
        assert validate_temperature(0) is True
        assert validate_temperature(1) is True
        assert validate_temperature(2) is True

    def test_invalid_temperature_as_int(self):
        """Test invalid integer temperature."""
        assert validate_temperature(-1) is False
        assert validate_temperature(3) is False


class TestValidateMaxTokens:
    """Test max_tokens validation."""

    def test_valid_max_tokens(self):
        """Test valid max_tokens."""
        assert validate_max_tokens(1) is True
        assert validate_max_tokens(100) is True
        assert validate_max_tokens(4096) is True
        assert validate_max_tokens(100000) is True

    def test_invalid_max_tokens_zero(self):
        """Test max_tokens of zero."""
        assert validate_max_tokens(0) is False

    def test_invalid_max_tokens_negative(self):
        """Test negative max_tokens."""
        assert validate_max_tokens(-1) is False
        assert validate_max_tokens(-100) is False

    def test_invalid_max_tokens_not_int(self):
        """Test non-integer max_tokens."""
        assert validate_max_tokens(None) is False
        assert validate_max_tokens(3.14) is False
        assert validate_max_tokens("100") is False


class TestValidateProvider:
    """Test AIProvider validation."""

    def test_valid_provider_minimal(self):
        """Test validation of minimal valid provider."""
        provider = AIProvider(
            name="test",
            api_key="sk-test-1234567890",
            endpoint="https://api.com",
        )
        errors = validate_provider(provider)
        assert len(errors) == 0

    def test_valid_provider_complete(self):
        """Test validation of complete valid provider."""
        provider = AIProvider(
            name="test",
            api_key="sk-test-1234567890",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.8,
            max_tokens=1000,
        )
        errors = validate_provider(provider)
        assert len(errors) == 0

    def test_invalid_provider_empty_name(self):
        """Test provider with empty name."""
        provider = AIProvider(
            name="",
            api_key="sk-test-1234567890",
            endpoint="https://api.com",
        )
        errors = validate_provider(provider)
        assert len(errors) >= 1
        assert any("name" in err.lower() for err in errors)

    def test_invalid_provider_short_api_key(self):
        """Test provider with short API key."""
        try:
            provider = AIProvider(
                name="test",
                api_key="short",
                endpoint="https://api.com",
            )
            errors = validate_provider(provider)
            # API key validation at __post_init__ doesn't fail on short keys
            # but our validator will catch it
            assert any("api key" in err.lower() for err in errors)
        except ValueError:
            # __post_init__ doesn't validate api_key format
            pass

    def test_invalid_provider_bad_endpoint(self):
        """Test provider with invalid endpoint."""
        provider = AIProvider(
            name="test",
            api_key="sk-test-1234567890",
            endpoint="not-a-url",
        )
        errors = validate_provider(provider)
        assert len(errors) >= 1
        assert any("endpoint" in err.lower() or "url" in err.lower() for err in errors)

    def test_invalid_provider_invalid_max_tokens(self):
        """Test provider with invalid max_tokens."""
        try:
            AIProvider(
                name="test",
                api_key="sk-test-1234567890",
                endpoint="https://api.com",
                max_tokens=-100,
            )
            # __post_init__ should have caught this
            assert False, "Should have raised ValueError"
        except ValueError:
            # Expected - __post_init__ validates max_tokens
            pass


class TestIsLocalhost:
    """Test localhost detection."""

    def test_is_localhost_localhost(self):
        """Test localhost detection."""
        assert is_localhost("http://localhost:8000") is True
        assert is_localhost("https://localhost") is True
        assert is_localhost("http://localhost") is True

    def test_is_localhost_127_0_0_1(self):
        """Test 127.0.0.1 detection."""
        assert is_localhost("http://127.0.0.1:8000") is True
        assert is_localhost("https://127.0.0.1") is True

    def test_is_localhost_ipv6(self):
        """Test IPv6 localhost."""
        assert is_localhost("http://[::1]:8000") is True
        assert is_localhost("http://[::1]") is True

    def test_not_localhost(self):
        """Test non-localhost URLs."""
        assert is_localhost("https://api.openai.com") is False
        assert is_localhost("http://example.com") is False
        assert is_localhost("https://192.168.1.1") is False

    def test_is_localhost_invalid_url(self):
        """Test invalid URLs."""
        assert is_localhost("not-a-url") is False
        assert is_localhost("") is False


class TestIsValidUrl:
    """Test URL validation."""

    def test_is_valid_url_https(self):
        """Test valid HTTPS URLs."""
        assert is_valid_url("https://api.openai.com/v1") is True
        assert is_valid_url("https://example.com") is True

    def test_is_valid_url_http(self):
        """Test valid HTTP URLs."""
        assert is_valid_url("http://localhost:8000") is True
        assert is_valid_url("http://example.com") is True

    def test_is_valid_url_with_port(self):
        """Test URLs with port."""
        assert is_valid_url("https://api.com:8443") is True
        assert is_valid_url("http://localhost:5000") is True

    def test_is_not_valid_url(self):
        """Test invalid URLs."""
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("example.com") is False
        assert is_valid_url("") is False

    def test_is_not_valid_url_invalid_scheme(self):
        """Test invalid URL schemes."""
        assert is_valid_url("ftp://example.com") is False
        assert is_valid_url("file:///path") is False


class TestValidateProviderConfig:
    """Test provider config validation from raw values."""

    def test_valid_provider_config_minimal(self):
        """Test valid minimal config."""
        errors = validate_provider_config(
            "test",
            "sk-test-1234567890",
            "https://api.com",
        )
        assert len(errors) == 0

    def test_valid_provider_config_complete(self):
        """Test valid complete config."""
        errors = validate_provider_config(
            "test",
            "sk-test-1234567890",
            "https://api.openai.com/v1",
            0.8,
            1000,
        )
        assert len(errors) == 0

    def test_invalid_provider_config_empty_name(self):
        """Test config with empty name."""
        errors = validate_provider_config(
            "",
            "sk-test-1234567890",
            "https://api.com",
        )
        assert len(errors) >= 1

    def test_invalid_provider_config_short_api_key(self):
        """Test config with short API key."""
        errors = validate_provider_config(
            "test",
            "short",
            "https://api.com",
        )
        assert len(errors) >= 1

    def test_invalid_provider_config_bad_endpoint(self):
        """Test config with invalid endpoint."""
        errors = validate_provider_config(
            "test",
            "sk-test-1234567890",
            "not-a-url",
        )
        assert len(errors) >= 1

    def test_invalid_provider_config_bad_temperature(self):
        """Test config with invalid temperature."""
        errors = validate_provider_config(
            "test",
            "sk-test-1234567890",
            "https://api.com",
            3.0,
        )
        assert len(errors) >= 1

    def test_invalid_provider_config_bad_max_tokens(self):
        """Test config with invalid max_tokens."""
        errors = validate_provider_config(
            "test",
            "sk-test-1234567890",
            "https://api.com",
            0.7,
            -100,
        )
        assert len(errors) >= 1

    def test_invalid_provider_config_multiple_errors(self):
        """Test config with multiple validation errors."""
        errors = validate_provider_config(
            "",
            "short",
            "not-a-url",
            3.0,
            -100,
        )
        # Should have multiple errors
        assert len(errors) >= 3


class TestIntegration:
    """Integration tests for validation."""

    def test_validate_real_openai_config(self):
        """Test validation with realistic OpenAI config."""
        provider = AIProvider(
            name="openai",
            api_key="sk-proj-abcdefghijklmnopqrstuvwxyz123456789",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
        )
        errors = validate_provider(provider)
        assert len(errors) == 0

    def test_validate_real_anthropic_config(self):
        """Test validation with realistic Anthropic config."""
        provider = AIProvider(
            name="anthropic",
            api_key="sk-ant-abcdefghijklmnopqrstuvwxyz123456789",
            endpoint="https://api.anthropic.com/v1",
            model="claude-3-opus-20240229",
            temperature=0.8,
        )
        errors = validate_provider(provider)
        assert len(errors) == 0

    def test_validate_local_provider_config(self):
        """Test validation with local provider."""
        provider = AIProvider(
            name="local-ollama",
            api_key="sk-local-test-key-1234567890",
            endpoint="http://localhost:11434",
            model="llama2",
        )
        errors = validate_provider(provider)
        assert len(errors) == 0
