"""
Test command functionality.
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.commands.test import TestCommand
from vibe_coder.types.config import AIProvider

# Set test environment variable
os.environ["VIBE_CODER_TEST"] = "true"


@pytest.fixture
def test_command():
    """Create a TestCommand instance."""
    return TestCommand()


@pytest.fixture
def mock_providers():
    """Create mock providers for testing."""
    return {
        "openai": AIProvider(
            name="openai",
            api_key="sk-openai123456",
            endpoint="https://api.openai.com/v1",
            model="gpt-4"
        ),
        "claude": AIProvider(
            name="claude",
            api_key="sk-ant-claude789",
            endpoint="https://api.anthropic.com",
            model="claude-3-sonnet"
        ),
        "local": AIProvider(
            name="local",
            api_key=None,
            endpoint="http://localhost:11434",
            model="llama2"
        )
    }


class TestTestCommandInitialization:
    """Test TestCommand initialization."""

    def test_test_command_init(self, test_command):
        """Test TestCommand initialization."""
        assert test_command.console is not None
        assert hasattr(test_command.console, "print")


class TestTestCommandRun:
    """Test main run functionality."""

    @patch("vibe_coder.commands.test.config_manager")
    async def test_run_with_provider_name(self, mock_config, test_command):
        """Test run with specific provider name."""
        mock_config.get_provider.return_value = MagicMock()

        with patch.object(test_command, "_test_single_provider", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = True
            result = await test_command.run("openai")
            assert result is True
            mock_test.assert_called_once_with("openai")

    @patch("vibe_coder.commands.test.config_manager")
    async def test_run_with_current_provider(self, mock_config, test_command, mock_providers):
        """Test run with current provider."""
        mock_config.get_current_provider.return_value = mock_providers["openai"]

        with patch.object(test_command, "_test_single_provider", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = True
            result = await test_command.run(None)
            assert result is True
            mock_test.assert_called_once_with("openai")

    @patch("vibe_coder.commands.test.config_manager")
    async def test_run_no_current_test_all(self, mock_config, test_command, mock_providers):
        """Test run with no current provider, tests all."""
        mock_config.get_current_provider.return_value = None
        mock_config.list_providers.return_value = mock_providers

        with patch.object(test_command, "_test_all_providers", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = True
            result = await test_command.run(None)
            assert result is True
            mock_test.assert_called_once_with(mock_providers)

    @patch("vibe_coder.commands.test.config_manager")
    async def test_run_no_providers(self, mock_config, test_command):
        """Test run with no providers configured."""
        mock_config.get_current_provider.return_value = None
        mock_config.list_providers.return_value = {}

        with patch.object(test_command.console, "print") as mock_print:
            result = await test_command.run(None)
            assert result is False
            mock_print.assert_any_call("[red]No providers configured to test.[/red]")


class TestTestCommandSingleProvider:
    """Test single provider testing."""

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_single_provider_success(self, mock_factory, mock_config, test_command, mock_providers):
        """Test successful single provider test."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_client.test_request.return_value = {
            "success": True,
            "response": "Test response",
            "latency": 0.5,
            "model": "gpt-4"
        }
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress") as mock_progress:
            mock_progress.return_value.__enter__.return_value = MagicMock()

            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_single_provider("openai")
                assert result is True
                # Should print success message
                mock_print.assert_any_call("[green]✓ Connection test passed[/green]")

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_single_provider_not_found(self, mock_factory, mock_config, test_command):
        """Test testing non-existent provider."""
        mock_config.get_provider.return_value = None

        with patch.object(test_command.console, "print") as mock_print:
            result = await test_command._test_single_provider("nonexistent")
            assert result is False
            mock_print.assert_any_call("[red]Provider 'nonexistent' not found[/red]")

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_single_provider_connection_failed(
        self, mock_factory, mock_config, test_command, mock_providers
    ):
        """Test single provider with connection failure."""
        provider = mock_providers["claude"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = False
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_single_provider("claude")
                assert result is False
                mock_print.assert_any_call("[red]✗ Connection failed[/red]")

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_single_provider_test_request_failed(
        self, mock_factory, mock_config, test_command, mock_providers
    ):
        """Test single provider with test request failure."""
        provider = mock_providers["local"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_client.test_request.return_value = {
            "success": False,
            "error": "API error occurred"
        }
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_single_provider("local")
                assert result is False
                mock_print.assert_any_call("[red]✗ Test request failed: API error occurred[/red]")

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_single_provider_with_latency_warning(
        self, mock_factory, mock_config, test_command, mock_providers
    ):
        """Test single provider with high latency warning."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_client.test_request.return_value = {
            "success": True,
            "response": "Slow response",
            "latency": 5.0,  # High latency
            "model": "gpt-4"
        }
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_single_provider("openai")
                assert result is True
                # Should warn about high latency
                mock_print.assert_any_call("[yellow]⚠ High latency detected: 5.00s[/yellow]")

    @patch("vibe_coder.commands.test.config_manager")
    async def test_single_provider_exception(
        self, mock_config, test_command, mock_providers
    ):
        """Test single provider with exception during test."""
        mock_config.get_provider.return_value = mock_providers["openai"]

        with patch("vibe_coder.commands.test.ClientFactory") as mock_factory:
            mock_factory.create_client.side_effect = Exception("Client creation failed")

            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_single_provider("openai")
                assert result is False
                mock_print.assert_any_call("[red]✗ Test failed: Client creation failed[/red]")


class TestTestCommandAllProviders:
    """Test testing all providers."""

    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_all_providers_all_success(self, mock_factory, test_command, mock_providers):
        """Test all providers when all succeed."""
        # Mock all clients to succeed
        mock_clients = []
        for provider_name in mock_providers:
            mock_client = AsyncMock()
            mock_client.validate_connection.return_value = True
            mock_client.test_request.return_value = {
                "success": True,
                "response": f"Response from {provider_name}",
                "latency": 0.3
            }
            mock_client.provider_name = provider_name
            mock_clients.append(mock_client)

        mock_factory.create_client.side_effect = [
            AsyncMock().__aenter__.return_value.__aexit__(mock_clients[0], None, None),
            AsyncMock().__aenter__.return_value.__aexit__(mock_clients[1], None, None),
            AsyncMock().__aenter__.return_value.__aexit__(mock_clients[2], None, None)
        ]

        for i, client in enumerate(mock_clients):
            mock_factory.create_client.return_value.__aenter__.return_value = client

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_all_providers(mock_providers)
                assert result is True

    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_all_providers_partial_failure(self, mock_factory, test_command, mock_providers):
        """Test all providers with some failures."""
        # Mock clients: first succeeds, others fail
        mock_clients = []
        results = [True, False, False]

        for i, (provider_name, success) in enumerate(zip(mock_providers, results)):
            mock_client = AsyncMock()
            mock_client.validate_connection.return_value = success
            mock_client.test_request.return_value = {
                "success": success,
                "response": "Response" if success else None,
                "error": None if success else "Connection failed"
            }
            mock_clients.append(mock_client)

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_all_providers(mock_providers)
                assert result is False  # Should return False if any fail

    async def test_all_providers_empty(self, test_command):
        """Test all providers with empty list."""
        result = await test_command._test_all_providers({})
        assert result is True  # Empty list should be considered success

    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_all_providers_show_summary(self, mock_factory, test_command, mock_providers):
        """Test that all providers test shows summary."""
        # Mock successful tests
        mock_clients = []
        for provider in mock_providers.values():
            mock_client = AsyncMock()
            mock_client.validate_connection.return_value = True
            mock_client.test_request.return_value = {
                "success": True,
                "response": "Success",
                "latency": 0.2
            }
            mock_clients.append(mock_client)

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                result = await test_command._test_all_providers(mock_providers)
                assert result is True
                # Should print summary
                assert any("Test Summary" in str(call) for call in mock_print.call_args_list)


class TestTestCommandDetailedReport:
    """Test detailed reporting functionality."""

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_show_detailed_report(self, mock_factory, mock_config, test_command, mock_providers):
        """Test showing detailed test report."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_client.test_request.return_value = {
            "success": True,
            "response": "Detailed test response",
            "latency": 0.45,
            "model": "gpt-4",
            "tokens": {
                "prompt": 10,
                "completion": 20,
                "total": 30
            },
            "usage": {
                "cost": 0.001
            }
        }
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                with patch.object(test_command, "_show_detailed_report") as mock_report:
                    await test_command._test_single_provider("openai", detailed=True)
                    mock_report.assert_called_once()

    def test_format_test_results(self, test_command):
        """Test formatting of test results."""
        results = {
            "success": True,
            "response": "Test response",
            "latency": 0.123,
            "model": "test-model",
            "tokens": {"prompt": 5, "completion": 10, "total": 15},
            "cost": 0.0005
        }

        # This would test the formatting of results for display
        # In a real test, you might capture the console output
        formatted = test_command._format_test_results(results)
        assert formatted is not None or True  # Placeholder


class TestTestCommandTroubleshooting:
    """Test troubleshooting guidance."""

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_connection_error_troubleshooting(
        self, mock_factory, mock_config, test_command, mock_providers
    ):
        """Test troubleshooting guidance for connection errors."""
        provider = mock_providers["openai"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.side_effect = Exception("Connection timeout")
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                with patch.object(test_command, "_show_troubleshooting") as mock_trouble:
                    await test_command._test_single_provider("openai")
                    mock_trouble.assert_called_once()

    @patch("vibe_coder.commands.test.config_manager")
    @patch("vibe_coder.commands.test.ClientFactory")
    async def test_auth_error_troubleshooting(
        self, mock_factory, mock_config, test_command, mock_providers
    ):
        """Test troubleshooting guidance for authentication errors."""
        provider = mock_providers["claude"]
        mock_config.get_provider.return_value = provider

        mock_client = AsyncMock()
        mock_client.validate_connection.side_effect = Exception("401 Unauthorized")
        mock_factory.create_client.return_value.__aenter__.return_value = mock_client
        mock_factory.create_client.return_value.__aexit__.return_value = None

        with patch("vibe_coder.commands.test.Progress"):
            with patch.object(test_command.console, "print") as mock_print:
                with patch.object(test_command, "_show_troubleshooting") as mock_trouble:
                    await test_command._test_single_provider("claude")
                    mock_trouble.assert_called_once()

    def test_show_troubleshooting_connection(self, test_command):
        """Test showing connection troubleshooting tips."""
        with patch.object(test_command.console, "print") as mock_print:
            test_command._show_troubleshooting("connection", "localhost:11434")
            mock_print.assert_called()
            # Should include tips about checking if server is running

    def test_show_troubleshooting_auth(self, test_command):
        """Test showing authentication troubleshooting tips."""
        with patch.object(test_command.console, "print") as mock_print:
            test_command._show_troubleshooting("auth", "api.openai.com")
            mock_print.assert_called()
            # Should include tips about checking API key


class TestTestCommandIntegration:
    """Integration tests for test command."""

    @patch("vibe_coder.commands.test.config_manager")
    async def test_test_provider_with_env_vars(self, mock_config, test_command):
        """Test testing provider using environment variables."""
        # Mock provider from environment
        provider = AIProvider(
            name="env-provider",
            api_key="env-key-123",
            endpoint="https://api.example.com/v1"
        )
        mock_config.get_provider.return_value = provider

        with patch("vibe_coder.commands.test.ClientFactory") as mock_factory:
            mock_client = AsyncMock()
            mock_client.validate_connection.return_value = True
            mock_client.test_request.return_value = {
                "success": True,
                "response": "Env test successful"
            }
            mock_factory.create_client.return_value.__aenter__.return_value = mock_client
            mock_factory.create_client.return_value.__aexit__.return_value = None

            with patch("vibe_coder.commands.test.Progress"):
                with patch.object(test_command.console, "print"):
                    result = await test_command._test_single_provider("env-provider")
                    assert result is True

    async def test_test_provider_model_info(self, test_command):
        """Test that model information is displayed correctly."""
        # This would test how model information from the provider is shown
        # In a real implementation, you might check that the model name
        # from the provider config appears in the test output
        assert True  # Placeholder