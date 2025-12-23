"""
Test setup command functionality.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.commands.setup import SetupCommand
from vibe_coder.types.config import AIProvider

# Set test environment variable
os.environ["VIBE_CODER_TEST"] = "true"


@pytest.fixture
def setup_command():
    """Create a SetupCommand instance."""
    return SetupCommand()


@pytest.fixture
def mock_provider():
    """Create a mock AI provider."""
    return AIProvider(
        name="test-openai",
        api_key="sk-test123456789",
        endpoint="https://api.openai.com/v1",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=2000,
    )


class TestSetupCommandInitialization:
    """Test SetupCommand initialization."""

    def test_setup_command_init(self, setup_command):
        """Test SetupCommand initialization."""
        assert setup_command.console is not None
        # Console should be a Rich Console instance
        assert hasattr(setup_command.console, "print")


class TestSetupCommandExistingConfig:
    """Test existing configuration checking."""

    @patch("vibe_coder.commands.setup.config_manager")
    async def test_check_existing_config_has_providers(self, mock_config, setup_command):
        """Test checking existing config with providers."""
        mock_config.list_providers.return_value = {"openai": MagicMock(), "claude": MagicMock()}

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._check_existing_config()
            assert result is True
            # Should print existing providers
            mock_print.assert_called()

    @patch("vibe_coder.commands.setup.config_manager")
    async def test_check_existing_config_no_providers(self, mock_config, setup_command):
        """Test checking existing config with no providers."""
        mock_config.list_providers.return_value = {}

        result = await setup_command._check_existing_config()
        assert result is False

    @patch("vibe_coder.commands.setup.questionary")
    @patch("vibe_coder.commands.setup.config_manager")
    async def test_check_existing_config_add_another(
        self, mock_config, mock_questionary, setup_command
    ):
        """Test checking existing config and choosing to add another provider."""
        mock_config.list_providers.return_value = {"openai": MagicMock()}
        mock_questionary.confirm.return_value.ask.return_value = True

        with patch.object(setup_command.console, "print"):
            result = await setup_command._check_existing_config()
            assert result is False  # Should continue with setup

    @patch("vibe_coder.commands.setup.questionary")
    @patch("vibe_coder.commands.setup.config_manager")
    async def test_check_existing_config_skip_setup(
        self, mock_config, mock_questionary, setup_command
    ):
        """Test checking existing config and choosing to skip setup."""
        mock_config.list_providers.return_value = {"openai": MagicMock()}
        mock_questionary.confirm.return_value.ask.return_value = False

        with patch.object(setup_command.console, "print"):
            result = await setup_command._check_existing_config()
            assert result is True  # Should skip setup


class TestSetupCommandProviderSelection:
    """Test provider type selection."""

    @patch("vibe_coder.commands.setup.questionary")
    async def test_select_provider_type_openai(self, mock_questionary, setup_command):
        """Test selecting OpenAI provider."""
        mock_questionary.select.return_value.ask.return_value = "OpenAI"

        result = await setup_command._select_provider_type()
        assert result == "openai"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_select_provider_type_anthropic(self, mock_questionary, setup_command):
        """Test selecting Anthropic provider."""
        mock_questionary.select.return_value.ask.return_value = "Anthropic (Claude)"

        result = await setup_command._select_provider_type()
        assert result == "anthropic"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_select_provider_type_ollama(self, mock_questionary, setup_command):
        """Test selecting Ollama provider."""
        mock_questionary.select.return_value.ask.return_value = "Ollama (Local)"

        result = await setup_command._select_provider_type()
        assert result == "ollama"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_select_provider_type_custom(self, mock_questionary, setup_command):
        """Test selecting custom provider."""
        mock_questionary.select.return_value.ask.return_value = "Custom/OpenAI-Compatible"

        result = await setup_command._select_provider_type()
        assert result == "custom"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_select_provider_type_cancelled(self, mock_questionary, setup_command):
        """Test cancelling provider selection."""
        mock_questionary.select.return_value.ask.return_value = None

        result = await setup_command._select_provider_type()
        assert result is None


class TestSetupCommandOpenAIConfiguration:
    """Test OpenAI provider configuration."""

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_openai_basic(self, mock_questionary, setup_command):
        """Test basic OpenAI configuration."""
        # Mock user inputs
        mock_questionary.text.return_value.ask.side_effect = [
            "my-openai",  # name
            "sk-test1234567890abcdef",  # api_key
            "gpt-4",  # model
            "0.7",  # temperature
            "2000",  # max_tokens
        ]

        result = await setup_command._configure_openai()
        assert isinstance(result, AIProvider)
        assert result.name == "my-openai"
        assert result.api_key == "sk-test1234567890abcdef"
        assert result.endpoint == "https://api.openai.com/v1"  # Default
        assert result.model == "gpt-4"
        assert result.temperature == 0.7
        assert result.max_tokens == 2000

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_openai_with_defaults(self, mock_questionary, setup_command):
        """Test OpenAI configuration with default values."""
        mock_questionary.text.return_value.ask.side_effect = [
            "test-openai",  # name
            "sk-test",  # api_key
            "",  # model (default)
            "",  # temperature (default)
            "",  # max_tokens (default)
        ]

        result = await setup_command._configure_openai()
        assert isinstance(result, AIProvider)
        assert result.name == "test-openai"
        assert result.api_key == "sk-test"
        assert result.model is None
        assert result.temperature == 0.7  # Default
        assert result.max_tokens is None

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_openai_validation_error(self, mock_questionary, setup_command):
        """Test OpenAI configuration with validation error."""
        mock_questionary.text.return_value.ask.side_effect = [
            "test",  # name
            "invalid-key",  # api_key (too short)
        ]

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._configure_openai()
            assert result is None
            # Should print error message
            mock_print.assert_called()
            assert "[red]" in str(mock_print.call_args)


class TestSetupCommandAnthropicConfiguration:
    """Test Anthropic provider configuration."""

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_anthropic_basic(self, mock_questionary, setup_command):
        """Test basic Anthropic configuration."""
        mock_questionary.text.return_value.ask.side_effect = [
            "my-claude",  # name
            "sk-ant-test03",  # api_key
            "claude-3-sonnet-20240229",  # model
            "0.5",  # temperature
            "4000",  # max_tokens
        ]

        result = await setup_command._configure_anthropic()
        assert isinstance(result, AIProvider)
        assert result.name == "my-claude"
        assert result.api_key == "sk-ant-test03"
        assert result.endpoint == "https://api.anthropic.com"  # Default
        assert result.model == "claude-3-sonnet-20240229"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_anthropic_with_defaults(self, mock_questionary, setup_command):
        """Test Anthropic configuration with defaults."""
        mock_questionary.text.return_value.ask.side_effect = [
            "claude",  # name
            "sk-ant-test",  # api_key
            "",  # model (default)
            "",  # temperature (default)
            "",  # max_tokens (default)
        ]

        result = await setup_command._configure_anthropic()
        assert isinstance(result, AIProvider)
        assert result.name == "claude"
        assert result.api_key == "sk-ant-test"
        assert result.model is None
        assert result.temperature == 0.7


class TestSetupCommandOllamaConfiguration:
    """Test Ollama provider configuration."""

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_ollama_basic(self, mock_questionary, setup_command):
        """Test basic Ollama configuration."""
        mock_questionary.text.return_value.ask.side_effect = [
            "local-llama",  # name
            "http://localhost:11434",  # endpoint
            "llama2",  # model
            "0.8",  # temperature
            "2048",  # max_tokens
        ]

        result = await setup_command._configure_ollama()
        assert isinstance(result, AIProvider)
        assert result.name == "local-llama"
        assert result.api_key is None  # No API key for Ollama
        assert result.endpoint == "http://localhost:11434"
        assert result.model == "llama2"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_ollama_default_endpoint(self, mock_questionary, setup_command):
        """Test Ollama configuration with default endpoint."""
        mock_questionary.text.return_value.ask.side_effect = [
            "ollama",  # name
            "",  # endpoint (default)
            "codellama",  # model
            "",  # temperature (default)
            "",  # max_tokens (default)
        ]

        result = await setup_command._configure_ollama()
        assert isinstance(result, AIProvider)
        assert result.endpoint == "http://localhost:11434"  # Default


class TestSetupCommandCustomConfiguration:
    """Test custom provider configuration."""

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_custom_basic(self, mock_questionary, setup_command):
        """Test basic custom provider configuration."""
        mock_questionary.text.return_value.ask.side_effect = [
            "my-custom",  # name
            "https://api.custom.com/v1",  # endpoint
            "custom-key",  # api_key
            "custom-model",  # model
            "0.6",  # temperature
            "1500",  # max_tokens
        ]

        result = await setup_command._configure_custom()
        assert isinstance(result, AIProvider)
        assert result.name == "my-custom"
        assert result.endpoint == "https://api.custom.com/v1"
        assert result.api_key == "custom-key"
        assert result.model == "custom-model"

    @patch("vibe_coder.commands.setup.questionary")
    async def test_configure_custom_no_api_key(self, mock_questionary, setup_command):
        """Test custom provider configuration without API key."""
        mock_questionary.confirm.return_value.ask.return_value = False
        mock_questionary.text.return_value.ask.side_effect = [
            "local-custom",  # name
            "http://localhost:8080",  # endpoint
            "local-model",  # model
            "0.9",  # temperature
            "1024",  # max_tokens
        ]

        result = await setup_command._configure_custom()
        assert isinstance(result, AIProvider)
        assert result.api_key is None


class TestSetupCommandConnectionTest:
    """Test connection testing functionality."""

    @patch("vibe_coder.commands.setup.ClientFactory")
    @patch("vibe_coder.commands.setup.Progress")
    async def test_connection_test_success(
        self, mock_progress, mock_factory, setup_command, mock_provider
    ):
        """Test successful connection test."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._test_connection(mock_provider)
            assert result is True
            # Should print success message
            mock_print.assert_any_call("[green]✓ Connection successful![/green]")

    @patch("vibe_coder.commands.setup.ClientFactory")
    @patch("vibe_coder.commands.setup.Progress")
    async def test_connection_test_failure(
        self, mock_progress, mock_factory, setup_command, mock_provider
    ):
        """Test failed connection test."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = False
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._test_connection(mock_provider)
            assert result is False
            # Should print failure message
            mock_print.assert_any_call("[red]✗ Connection failed![/red]")

    @patch("vibe_coder.commands.setup.questionary")
    @patch("vibe_coder.commands.setup.ClientFactory")
    @patch("vibe_coder.commands.setup.Progress")
    async def test_connection_test_retry(
        self, mock_progress, mock_factory, mock_questionary, setup_command, mock_provider
    ):
        """Test retrying connection test after failure."""
        # First attempt fails, second succeeds
        mock_client = AsyncMock()
        mock_client.validate_connection.side_effect = [False, True]
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        mock_questionary.confirm.return_value.ask.return_value = True

        with patch.object(setup_command.console, "print"):
            result = await setup_command._test_connection(mock_provider)
            assert result is True
            # Should have called validate_connection twice
            assert mock_client.validate_connection.call_count == 2

    @patch("vibe_coder.commands.setup.questionary")
    @patch("vibe_coder.commands.setup.ClientFactory")
    @patch("vibe_coder.commands.setup.Progress")
    async def test_connection_test_skip_retry(
        self, mock_progress, mock_factory, mock_questionary, setup_command, mock_provider
    ):
        """Test skipping retry after connection failure."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = False
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        mock_questionary.confirm.return_value.ask.return_value = False

        with patch.object(setup_command.console, "print"):
            result = await setup_command._test_connection(mock_provider)
            assert result is False


