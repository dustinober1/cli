"""Tests for environment variable configuration handler."""

import os
import tempfile
from pathlib import Path

import pytest

from vibe_coder.config.env_handler import (
    get_env_provider,
    has_env_config,
    load_env_config,
    save_to_env,
)


class TestLoadEnvConfig:
    """Test loading configuration from environment variables."""

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up environment variables after each test."""
        yield
        # Clean up after test
        for key in list(os.environ.keys()):
            if key.startswith("VIBE_CODER_"):
                del os.environ[key]

    def test_load_minimal_config(self):
        """Test loading minimal config with just required vars."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"

        config = load_env_config()
        assert config is not None
        assert config["api_key"] == "sk-test"
        assert config["endpoint"] == "https://api.com"

    def test_load_complete_config(self):
        """Test loading complete config with all variables."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-complete"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.complete.com"
        os.environ["VIBE_CODER_MODEL"] = "model-x"
        os.environ["VIBE_CODER_TEMPERATURE"] = "0.8"
        os.environ["VIBE_CODER_MAX_TOKENS"] = "1000"
        os.environ["VIBE_CODER_PROVIDER_NAME"] = "complete-provider"

        config = load_env_config()
        assert config is not None
        assert config["api_key"] == "sk-complete"
        assert config["endpoint"] == "https://api.complete.com"
        assert config["model"] == "model-x"
        assert config["temperature"] == "0.8"
        assert config["max_tokens"] == "1000"
        assert config["provider_name"] == "complete-provider"

    def test_load_config_with_only_api_key(self):
        """Test loading config with only API key."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-only-key"

        config = load_env_config()
        assert config is not None
        assert config["api_key"] == "sk-only-key"

    def test_load_config_with_only_endpoint(self):
        """Test loading config with only endpoint."""
        os.environ["VIBE_CODER_ENDPOINT"] = "https://endpoint-only.com"

        config = load_env_config()
        assert config is not None
        assert config["endpoint"] == "https://endpoint-only.com"

    def test_load_config_no_vars_returns_none(self):
        """Test that None is returned when no VIBE_CODER vars are set."""
        # Make sure no VIBE_CODER vars exist
        for key in list(os.environ.keys()):
            if key.startswith("VIBE_CODER_"):
                del os.environ[key]

        config = load_env_config()
        assert config is None

    def test_load_config_with_optional_fields(self):
        """Test loading config with optional fields."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_MODEL"] = "gpt-4"

        config = load_env_config()
        assert config is not None
        assert config["model"] == "gpt-4"
        assert config.get("temperature") is None  # Not set


class TestGetEnvProvider:
    """Test creating AIProvider from environment variables."""

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up environment variables after each test."""
        yield
        for key in list(os.environ.keys()):
            if key.startswith("VIBE_CODER_"):
                del os.environ[key]

    def test_get_provider_minimal(self):
        """Test creating provider with minimal config."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-minimal"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.minimal.com"

        provider = get_env_provider()
        assert provider is not None
        assert provider.name == "env"  # Default name
        assert provider.api_key == "sk-minimal"
        assert provider.endpoint == "https://api.minimal.com"
        assert provider.temperature == 0.7  # Default

    def test_get_provider_complete(self):
        """Test creating provider with all fields."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-complete"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.complete.com"
        os.environ["VIBE_CODER_MODEL"] = "gpt-4"
        os.environ["VIBE_CODER_TEMPERATURE"] = "0.9"
        os.environ["VIBE_CODER_MAX_TOKENS"] = "2000"
        os.environ["VIBE_CODER_PROVIDER_NAME"] = "custom-name"

        provider = get_env_provider()
        assert provider is not None
        assert provider.name == "custom-name"
        assert provider.api_key == "sk-complete"
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.9
        assert provider.max_tokens == 2000

    def test_get_provider_no_vars_returns_none(self):
        """Test that None is returned when no vars are set."""
        provider = get_env_provider()
        assert provider is None

    def test_get_provider_missing_api_key_raises_error(self):
        """Test error when API key is missing."""
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"

        with pytest.raises(ValueError, match="VIBE_CODER_API_KEY"):
            get_env_provider()

    def test_get_provider_missing_endpoint_raises_error(self):
        """Test error when endpoint is missing."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"

        with pytest.raises(ValueError, match="VIBE_CODER_ENDPOINT"):
            get_env_provider()

    def test_get_provider_invalid_temperature_raises_error(self):
        """Test error when temperature is out of range."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_TEMPERATURE"] = "3.0"

        with pytest.raises(ValueError, match="Invalid temperature"):
            get_env_provider()

    def test_get_provider_invalid_temperature_too_low(self):
        """Test error when temperature is too low."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_TEMPERATURE"] = "-0.1"

        with pytest.raises(ValueError, match="Invalid temperature"):
            get_env_provider()

    def test_get_provider_invalid_temperature_not_numeric(self):
        """Test error when temperature is not numeric."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_TEMPERATURE"] = "not-a-number"

        with pytest.raises(ValueError, match="Invalid temperature"):
            get_env_provider()

    def test_get_provider_invalid_max_tokens_negative(self):
        """Test error when max_tokens is negative."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_MAX_TOKENS"] = "-100"

        with pytest.raises(ValueError, match="max_tokens"):
            get_env_provider()

    def test_get_provider_invalid_max_tokens_zero(self):
        """Test error when max_tokens is zero."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_MAX_TOKENS"] = "0"

        with pytest.raises(ValueError, match="max_tokens"):
            get_env_provider()

    def test_get_provider_invalid_max_tokens_not_numeric(self):
        """Test error when max_tokens is not numeric."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        os.environ["VIBE_CODER_MAX_TOKENS"] = "not-a-number"

        with pytest.raises(ValueError, match="Invalid max_tokens"):
            get_env_provider()

    def test_get_provider_temperature_boundaries(self):
        """Test that temperature boundaries are accepted."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"

        # Test boundary 0.0
        os.environ["VIBE_CODER_TEMPERATURE"] = "0.0"
        provider = get_env_provider()
        assert provider.temperature == 0.0

        # Test boundary 2.0
        os.environ["VIBE_CODER_TEMPERATURE"] = "2.0"
        provider = get_env_provider()
        assert provider.temperature == 2.0


