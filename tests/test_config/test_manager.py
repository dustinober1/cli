"""Tests for ConfigManager class."""

import json
import tempfile
from pathlib import Path

import pytest

from vibe_coder.config.manager import ConfigManager
from vibe_coder.types.config import AIProvider, AppConfig


class TestConfigManagerInitialization:
    """Test ConfigManager initialization."""

    def test_create_with_default_directory(self):
        """Test that ConfigManager creates default ~/.vibe directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            assert manager.config_dir == Path(tmpdir)
            assert manager.config_file == Path(tmpdir) / "config.json"

    def test_creates_config_directory(self):
        """Test that ConfigManager creates config directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "nested" / "vibe"
            ConfigManager(config_dir=config_dir)
            assert config_dir.exists()
            assert config_dir.is_dir()

    def test_creates_default_config_file(self):
        """Test that ConfigManager creates default config.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ConfigManager(config_dir=Path(tmpdir))
            config_file = Path(tmpdir) / "config.json"
            assert config_file.exists()

    def test_loads_existing_config(self):
        """Test that ConfigManager loads existing config.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial config
            config_file = Path(tmpdir) / "config.json"
            initial_config = {
                "current_provider": "existing",
                "providers": {
                    "existing": {
                        "name": "existing",
                        "api_key": "sk-test",
                        "endpoint": "https://api.com",
                        "model": None,
                        "temperature": 0.7,
                        "max_tokens": None,
                        "headers": None,
                    }
                },
                "default_model": None,
                "default_temperature": 0.7,
                "default_max_tokens": None,
                "offline_mode": False,
                "debug_mode": False,
            }
            with open(config_file, "w") as f:
                json.dump(initial_config, f)

            # Load it
            manager = ConfigManager(config_dir=Path(tmpdir))
            assert manager.get_current_provider() is not None
            assert manager.get_current_provider().name == "existing"

    def test_handles_corrupted_config(self):
        """Test that ConfigManager handles corrupted config.json gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create corrupted config
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, "w") as f:
                f.write("{ invalid json }")

            # Should return default config instead of crashing
            manager = ConfigManager(config_dir=Path(tmpdir))
            assert manager.list_providers() == []


class TestConfigManagerProviderOperations:
    """Test provider CRUD operations."""

    @pytest.fixture
    def temp_manager(self):
        """Fixture providing a ConfigManager with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ConfigManager(config_dir=Path(tmpdir))

    def test_set_and_get_provider(self, temp_manager):
        """Test setting and retrieving a provider."""
        provider = AIProvider(
            name="test",
            api_key="sk-test",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
        )
        temp_manager.set_provider("test", provider)

        retrieved = temp_manager.get_provider("test")
        assert retrieved is not None
        assert retrieved.name == "test"
        assert retrieved.model == "gpt-4"

    def test_get_nonexistent_provider(self, temp_manager):
        """Test getting a provider that doesn't exist returns None."""
        result = temp_manager.get_provider("nonexistent")
        assert result is None

    def test_set_provider_persists_to_disk(self, temp_manager):
        """Test that setting a provider saves to disk immediately."""
        provider = AIProvider(
            name="persist-test",
            api_key="sk-persist",
            endpoint="https://api.com",
        )
        temp_manager.set_provider("persist-test", provider)

        # Read file directly to verify
        config_file = temp_manager.config_file
        with open(config_file, "r") as f:
            data = json.load(f)
        assert "persist-test" in data["providers"]
        assert data["providers"]["persist-test"]["name"] == "persist-test"

    def test_set_current_provider(self, temp_manager):
        """Test setting the current provider."""
        provider = AIProvider(
            name="current",
            api_key="sk-current",
            endpoint="https://api.com",
        )
        temp_manager.set_provider("current", provider)
        temp_manager.set_current_provider("current")

        current = temp_manager.get_current_provider()
        assert current is not None
        assert current.name == "current"

    def test_set_current_provider_nonexistent_raises_error(self, temp_manager):
        """Test that setting nonexistent provider as current raises error."""
        with pytest.raises(ValueError, match="not found"):
            temp_manager.set_current_provider("nonexistent")

    def test_get_current_provider_none_initially(self, temp_manager):
        """Test that current provider is None initially."""
        current = temp_manager.get_current_provider()
        assert current is None

    def test_list_providers_empty(self, temp_manager):
        """Test listing providers when none exist."""
        providers = temp_manager.list_providers()
        assert providers == []

    def test_list_providers_multiple(self, temp_manager):
        """Test listing multiple providers."""
        provider1 = AIProvider(name="p1", api_key="sk-1", endpoint="https://api1.com")
        provider2 = AIProvider(name="p2", api_key="sk-2", endpoint="https://api2.com")
        provider3 = AIProvider(name="p3", api_key="sk-3", endpoint="https://api3.com")
        temp_manager.set_provider("p1", provider1)
        temp_manager.set_provider("p2", provider2)
        temp_manager.set_provider("p3", provider3)

        providers = temp_manager.list_providers()
        assert set(providers) == {"p1", "p2", "p3"}

    def test_has_provider(self, temp_manager):
        """Test checking provider existence."""
        provider = AIProvider(name="exists", api_key="sk-test", endpoint="https://api.com")
        temp_manager.set_provider("exists", provider)

        assert temp_manager.has_provider("exists") is True
        assert temp_manager.has_provider("missing") is False

    def test_delete_provider(self, temp_manager):
        """Test deleting a provider."""
        provider = AIProvider(name="delete-me", api_key="sk-test", endpoint="https://api.com")
        temp_manager.set_provider("delete-me", provider)
        assert temp_manager.has_provider("delete-me")

        temp_manager.delete_provider("delete-me")
        assert not temp_manager.has_provider("delete-me")

    def test_delete_provider_persists(self, temp_manager):
        """Test that deleting provider persists to disk."""
        provider = AIProvider(name="delete-persist", api_key="sk-test", endpoint="https://api.com")
        temp_manager.set_provider("delete-persist", provider)
        temp_manager.delete_provider("delete-persist")

        # Read file directly
        with open(temp_manager.config_file, "r") as f:
            data = json.load(f)
        assert "delete-persist" not in data["providers"]

    def test_delete_current_provider_clears_current(self, temp_manager):
        """Test that deleting current provider clears current_provider."""
        provider = AIProvider(
            name="current",
            api_key="sk-test",
            endpoint="https://api.com",
        )
        temp_manager.set_provider("current", provider)
        temp_manager.set_current_provider("current")
        assert temp_manager.get_current_provider() is not None

        temp_manager.delete_provider("current")
        assert temp_manager.get_current_provider() is None