class TestSetupCommandSaveConfiguration:
    """Test configuration saving functionality."""

    @patch("vibe_coder.commands.setup.config_manager")
    @patch("vibe_coder.commands.setup.questionary")
    async def test_save_config_success(
        self, mock_questionary, mock_config, setup_command, mock_provider
    ):
        """Test successful configuration saving."""
        mock_questionary.confirm.return_value.ask.return_value = True

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._save_config(mock_provider)
            assert result is True
            mock_config.set_provider.assert_called_once_with(mock_provider.name, mock_provider)
            mock_print.assert_any_call("[green]✓ Configuration saved successfully![/green]")

    @patch("vibe_coder.commands.setup.questionary")
    async def test_save_config_cancelled(self, mock_questionary, setup_command, mock_provider):
        """Test cancelled configuration saving."""
        mock_questionary.confirm.return_value.ask.return_value = False

        result = await setup_command._save_config(mock_provider)
        assert result is False

    @patch("vibe_coder.commands.setup.config_manager")
    @patch("vibe_coder.commands.setup.questionary")
    async def test_save_config_error(
        self, mock_questionary, mock_config, setup_command, mock_provider
    ):
        """Test configuration saving with error."""
        mock_questionary.confirm.return_value.ask.return_value = True
        mock_config.set_provider.side_effect = Exception("Save failed")

        with patch.object(setup_command.console, "print") as mock_print:
            result = await setup_command._save_config(mock_provider)
            assert result is False
            # Should print error message
            mock_print.assert_any_call("[red]✗ Failed to save configuration: Save failed[/red]")

    @patch("vibe_coder.commands.setup.config_manager")
    @patch("vibe_coder.commands.setup.questionary")
    async def test_save_config_set_as_current(
        self, mock_questionary, mock_config, setup_command, mock_provider
    ):
        """Test saving configuration and setting as current."""
        mock_questionary.confirm.return_value.ask.side_effect = [True, True]
        mock_config.list_providers.return_value = {}  # No existing providers

        with patch.object(setup_command.console, "print"):
            result = await setup_command._save_config(mock_provider)
            assert result is True
            mock_config.set_current_provider.assert_called_once_with(mock_provider.name)


