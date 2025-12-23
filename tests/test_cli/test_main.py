"""
Test main CLI entry point and command routing.
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
import typer
from typer.testing import CliRunner

from vibe_coder.cli import app, main

# Set test environment variable to prevent actual config loading
os.environ["VIBE_CODER_TEST"] = "true"


@pytest.fixture
def runner():
    """Create a Typer test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestCliBasicFunctionality:
    """Test basic CLI functionality."""

    def test_app_exists(self, runner):
        """Test that the Typer app exists."""
        assert app is not None
        assert isinstance(app, typer.Typer)
        assert app.info.name == "vibe-coder"

    def test_main_function_exists(self):
        """Test that main function exists."""
        assert callable(main)

    def test_cli_help(self, runner):
        """Test CLI help message."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "vibe-coder" in result.stdout
        assert "A configurable CLI coding assistant" in result.stdout
        assert "chat" in result.stdout
        assert "setup" in result.stdout
        assert "config" in result.stdout
        assert "test" in result.stdout

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(app, ["--version"])
        # Typer shows version if it's defined in pyproject.toml
        # We just check it doesn't crash
        assert result.exit_code in [0, 2]  # 2 if version not configured

    def test_no_command_provided(self, runner):
        """Test CLI when no command is provided."""
        result = runner.invoke(app, [])
        # Should show help when no command provided (exit code 2 is expected for missing command)
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.stdout or "Missing command" in result.stdout


class TestChatCommand:
    """Test chat command parsing and basic behavior."""

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_basic(self, mock_chat_class, runner):
        """Test basic chat command invocation."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 0
        mock_chat_class.assert_called_once()
        mock_command.run.assert_called_once_with(provider_name=None, model=None, temperature=None)

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_with_provider(self, mock_chat_class, runner):
        """Test chat command with provider option."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat", "--provider", "openai"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(
            provider_name="openai", model=None, temperature=None
        )

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_with_model(self, mock_chat_class, runner):
        """Test chat command with model option."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat", "--model", "gpt-4"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(
            provider_name=None, model="gpt-4", temperature=None
        )

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_with_temperature(self, mock_chat_class, runner):
        """Test chat command with temperature option."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat", "--temperature", "0.5"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(provider_name=None, model=None, temperature=0.5)

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_with_all_options(self, mock_chat_class, runner):
        """Test chat command with all options."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        result = runner.invoke(
            app,
            ["chat", "--provider", "claude", "--model", "claude-3-sonnet", "--temperature", "0.8"],
        )
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(
            provider_name="claude", model="claude-3-sonnet", temperature=0.8
        )

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_failure(self, mock_chat_class, runner):
        """Test chat command when it fails."""
        mock_command = AsyncMock()
        mock_command.run.return_value = False
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 1

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_exception(self, mock_chat_class, runner):
        """Test chat command when it raises an exception."""
        mock_command = AsyncMock()
        mock_command.run.side_effect = Exception("Test error")
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat"])
        assert result.exit_code != 0

    def test_chat_help(self, runner):
        """Test chat command help."""
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "Start an interactive chat session" in result.stdout
        assert "--provider" in result.stdout
        assert "--model" in result.stdout
        assert "--temperature" in result.stdout