class TestSaveToEnv:
    """Test saving configuration to .env file."""

    def test_save_minimal_config(self):
        """Test saving minimal config to .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            save_to_env(
                api_key="sk-save",
                endpoint="https://api.save.com",
                env_file=str(env_file),
            )

            assert env_file.exists()
            content = env_file.read_text()
            assert "VIBE_CODER_API_KEY" in content and "sk-save" in content
            assert "VIBE_CODER_ENDPOINT" in content and "https://api.save.com" in content

    def test_save_complete_config(self):
        """Test saving complete config to .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            save_to_env(
                api_key="sk-complete",
                endpoint="https://api.complete.com",
                model="gpt-4",
                temperature=0.8,
                max_tokens=1000,
                provider_name="complete-provider",
                env_file=str(env_file),
            )

            assert env_file.exists()
            content = env_file.read_text()
            assert "sk-complete" in content
            assert "gpt-4" in content
            assert "0.8" in content
            assert "1000" in content
            assert "complete-provider" in content

    def test_save_invalid_temperature_raises_error(self):
        """Test that invalid temperature raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            with pytest.raises(ValueError, match="Temperature"):
                save_to_env(
                    api_key="sk-test",
                    endpoint="https://api.com",
                    temperature=3.0,
                    env_file=str(env_file),
                )

    def test_save_invalid_max_tokens_raises_error(self):
        """Test that invalid max_tokens raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            with pytest.raises(ValueError, match="max_tokens"):
                save_to_env(
                    api_key="sk-test",
                    endpoint="https://api.com",
                    max_tokens=-100,
                    env_file=str(env_file),
                )

    def test_save_creates_custom_env_file(self):
        """Test saving to custom .env file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_file = Path(tmpdir) / "custom.env"

            save_to_env(
                api_key="sk-custom",
                endpoint="https://api.custom.com",
                env_file=str(custom_file),
            )

            assert custom_file.exists()
            content = custom_file.read_text()
            assert "sk-custom" in content


class TestHasEnvConfig:
    """Test checking if environment config is available."""

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up environment variables after each test."""
        yield
        for key in list(os.environ.keys()):
            if key.startswith("VIBE_CODER_"):
                del os.environ[key]

    def test_has_env_config_false_initially(self):
        """Test that has_env_config returns False when no vars set."""
        assert has_env_config() is False

    def test_has_env_config_true_with_api_key(self):
        """Test that has_env_config returns True with API key."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        assert has_env_config() is True

    def test_has_env_config_true_with_endpoint(self):
        """Test that has_env_config returns True with endpoint."""
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        assert has_env_config() is True

    def test_has_env_config_true_with_both(self):
        """Test that has_env_config returns True with both vars."""
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        os.environ["VIBE_CODER_ENDPOINT"] = "https://api.com"
        assert has_env_config() is True

    def test_has_env_config_true_with_other_vars(self):
        """Test that has_env_config returns True with other VIBE_CODER vars."""
        os.environ["VIBE_CODER_MODEL"] = "gpt-4"
        # API_KEY and ENDPOINT are not set, but other vars are
        assert has_env_config() is False

        # Now add one of the required vars
        os.environ["VIBE_CODER_API_KEY"] = "sk-test"
        assert has_env_config() is True


class TestIntegration:
    """Integration tests for env handler."""

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up environment variables after each test."""
        yield
        for key in list(os.environ.keys()):
            if key.startswith("VIBE_CODER_"):
                del os.environ[key]

    def test_save_and_load_workflow(self):
        """Test saving config and loading it as provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            # Save config
            save_to_env(
                api_key="sk-workflow",
                endpoint="https://api.workflow.com",
                model="test-model",
                temperature=0.5,
                max_tokens=500,
                provider_name="workflow-provider",
                env_file=str(env_file),
            )

            # Now load it by setting env var to point to our file
            # (In real usage, the .env file would be loaded by dotenv)
            # For this test, we'll set the env vars directly as if .env was loaded
            os.environ["VIBE_CODER_API_KEY"] = "sk-workflow"
            os.environ["VIBE_CODER_ENDPOINT"] = "https://api.workflow.com"
            os.environ["VIBE_CODER_MODEL"] = "test-model"
            os.environ["VIBE_CODER_TEMPERATURE"] = "0.5"
            os.environ["VIBE_CODER_MAX_TOKENS"] = "500"
            os.environ["VIBE_CODER_PROVIDER_NAME"] = "workflow-provider"

            # Load as provider
            provider = get_env_provider()
            assert provider is not None
            assert provider.name == "workflow-provider"
            assert provider.api_key == "sk-workflow"
            assert provider.endpoint == "https://api.workflow.com"
            assert provider.model == "test-model"