class TestConfigManagerConfigOperations:
    """Test overall config operations."""

    @pytest.fixture
    def temp_manager(self):
        """Fixture providing a ConfigManager with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ConfigManager(config_dir=Path(tmpdir))

    def test_get_config(self, temp_manager):
        """Test getting the AppConfig object."""
        config = temp_manager.get_config()
        assert isinstance(config, AppConfig)
        assert config.current_provider == ""

    def test_set_config(self, temp_manager):
        """Test replacing the entire config."""
        new_config = AppConfig(current_provider="new")
        provider = AIProvider(name="new", api_key="sk-new", endpoint="https://api.com")
        new_config.set_provider("new", provider)

        temp_manager.set_config(new_config)
        assert temp_manager.get_current_provider() is not None
        assert temp_manager.get_current_provider().name == "new"

    def test_set_config_persists(self, temp_manager):
        """Test that set_config persists to disk."""
        new_config = AppConfig(current_provider="persist-config")
        provider = AIProvider(name="persist-config", api_key="sk-test", endpoint="https://api.com")
        new_config.set_provider("persist-config", provider)

        temp_manager.set_config(new_config)

        # Verify by loading fresh manager
        manager2 = ConfigManager(config_dir=temp_manager.config_dir)
        assert manager2.get_current_provider() is not None
        assert manager2.get_current_provider().name == "persist-config"

    def test_reset_config(self, temp_manager):
        """Test resetting configuration to defaults."""
        provider = AIProvider(name="to-reset", api_key="sk-test", endpoint="https://api.com")
        temp_manager.set_provider("to-reset", provider)
        assert temp_manager.has_provider("to-reset")

        temp_manager.reset_config()
        assert temp_manager.list_providers() == []
        assert temp_manager.get_current_provider() is None

    def test_reset_config_persists(self, temp_manager):
        """Test that reset_config persists to disk."""
        provider = AIProvider(name="to-reset", api_key="sk-test", endpoint="https://api.com")
        temp_manager.set_provider("to-reset", provider)
        temp_manager.reset_config()

        # Verify by loading fresh manager
        manager2 = ConfigManager(config_dir=temp_manager.config_dir)
        assert manager2.list_providers() == []

    def test_save_config_explicit(self, temp_manager):
        """Test explicitly saving config."""
        config = temp_manager.get_config()
        config.debug_mode = True

        temp_manager.save_config()

        # Verify persistence
        manager2 = ConfigManager(config_dir=temp_manager.config_dir)
        assert manager2.get_config().debug_mode is True


class TestConfigManagerPersistence:
    """Test configuration persistence across instances."""

    def test_persistence_across_instances(self):
        """Test that configuration persists across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and populate first manager
            manager1 = ConfigManager(config_dir=Path(tmpdir))
            provider = AIProvider(
                name="persistent",
                api_key="sk-persist",
                endpoint="https://api.openai.com/v1",
                model="gpt-4",
                temperature=0.8,
            )
            manager1.set_provider("persistent", provider)
            manager1.set_current_provider("persistent")

            # Create new manager with same directory
            manager2 = ConfigManager(config_dir=Path(tmpdir))

            # Verify data persisted
            assert manager2.has_provider("persistent")
            current = manager2.get_current_provider()
            assert current is not None
            assert current.name == "persistent"
            assert current.model == "gpt-4"
            assert current.temperature == 0.8

    def test_multiple_providers_persistence(self):
        """Test persistence of multiple providers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = ConfigManager(config_dir=Path(tmpdir))

            # Add multiple providers
            for i in range(1, 4):
                provider = AIProvider(
                    name=f"provider-{i}",
                    api_key=f"sk-{i}",
                    endpoint=f"https://api{i}.com",
                )
                manager1.set_provider(f"provider-{i}", provider)

            # Create new manager and verify all persisted
            manager2 = ConfigManager(config_dir=Path(tmpdir))
            providers = manager2.list_providers()
            assert len(providers) == 3
            assert all(p in providers for p in ["provider-1", "provider-2", "provider-3"])

    def test_config_file_format(self):
        """Test that config.json has expected format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            provider = AIProvider(
                name="format-test",
                api_key="sk-format",
                endpoint="https://api.com",
                model="model-x",
                temperature=0.5,
                max_tokens=1000,
            )
            manager.set_provider("format-test", provider)
            manager.set_current_provider("format-test")

            # Read and check format
            config_file = Path(tmpdir) / "config.json"
            with open(config_file, "r") as f:
                data = json.load(f)

            # Verify structure
            assert "current_provider" in data
            assert "providers" in data
            assert "default_model" in data
            assert "default_temperature" in data
            assert "offline_mode" in data
            assert "debug_mode" in data

            # Verify provider structure
            provider_data = data["providers"]["format-test"]
            assert provider_data["name"] == "format-test"
            assert provider_data["api_key"] == "sk-format"
            assert provider_data["model"] == "model-x"
            assert provider_data["temperature"] == 0.5
            assert provider_data["max_tokens"] == 1000


class TestConfigManagerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def temp_manager(self):
        """Fixture providing a ConfigManager with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ConfigManager(config_dir=Path(tmpdir))

    def test_provider_with_none_fields(self, temp_manager):
        """Test handling provider with None optional fields."""
        provider = AIProvider(
            name="minimal",
            api_key="sk-minimal",
            endpoint="https://api.com",
            model=None,
            max_tokens=None,
            headers=None,
        )
        temp_manager.set_provider("minimal", provider)

        retrieved = temp_manager.get_provider("minimal")
        assert retrieved is not None
        assert retrieved.model is None
        assert retrieved.max_tokens is None
        assert retrieved.headers is None

    def test_provider_with_custom_headers(self, temp_manager):
        """Test provider with custom headers."""
        provider = AIProvider(
            name="headers-test",
            api_key="sk-test",
            endpoint="https://api.com",
            headers={"X-Custom": "value", "Authorization": "Bearer token"},
        )
        temp_manager.set_provider("headers-test", provider)

        retrieved = temp_manager.get_provider("headers-test")
        assert retrieved.headers == {"X-Custom": "value", "Authorization": "Bearer token"}

    def test_delete_nonexistent_provider_silent(self, temp_manager):
        """Test that deleting nonexistent provider is silent."""
        # Should not raise error
        temp_manager.delete_provider("does-not-exist")
        assert not temp_manager.has_provider("does-not-exist")

    def test_provider_name_case_sensitive(self, temp_manager):
        """Test that provider names are case-sensitive."""
        provider = AIProvider(
            name="CaseSensitive",
            api_key="sk-test",
            endpoint="https://api.com",
        )
        temp_manager.set_provider("CaseSensitive", provider)

        assert temp_manager.has_provider("CaseSensitive") is True
        assert temp_manager.has_provider("casesensitive") is False