class TestSetupCommandMainFlow:
    """Test main setup flow."""

    @patch("vibe_coder.commands.setup.config_manager")
    async def test_run_success_flow(self, mock_config, setup_command):
        """Test complete successful setup flow."""
        # No existing providers
        mock_config.list_providers.return_value = {}

        with (
            patch.object(
                setup_command, "_check_existing_config", new_callable=AsyncMock
            ) as mock_check,
            patch.object(
                setup_command, "_select_provider_type", new_callable=AsyncMock
            ) as mock_select,
            patch.object(
                setup_command, "_configure_openai", new_callable=AsyncMock
            ) as mock_configure,
            patch.object(setup_command, "_test_connection", new_callable=AsyncMock) as mock_test,
            patch.object(setup_command, "_save_config", new_callable=AsyncMock) as mock_save,
        ):

            mock_check.return_value = False
            mock_select.return_value = "openai"
            mock_configure.return_value = mock_provider
            mock_test.return_value = True
            mock_save.return_value = True

            with patch.object(setup_command.console, "print"):
                result = await setup_command.run()
                assert result is True

    @patch("vibe_coder.commands.setup.config_manager")
    async def test_run_with_existing_config(self, mock_config, setup_command):
        """Test run with existing configuration."""
        mock_config.list_providers.return_value = {"existing": MagicMock()}

        with patch.object(
            setup_command, "_check_existing_config", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = True

            result = await setup_command.run()
            assert result is True

    async def test_run_cancelled_provider_selection(self, setup_command):
        """Test run with cancelled provider selection."""
        with (
            patch.object(
                setup_command, "_check_existing_config", new_callable=AsyncMock
            ) as mock_check,
            patch.object(
                setup_command, "_select_provider_type", new_callable=AsyncMock
            ) as mock_select,
        ):

            mock_check.return_value = False
            mock_select.return_value = None

            with patch.object(setup_command.console, "print"):
                result = await setup_command.run()
                assert result is False

    async def test_run_keyboard_interrupt(self, setup_command):
        """Test run with keyboard interrupt."""
        with patch.object(
            setup_command, "_check_existing_config", new_callable=AsyncMock
        ) as mock_check:
            mock_check.side_effect = KeyboardInterrupt()

            with patch.object(setup_command.console, "print"):
                result = await setup_command.run()
                assert result is False

    async def test_run_general_exception(self, setup_command):
        """Test run with general exception."""
        with patch.object(
            setup_command, "_check_existing_config", new_callable=AsyncMock
        ) as mock_check:
            mock_check.side_effect = Exception("Unexpected error")

            with patch.object(setup_command.console, "print"):
                result = await setup_command.run()
                assert result is False
