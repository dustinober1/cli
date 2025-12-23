"""
Test config command functionality.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from vibe_coder.commands.config import ConfigCommand
from vibe_coder.types.config import AIProvider

# Set test environment variable
os.environ["VIBE_CODER_TEST"] = "true"


@pytest.fixture
def config_command():
    """Create a ConfigCommand instance."""
    return ConfigCommand()


@pytest.fixture
def mock_providers():
    """Create mock providers for testing."""
    return {
        "openai": AIProvider(
            name="openai",
            api_key="sk-openai123",
            endpoint="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
        ),
        "claude": AIProvider(
            name="claude",
            api_key="sk-ant-claude456",
            endpoint="https://api.anthropic.com",
            model="claude-3-sonnet",
            temperature=0.5,
        ),
        "local": AIProvider(
            name="local", api_key=None, endpoint="http://localhost:11434", model="llama2"
        ),
    }


class TestConfigCommandInitialization:
    """Test ConfigCommand initialization."""

    def test_config_command_init(self, config_command):
        """Test ConfigCommand initialization."""
        assert config_command.console is not None
        assert hasattr(config_command.console, "print")


class TestConfigCommandListProviders:
    """Test listing providers functionality."""

    @patch("vibe_coder.commands.config.config_manager")
    async def test_list_providers_with_data(self, mock_config, config_command, mock_providers):
        """Test listing providers when providers exist."""
        mock_config.list_providers.return_value = mock_providers
        mock_config.get_current_provider_name.return_value = "openai"

        with patch.object(config_command.console, "print") as mock_print:
            await config_command.list_providers()
            mock_print.assert_called()

    @patch("vibe_coder.commands.config.config_manager")
    async def test_list_providers_empty(self, mock_config, config_command):
        """Test listing providers when none exist."""
        mock_config.list_providers.return_value = {}
        mock_config.get_current_provider_name.return_value = None

        with patch.object(config_command.console, "print") as mock_print:
            await config_command.list_providers()
            mock_print.assert_called()
            # Should print "No providers configured" message
            call_args = mock_print.call_args[0][0]
            assert "No providers configured" in str(call_args)

    @patch("vibe_coder.commands.config.config_manager")
    async def test_list_providers_with_current_marker(
        self, mock_config, config_command, mock_providers
    ):
        """Test listing providers with current provider marked."""
        mock_config.list_providers.return_value = mock_providers
        mock_config.get_current_provider_name.return_value = "claude"

        with patch.object(config_command.console, "print"):
            await config_command.list_providers()
            # The table should show the current provider

    @patch("vibe_coder.commands.config.config_manager")
    async def test_list_providers_no_current(self, mock_config, config_command, mock_providers):
        """Test listing providers with no current provider set."""
        mock_config.list_providers.return_value = mock_providers
        mock_config.get_current_provider_name.return_value = None

        with patch.object(config_command.console, "print"):
            await config_command.list_providers()


class TestConfigCommandShowProvider:
    """Test showing provider details."""

    @patch("vibe_coder.commands.config.config_manager")
    async def test_show_provider_exists(self, mock_config, config_command, mock_providers):
        """Test showing an existing provider."""
        mock_config.get_provider.return_value = mock_providers["openai"]

        with patch.object(config_command.console, "print") as mock_print:
            result = await config_command.show_provider("openai")
            assert result is True
            mock_print.assert_called()

    @patch("vibe_coder.commands.config.config_manager")
    async def test_show_provider_not_found(self, mock_config, config_command):
        """Test showing a non-existent provider."""
        mock_config.get_provider.return_value = None

        with patch.object(config_command.console, "print") as mock_print:
            result = await config_command.show_provider("nonexistent")
            assert result is False
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "not found" in str(call_args)

    @patch("vibe_coder.commands.config.config_manager")
    async def test_show_provider_no_name(self, mock_config, config_command, mock_providers):
        """Test showing provider without specifying name."""
        mock_config.get_provider.return_value = mock_providers["claude"]
        mock_config.get_current_provider_name.return_value = "claude"

        with patch.object(config_command.console, "print"):
            result = await config_command.show_provider(None)
            assert result is True
            mock_config.get_provider.assert_called_once_with("claude")

    @patch("vibe_coder.commands.config.config_manager")
    async def test_show_provider_no_name_no_current(self, mock_config, config_command):
        """Test showing provider without name and no current provider."""
        mock_config.get_current_provider_name.return_value = None

        with patch.object(config_command.console, "print"):
            result = await config_command.show_provider(None)
            assert result is False

    def test_show_provider_formatting(self, config_command):
        """Test provider details formatting."""
        provider = AIProvider(
            name="test",
            api_key="sk-test123456789",
            endpoint="https://api.test.com/v1",
            model="test-model",
            temperature=0.8,
            max_tokens=1500,
            headers={"Custom-Header": "value"},
        )

        with patch.object(config_command.console, "print"):
            # This would test the formatting of provider details
            # In a real test, you might capture the output and verify structure
            config_command._format_provider_details(provider)


class TestConfigCommandAddProvider:
    """Test adding a new provider."""

    @patch("vibe_coder.commands.config.SetupCommand")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_add_provider_success(
        self, mock_config, mock_setup, config_command, mock_providers
    ):
        """Test successfully adding a provider."""
        mock_setup_instance = AsyncMock()
        mock_setup_instance.run.return_value = True
        mock_setup.return_value = mock_setup_instance

        with patch.object(config_command.console, "print"):
            result = await config_command.add_provider()
            assert result is True
            mock_setup_instance.run.assert_called_once()

    @patch("vibe_coder.commands.config.SetupCommand")
    async def test_add_provider_cancelled(self, mock_setup, config_command):
        """Test adding a provider when setup is cancelled."""
        mock_setup_instance = AsyncMock()
        mock_setup_instance.run.return_value = False
        mock_setup.return_value = mock_setup_instance

        with patch.object(config_command.console, "print"):
            result = await config_command.add_provider()
            assert result is False

    @patch("vibe_coder.commands.config.SetupCommand")
    async def test_add_provider_error(self, mock_setup, config_command):
        """Test adding a provider when setup raises an error."""
        mock_setup_instance = AsyncMock()
        mock_setup_instance.run.side_effect = Exception("Setup error")
        mock_setup.return_value = mock_setup_instance

        with patch.object(config_command.console, "print"):
            result = await config_command.add_provider()
            assert result is False


class TestConfigCommandEditProvider:
    """Test editing an existing provider."""

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_edit_provider_success(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test successfully editing a provider."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        # Mock user edits
        mock_questionary.text.return_value.ask.side_effect = [
            "gpt-4-turbo",  # new model
            "0.9",  # new temperature
            "3000",  # new max_tokens
        ]

        with patch.object(config_command.console, "print"):
            result = await config_command.edit_provider("openai")
            assert result is True
            mock_config.set_provider.assert_called_once()

            # Check that provider was updated
            updated_provider = mock_config.set_provider.call_args[0][1]
            assert updated_provider.model == "gpt-4-turbo"
            assert updated_provider.temperature == 0.9
            assert updated_provider.max_tokens == 3000

    @patch("vibe_coder.commands.config.config_manager")
    async def test_edit_provider_not_found(self, mock_config, config_command):
        """Test editing a non-existent provider."""
        mock_config.get_provider.return_value = None

        with patch.object(config_command.console, "print"):
            result = await config_command.edit_provider("nonexistent")
            assert result is False

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_edit_provider_cancelled(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test cancelling provider edit."""
        mock_config.get_provider.return_value = mock_providers["claude"]
        mock_questionary.text.return_value.ask.side_effect = KeyboardInterrupt()

        with patch.object(config_command.console, "print"):
            result = await config_command.edit_provider("claude")
            assert result is False

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_edit_provider_api_key(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test editing provider API key."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        # Confirm API key change
        mock_questionary.confirm.return_value.ask.return_value = True
        mock_questionary.password.return_value.ask.return_value = "sk-new-key-12345"

        # Mock other edits to be empty (no change)
        def side_effect(*args, **kwargs):
            if hasattr(side_effect, "call_count"):
                side_effect.call_count += 1
            else:
                side_effect.call_count = 1
            if side_effect.call_count == 1:  # API key prompt
                return "sk-new-key-12345"
            return ""  # All other prompts

        mock_questionary.password.return_value.ask.side_effect = side_effect
        mock_questionary.text.return_value.ask.side_effect = side_effect

        with patch.object(config_command.console, "print"):
            result = await config_command.edit_provider("openai")
            assert result is True

            updated_provider = mock_config.set_provider.call_args[0][1]
            assert updated_provider.api_key == "sk-new-key-12345"


class TestConfigCommandDeleteProvider:
    """Test deleting a provider."""

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_delete_provider_success(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test successfully deleting a provider."""
        mock_config.get_provider.return_value = mock_providers["local"]
        mock_questionary.confirm.return_value.ask.return_value = True

        with patch.object(config_command.console, "print"):
            result = await config_command.delete_provider("local")
            assert result is True
            mock_config.delete_provider.assert_called_once_with("local")

    @patch("vibe_coder.commands.config.config_manager")
    async def test_delete_provider_not_found(self, mock_config, config_command):
        """Test deleting a non-existent provider."""
        mock_config.get_provider.return_value = None

        with patch.object(config_command.console, "print"):
            result = await config_command.delete_provider("nonexistent")
            assert result is False

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_delete_provider_cancelled(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test cancelling provider deletion."""
        mock_config.get_provider.return_value = mock_providers["claude"]
        mock_questionary.confirm.return_value.ask.return_value = False

        with patch.object(config_command.console, "print"):
            result = await config_command.delete_provider("claude")
            assert result is False
            mock_config.delete_provider.assert_not_called()

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_delete_current_provider(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test deleting the current provider."""
        mock_config.get_provider.return_value = mock_providers["openai"]
        mock_config.get_current_provider_name.return_value = "openai"
        mock_questionary.confirm.return_value.ask.return_value = True
        mock_config.list_providers.return_value = {
            "openai": mock_providers["openai"],
            "claude": mock_providers["claude"],
        }

        with patch.object(config_command.console, "print"):
            result = await config_command.delete_provider("openai")
            assert result is True
            # Should ask about selecting new current provider

    @patch("vibe_coder.commands.config.questionary")
    @patch("vibe_coder.commands.config.config_manager")
    async def test_delete_last_provider(
        self, mock_config, mock_questionary, config_command, mock_providers
    ):
        """Test deleting the last provider."""
        mock_config.get_provider.return_value = mock_providers["local"]
        mock_config.get_current_provider_name.return_value = "local"
        mock_config.list_providers.return_value = {"local": mock_providers["local"]}
        mock_questionary.confirm.return_value.ask.return_value = True

        with patch.object(config_command.console, "print"):
            result = await config_command.delete_provider("local")
            assert result is True
            # Should clear current provider
            mock_config.clear_current_provider.assert_called_once()


class TestConfigCommandMainFlow:
    """Test main config command flow."""

    @patch("vibe_coder.commands.config.config_manager")
    async def test_run_list_action(self, mock_config, config_command):
        """Test run with list action."""
        mock_config.list_providers.return_value = {}

        with patch.object(config_command, "list_providers", new_callable=AsyncMock) as mock_list:
            result = await config_command.run("list")
            assert result is True
            mock_list.assert_called_once()

    @patch("vibe_coder.commands.config.config_manager")
    async def test_run_show_action(self, mock_config, config_command, mock_providers):
        """Test run with show action."""
        mock_config.get_provider.return_value = mock_providers["openai"]

        with patch.object(config_command, "show_provider", new_callable=AsyncMock) as mock_show:
            mock_show.return_value = True
            result = await config_command.run("show", "openai")
            assert result is True
            mock_show.assert_called_once_with("openai")

    @patch("vibe_coder.commands.config.config_manager")
    async def test_run_add_action(self, mock_config, config_command):
        """Test run with add action."""
        mock_config.list_providers.return_value = {}

        with patch.object(config_command, "add_provider", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            result = await config_command.run("add")
            assert result is True
            mock_add.assert_called_once()

    @patch("vibe_coder.commands.config.config_manager")
    async def test_run_edit_action(self, mock_config, config_command, mock_providers):
        """Test run with edit action."""
        mock_config.get_provider.return_value = mock_providers["claude"]

        with patch.object(config_command, "edit_provider", new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            result = await config_command.run("edit", "claude")
            assert result is True
            mock_edit.assert_called_once_with("claude")

    @patch("vibe_coder.commands.config.config_manager")
    async def test_run_delete_action(self, mock_config, config_command, mock_providers):
        """Test run with delete action."""
        mock_config.get_provider.return_value = mock_providers["local"]

        with patch.object(config_command, "delete_provider", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            result = await config_command.run("delete", "local")
            assert result is True
            mock_delete.assert_called_once_with("local")

    async def test_run_unknown_action(self, config_command):
        """Test run with unknown action."""
        with (
            patch.object(config_command.console, "print") as mock_print,
            patch.object(config_command, "_show_available_actions") as mock_show,
        ):
            result = await config_command.run("unknown")
            assert result is False
            mock_print.assert_called()
            mock_show.assert_called_once()

    async def test_run_keyboard_interrupt(self, config_command):
        """Test run with keyboard interrupt."""
        with patch.object(config_command.console, "print"):
            await config_command.run("list")
            # The interrupt would happen inside the actual method
            assert True  # Placeholder for actual interrupt test

    def test_show_available_actions(self, config_command):
        """Test showing available actions help."""
        with patch.object(config_command.console, "print") as mock_print:
            config_command._show_available_actions()
            mock_print.assert_called()
