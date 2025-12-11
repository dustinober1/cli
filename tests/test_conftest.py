"""
Tests to verify that the testing infrastructure is working correctly.
"""

import pytest
from pathlib import Path

from vibe_coder.types.config import AIProvider, AppConfig
from vibe_coder.types.api import ApiMessage, MessageRole


class TestFixtures:
    """Test that all fixtures are working correctly."""

    def test_temp_dir(self, temp_dir: Path):
        """Test the temp_dir fixture."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        # Verify it's actually in a temp location
        assert "vibe_coder_test_" in str(temp_dir)

    def test_sample_python_project(self, sample_python_project: Path):
        """Test the sample_python_project fixture."""
        assert sample_python_project.exists()
        assert (sample_python_project / "src").exists()
        assert (sample_python_project / "tests").exists()
        assert (sample_python_project / "pyproject.toml").exists()
        assert (sample_python_project / "README.md").exists()

    def test_git_repository(self, git_repository: Path):
        """Test the git_repository fixture."""
        assert git_repository.exists()
        assert (git_repository / ".git").exists()
        assert (git_repository / ".git").is_dir()

    async def test_config_manager(self, config_manager):
        """Test the config_manager fixture."""
        assert config_manager is not None
        assert isinstance(config_manager.config, AppConfig)
        assert len(config_manager.list_providers()) == 0

    async def test_sample_provider(self, sample_provider):
        """Test the sample_provider fixture."""
        assert isinstance(sample_provider, AIProvider)
        assert sample_provider.name == "test-openai"
        assert sample_provider.api_key == "sk-test-key-12345"
        assert sample_provider.endpoint == "https://api.openai.com/v1"
        assert sample_provider.model == "gpt-4"

    async def test_config_manager_with_provider(
        self, config_manager_with_provider, sample_provider
    ):
        """Test the config_manager_with_provider fixture."""
        providers = config_manager_with_provider.list_providers()
        assert len(providers) == 1
        assert sample_provider.name in providers

    def test_mock_openai_client(self, mock_openai_client):
        """Test the mock_openai_client fixture."""
        assert mock_openai_client is not None
        assert hasattr(mock_openai_client, 'send_request')
        assert hasattr(mock_openai_client, 'stream_request')
        assert hasattr(mock_openai_client, 'validate_connection')

    def test_mock_anthropic_client(self, mock_anthropic_client):
        """Test the mock_anthropic_client fixture."""
        assert mock_anthropic_client is not None
        assert hasattr(mock_anthropic_client, 'send_request')
        assert hasattr(mock_anthropic_client, 'stream_request')

    def test_mock_generic_client(self, mock_generic_client):
        """Test the mock_generic_client fixture."""
        assert mock_generic_client is not None
        assert hasattr(mock_generic_client, 'send_request')
        assert hasattr(mock_generic_client, 'stream_request')

    def test_mock_provider(self, mock_provider):
        """Test the mock_provider fixture."""
        assert isinstance(mock_provider, dict)
        assert "name" in mock_provider
        assert "api_key" in mock_provider
        assert "endpoint" in mock_provider
        assert mock_provider["name"] == "mock-provider"

    def test_mock_ai_response(self, mock_ai_response):
        """Test the mock_ai_response fixture."""
        assert mock_ai_response.content is not None
        assert mock_ai_response.usage is not None
        assert mock_ai_response.finish_reason is not None

    def test_mock_api_messages(self, mock_api_messages):
        """Test the mock_api_messages fixture."""
        assert len(mock_api_messages) > 0
        assert all(isinstance(msg, ApiMessage) for msg in mock_api_messages)
        assert mock_api_messages[0].role == MessageRole.SYSTEM
        assert mock_api_messages[1].role == MessageRole.USER

    def test_mock_console(self, mock_console):
        """Test the mock_console fixture."""
        assert mock_console is not None
        assert hasattr(mock_console, 'print')
        assert hasattr(mock_console, 'input')
        assert hasattr(mock_console, 'panel')

    def test_slash_command_parser(self, slash_command_parser):
        """Test the slash_command_parser fixture."""
        assert slash_command_parser is not None
        assert hasattr(slash_command_parser, 'parse')

    def test_sample_ast_data(self, sample_ast_data):
        """Test the sample_ast_data fixture."""
        assert isinstance(sample_ast_data, dict)
        assert "functions" in sample_ast_data
        assert "classes" in sample_ast_data
        assert "imports" in sample_ast_data

    def test_error_snippet(self, error_snippet):
        """Test the error_snippet fixture."""
        assert isinstance(error_snippet, str)
        assert "calculate_average" in error_snippet

    def test_fixed_snippet(self, fixed_snippet):
        """Test the fixed_snippet fixture."""
        assert isinstance(fixed_snippet, str)
        assert "calculate_average" in fixed_snippet
        assert "if not numbers:" in fixed_snippet

    def test_cost_tracker(self, cost_tracker):
        """Test the cost_tracker fixture."""
        assert cost_tracker is not None
        assert hasattr(cost_tracker, 'track_usage')

    def test_sample_usage_data(self, sample_usage_data):
        """Test the sample_usage_data fixture."""
        assert isinstance(sample_usage_data, dict)
        assert "openai" in sample_usage_data
        assert "anthropic" in sample_usage_data
        assert "requests" in sample_usage_data["openai"]

    def test_plugin_manager(self, plugin_manager):
        """Test the plugin_manager fixture."""
        assert plugin_manager is not None
        assert hasattr(plugin_manager, 'load_plugins')
        assert hasattr(plugin_manager, 'get_plugins')

    def test_sample_plugin_code(self, sample_plugin_code):
        """Test the sample_plugin_code fixture."""
        assert isinstance(sample_plugin_code, str)
        assert "class CustomAnalyzer" in sample_plugin_code
        assert "BaseAnalyzerPlugin" in sample_plugin_code


class TestMarkedTests:
    """Test that pytest markers are working correctly."""

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit marker is recognized."""
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow marker is recognized."""
        import time
        time.sleep(0.01)  # Small delay to qualify as slow
        assert True

    @pytest.mark.cli
    def test_cli_marker(self):
        """Test that CLI marker is recognized."""
        assert True

    @pytest.mark.api
    def test_api_marker(self):
        """Test that API marker is recognized."""
        assert True

    @pytest.mark.config
    def test_config_marker(self):
        """Test that config marker is recognized."""
        assert True

    @pytest.mark.openai
    def test_openai_marker(self):
        """Test that OpenAI marker is recognized."""
        assert True

    @pytest.mark.anthropic
    def test_anthropic_marker(self):
        """Test that Anthropic marker is recognized."""
        assert True

    @pytest.mark.ollama
    def test_ollama_marker(self):
        """Test that Ollama marker is recognized."""
        assert True

    @pytest.mark.generic
    def test_generic_marker(self):
        """Test that generic provider marker is recognized."""
        assert True

    @pytest.mark.security
    def test_security_marker(self):
        """Test that security marker is recognized."""
        assert True

    @pytest.mark.reliability
    def test_reliability_marker(self):
        """Test that reliability marker is recognized."""
        assert True

    @pytest.mark.compatibility
    def test_compatibility_marker(self):
        """Test that compatibility marker is recognized."""
        assert True

    @pytest.mark.network
    def test_network_marker(self):
        """Test that network marker is recognized."""
        assert True

    @pytest.mark.github
    def test_github_marker(self):
        """Test that GitHub marker is recognized."""
        assert True


class TestAsyncFixtures:
    """Test that async fixtures are working correctly."""

    @pytest.mark.asyncio
    async def test_async_fixture(self, event_loop):
        """Test that async fixtures work correctly."""
        assert event_loop is not None
        import asyncio
        assert isinstance(asyncio.get_event_loop(), type(event_loop))

    @pytest.mark.asyncio
    async def test_async_config_manager(self, config_manager_with_provider):
        """Test async config manager operations."""
        provider = config_manager_with_provider.get_current_provider()
        assert provider is not None
        assert provider.name == "test-openai"

    @pytest.mark.asyncio
    async def test_mock_streaming(self, mock_openai_client):
        """Test mock streaming functionality."""
        chunks = []
        async for chunk in mock_openai_client.stream_request([]):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert "".join(chunks) == "This is a mock streaming response"