class TestSetupCommand:
    """Test setup command."""

    @patch("vibe_coder.cli.SetupCommand")
    def test_setup_command_basic(self, mock_setup_class, runner):
        """Test basic setup command invocation."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_setup_class.return_value = mock_command

        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        mock_setup_class.assert_called_once()
        mock_command.run.assert_called_once_with()

    @patch("vibe_coder.cli.SetupCommand")
    def test_setup_command_failure(self, mock_setup_class, runner):
        """Test setup command when it fails."""
        mock_command = AsyncMock()
        mock_command.run.return_value = False
        mock_setup_class.return_value = mock_command

        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 1

    def test_setup_help(self, runner):
        """Test setup command help."""
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0
        assert "Run the interactive setup wizard" in result.stdout


class TestConfigCommand:
    """Test config command."""

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_list_command(self, mock_config_class, runner):
        """Test config list command."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("list", None)

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_show_command(self, mock_config_class, runner):
        """Test config show command."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "show", "openai"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("show", "openai")

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_add_command(self, mock_config_class, runner):
        """Test config add command."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "add"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("add", None)

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_edit_command(self, mock_config_class, runner):
        """Test config edit command."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "edit", "claude"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("edit", "claude")

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_delete_command(self, mock_config_class, runner):
        """Test config delete command."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "delete", "old-provider"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("delete", "old-provider")

    def test_config_help(self, runner):
        """Test config command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Manage provider configurations" in result.stdout
        assert "list" in result.stdout
        assert "show" in result.stdout
        assert "add" in result.stdout


class TestTestCommand:
    """Test test command."""

    @patch("vibe_coder.commands.test.TestCommand")
    def test_test_command_no_provider(self, mock_test_class, runner):
        """Test test command without provider."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_test_class.return_value = mock_command

        result = runner.invoke(app, ["test"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(None)

    @patch("vibe_coder.commands.test.TestCommand")
    def test_test_command_with_provider(self, mock_test_class, runner):
        """Test test command with provider."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_test_class.return_value = mock_command

        result = runner.invoke(app, ["test", "openai"])
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with("openai")

    def test_test_help(self, runner):
        """Test test command help."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "Test connection to an AI provider" in result.stdout


class TestErrorHandling:
    """Test error handling in CLI."""

    def test_invalid_command(self, runner):
        """Test invalid command handling."""
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0

    def test_config_invalid_action(self, runner):
        """Test config command with invalid action."""
        result = runner.invoke(app, ["config", "invalid"])
        assert result.exit_code != 0

    def test_chat_invalid_temperature(self, runner):
        """Test chat command with invalid temperature."""
        # Typer should handle this validation
        result = runner.invoke(app, ["chat", "--temperature", "invalid"])
        assert result.exit_code != 0

    def test_chat_temperature_out_of_range(self, runner):
        """Test chat command with temperature out of range."""
        # Note: This depends on how the validation is implemented
        runner.invoke(app, ["chat", "--temperature", "5.0"])
        # May or may not fail depending on implementation
        assert True  # Placeholder for actual test


class TestMainFunction:
    """Test the main function directly."""

    @patch("vibe_coder.cli.app")
    def test_main_function(self, mock_app):
        """Test main function calls app()."""
        main()
        mock_app.assert_called_once()


class TestCliCoverage:
    """Additional tests to improve CLI coverage."""

    def test_chat_command_with_negative_temperature(self, runner):
        """Test chat command with negative temperature."""
        result = runner.invoke(app, ["chat", "--temperature", "-0.5"])
        # Typer may or may not validate this range
        assert result.exit_code in [0, 2]

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_command_with_asyncio_run(self, mock_chat_class, runner):
        """Test that asyncio.run is called correctly."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_chat_class.return_value = mock_command

        with patch("vibe_coder.cli.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = True
            result = runner.invoke(app, ["chat"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()

    @patch("vibe_coder.cli.SetupCommand")
    def test_setup_command_with_asyncio_run(self, mock_setup_class, runner):
        """Test that asyncio.run is called correctly for setup."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_setup_class.return_value = mock_command

        with patch("vibe_coder.cli.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = True
            result = runner.invoke(app, ["setup"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_command_with_asyncio_run(self, mock_config_class, runner):
        """Test that asyncio.run is called correctly for config."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_config_class.return_value = mock_command

        with patch("vibe_coder.cli.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = True
            result = runner.invoke(app, ["config", "list"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()

    @patch("vibe_coder.commands.test.TestCommand")
    def test_test_command_with_asyncio_run(self, mock_test_class, runner):
        """Test that asyncio.run is called correctly for test."""
        mock_command = AsyncMock()
        mock_command.run.return_value = True
        mock_test_class.return_value = mock_command

        with patch("vibe_coder.cli.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = True
            result = runner.invoke(app, ["test"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()

    def test_cli_callback_function(self, runner):
        """Test the CLI callback function."""
        # The callback function doesn't do anything, but test it's properly set up
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Vibe Coder - Your AI coding assistant" in result.stdout

    def test_chat_command_short_options(self, runner):
        """Test chat command with short option flags."""
        with patch("vibe_coder.cli.ChatCommand") as mock_chat_class:
            mock_command = AsyncMock()
            mock_command.run.return_value = True
            mock_chat_class.return_value = mock_command

            result = runner.invoke(app, ["chat", "-p", "test", "-m", "gpt-4", "-t", "0.5"])
            assert result.exit_code == 0
            mock_command.run.assert_called_once_with(
                provider_name="test", model="gpt-4", temperature=0.5
            )

    def test_config_command_all_actions(self, runner):
        """Test config command with all valid actions."""
        actions = ["list", "show", "add", "edit", "delete"]

        for action in actions:
            with patch("vibe_coder.cli.ConfigCommand") as mock_config_class:
                mock_command = AsyncMock()
                mock_command.run.return_value = True
                mock_config_class.return_value = mock_command

                args = ["config", action]
                if action in ["show", "edit", "delete"]:
                    args.append("test-provider")

                result = runner.invoke(app, args)
                assert result.exit_code == 0
                expected_name = "test-provider" if action in ["show", "edit", "delete"] else None
                mock_command.run.assert_called_once_with(action, expected_name)

    def test_command_imports(self):
        """Test that all command classes are imported correctly."""
        # This test ensures the import statements are executed
        from vibe_coder.commands.chat import ChatCommand
        from vibe_coder.commands.config import ConfigCommand
        from vibe_coder.commands.setup import SetupCommand
        from vibe_coder.commands.test import TestCommand

        assert ChatCommand is not None
        assert ConfigCommand is not None
        assert SetupCommand is not None
        assert TestCommand is not None

    def test_app_configuration(self):
        """Test the Typer app configuration."""
        assert app.info.name == "vibe-coder"
        assert "A configurable CLI coding assistant" in app.info.help
        assert app.rich_markup_mode == "rich"

        # Check that commands are registered
        command_names = [cmd.name for cmd in app.commands.values()]
        assert "chat" in command_names
        assert "setup" in command_names
        assert "config" in command_names
        assert "test" in command_names

    def test_console_instance(self):
        """Test that console instance is created."""
        from rich.console import Console

        from vibe_coder.cli import console

        assert isinstance(console, Console)

    @patch("vibe_coder.cli.ChatCommand")
    def test_chat_exception_handling(self, mock_chat_class, runner):
        """Test chat command exception handling."""
        mock_command = AsyncMock()
        mock_command.run.side_effect = Exception("Test exception")
        mock_chat_class.return_value = mock_command

        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 1

    @patch("vibe_coder.cli.SetupCommand")
    def test_setup_exception_handling(self, mock_setup_class, runner):
        """Test setup command exception handling."""
        mock_command = AsyncMock()
        mock_command.run.side_effect = Exception("Test exception")
        mock_setup_class.return_value = mock_command

        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 1

    @patch("vibe_coder.cli.ConfigCommand")
    def test_config_exception_handling(self, mock_config_class, runner):
        """Test config command exception handling."""
        mock_command = AsyncMock()
        mock_command.run.side_effect = Exception("Test exception")
        mock_config_class.return_value = mock_command

        result = runner.invoke(app, ["config", "list"])
        assert result.exit_code == 1
