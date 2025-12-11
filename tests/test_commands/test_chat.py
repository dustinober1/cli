"""
Test chat command functionality.
"""
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from rich.console import Console

from vibe_coder.commands.chat import ChatCommand
from vibe_coder.types.api import ApiMessage, MessageRole, ApiResponse, TokenUsage
from vibe_coder.types.config import AIProvider

# Set test environment variable
os.environ["VIBE_CODER_TEST"] = "true"


@pytest.fixture
def mock_provider():
    """Create a mock AI provider."""
    return AIProvider(
        name="test-provider",
        api_key="test-key",
        endpoint="https://api.test.com/v1",
        model="test-model",
        temperature=0.7,
        max_tokens=1000
    )


@pytest.fixture
def mock_config_manager(mock_provider):
    """Create a mock config manager."""
    mock = MagicMock()
    mock.get_provider.return_value = mock_provider
    mock.get_current_provider.return_value = mock_provider
    mock.list_providers.return_value = {"test-provider": mock_provider}
    return mock


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    mock = AsyncMock()
    mock.send_request.return_value = ApiResponse(
        content="Test response",
        usage=TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        ),
        finish_reason="stop"
    )
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def chat_command():
    """Create a ChatCommand instance."""
    # Mock the repository intelligence components to avoid dependencies
    with patch("vibe_coder.commands.chat.RepositoryMapper"), \
         patch("vibe_coder.commands.chat.CodeContextProvider"), \
         patch("vibe_coder.commands.chat.GitOperations") as mock_git:
        mock_git.return_value.is_git_repo.return_value = False

        # Mock MCP manager to avoid connection errors
        with patch("vibe_coder.commands.chat.MCPManager") as mock_mcp:
            mock_mcp.return_value.connect_all = AsyncMock()
            mock_mcp.return_value.close = AsyncMock()

            command = ChatCommand()
            return command


class TestChatCommandInitialization:
    """Test ChatCommand initialization."""

    def test_chat_command_init(self, chat_command):
        """Test ChatCommand initialization."""
        assert chat_command.console is not None
        assert isinstance(chat_command.console, Console)
        assert chat_command.messages == []
        assert chat_command.client is None
        assert chat_command.provider is None

    @patch("vibe_coder.commands.chat.questionary")
    def test_chat_command_init_with_imports(self, mock_questionary):
        """Test ChatCommand with mocked imports."""
        with patch("vibe_coder.commands.chat.RepositoryMapper"), \
             patch("vibe_coder.commands.chat.CodeContextProvider"), \
             patch("vibe_coder.commands.chat.GitOperations") as mock_git, \
             patch("vibe_coder.commands.chat.command_registry") as mock_registry, \
             patch("vibe_coder.commands.chat.MCPManager"):

            mock_git.return_value.is_git_repo.return_value = True
            mock_git.return_value.get_git_info.return_value = {"branch": "main"}
            mock_registry.get_parser.return_value = MagicMock()

            command = ChatCommand()
            assert command.slash_parser is not None
            assert command.git_info is not None

    def test_chat_command_init_slash_command_error(self):
        """Test ChatCommand initialization with slash command error."""
        with patch("vibe_coder.commands.chat.RepositoryMapper"), \
             patch("vibe_coder.commands.chat.CodeContextProvider"), \
             patch("vibe_coder.commands.chat.GitOperations") as mock_git, \
             patch("vibe_coder.commands.chat.command_registry") as mock_registry, \
             patch("vibe_coder.commands.chat.MCPManager"):

            mock_git.return_value.is_git_repo.side_effect = Exception("Git error")
            mock_registry.get_parser.side_effect = Exception("Registry error")

            command = ChatCommand()
            assert command.slash_parser is None


class TestChatCommandProviderSetup:
    """Test provider setup functionality."""

    @patch("vibe_coder.commands.chat.config_manager")
    @patch("vibe_coder.commands.chat.ClientFactory")
    async def test_setup_provider_success(
        self, mock_factory, mock_config, chat_command, mock_provider, mock_client
    ):
        """Test successful provider setup."""
        mock_config.get_current_provider.return_value = mock_provider
        mock_factory.create_client.return_value = mock_client

        result = await chat_command._setup_provider(
            provider_name=None,
            model=None,
            temperature=None,
            max_tokens=None
        )

        assert result is True
        assert chat_command.provider == mock_provider
        assert chat_command.client == mock_client
        mock_factory.create_client.assert_called_once_with(mock_provider)

    @patch("vibe_coder.commands.chat.config_manager")
    @patch("vibe_coder.commands.chat.ClientFactory")
    async def test_setup_provider_with_overrides(
        self, mock_factory, mock_config, chat_command, mock_provider, mock_client
    ):
        """Test provider setup with parameter overrides."""
        mock_config.get_provider.return_value = mock_provider
        mock_factory.create_client.return_value = mock_client

        result = await chat_command._setup_provider(
            provider_name="override-provider",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )

        assert result is True
        # Check that overrides were applied to the provider
        assert mock_provider.model == "gpt-4"
        assert mock_provider.temperature == 0.5
        assert mock_provider.max_tokens == 2000

    @patch("vibe_coder.commands.chat.config_manager")
    async def test_setup_provider_no_current(self, mock_config, chat_command):
        """Test provider setup with no current provider."""
        mock_config.get_current_provider.return_value = None

        result = await chat_command._setup_provider(
            provider_name=None,
            model=None,
            temperature=None,
            max_tokens=None
        )

        assert result is False

    @patch("vibe_coder.commands.chat.config_manager")
    @patch("vibe_coder.commands.chat.questionary")
    async def test_setup_provider_no_providers_configured(
        self, mock_questionary, mock_config, chat_command
    ):
        """Test provider setup when no providers are configured."""
        mock_config.get_current_provider.return_value = None
        mock_config.list_providers.return_value = {}
        mock_questionary.select.return_value.ask.return_value = "setup"

        result = await chat_command._setup_provider(
            provider_name=None,
            model=None,
            temperature=None,
            max_tokens=None
        )

        assert result is False

    @patch("vibe_coder.commands.chat.config_manager")
    async def test_setup_provider_creation_error(
        self, mock_config, chat_command, mock_provider
    ):
        """Test provider setup when client creation fails."""
        mock_config.get_current_provider.return_value = mock_provider

        with patch("vibe_coder.commands.chat.ClientFactory") as mock_factory:
            mock_factory.create_client.side_effect = Exception("Client creation failed")

            result = await chat_command._setup_provider(
                provider_name=None,
                model=None,
                temperature=None,
                max_tokens=None
            )

            assert result is False


class TestChatCommandWelcomeMessage:
    """Test welcome message functionality."""

    def test_show_welcome(self, chat_command, mock_provider):
        """Test showing welcome message."""
        chat_command.provider = mock_provider
        chat_command.git_info = None

        with patch.object(chat_command.console, "print") as mock_print:
            chat_command._show_welcome()
            mock_print.assert_called()
            # Check that provider info is in the output
            call_args = mock_print.call_args[0][0]
            assert "test-provider" in str(call_args)

    def test_show_welcome_with_git_info(self, chat_command, mock_provider):
        """Test showing welcome message with git info."""
        chat_command.provider = mock_provider
        chat_command.git_info = {"branch": "main", "remote": "origin"}

        with patch.object(chat_command.console, "print") as mock_print:
            chat_command._show_welcome()
            mock_print.assert_called()


class TestChatCommandMessageHandling:
    """Test message handling functionality."""

    def test_add_message(self, chat_command):
        """Test adding a message to history."""
        message = ApiMessage(role=MessageRole.USER, content="Hello")
        chat_command._add_message(message)

        assert len(chat_command.messages) == 1
        assert chat_command.messages[0] == message

    def test_clear_messages(self, chat_command):
        """Test clearing message history."""
        chat_command.messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        ]

        chat_command._clear_messages()
        assert len(chat_command.messages) == 0

    def test_get_history(self, chat_command):
        """Test getting message history."""
        messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        ]
        chat_command.messages = messages

        history = chat_command._get_history()
        assert history == messages


class TestChatCommandChatLoop:
    """Test chat loop functionality."""

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_normal_message(
        self, mock_questionary, chat_command, mock_client
    ):
        """Test chat loop with normal message."""
        chat_command.client = mock_client

        # Mock user input
        mock_questionary.text.return_value.ask.return_value = "Hello, AI!"

        # Mock exit condition
        def side_effect(*args, **kwargs):
            if len(chat_command.messages) > 0:
                return "/exit"
            return "Hello, AI!"

        mock_questionary.text.return_value.ask.side_effect = side_effect

        with patch.object(chat_command.console, "print"):
            with patch.object(chat_command, "_handle_ai_response") as mock_handle:
                await chat_command._chat_loop()
                mock_handle.assert_called_once()

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_with_slash_command(
        self, mock_questionary, chat_command
    ):
        """Test chat loop with slash command."""
        chat_command.slash_parser = MagicMock()
        chat_command.slash_parser.is_slash_command.return_value = True
        chat_command.slash_parser.parse_and_execute = AsyncMock(return_value=True)

        mock_questionary.text.return_value.ask.return_value = "/help"

        with patch.object(chat_command.console, "print"):
            # Mock exit after one iteration
            def side_effect(*args, **kwargs):
                if hasattr(chat_command, "_slash_called"):
                    return "/exit"
                chat_command._slash_called = True
                return "/help"

            mock_questionary.text.return_value.ask.side_effect = side_effect

            await chat_command._chat_loop()
            chat_command.slash_parser.parse_and_execute.assert_called_once()

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_exit_commands(
        self, mock_questionary, chat_command
    ):
        """Test chat loop with exit commands."""
        test_cases = ["/exit", "/quit", "exit"]

        for exit_cmd in test_cases:
            chat_command.messages = []  # Reset for each test
            mock_questionary.text.return_value.ask.return_value = exit_cmd

            with patch.object(chat_command.console, "print"):
                await chat_command._chat_loop()
                # Should exit without adding messages
                assert len(chat_command.messages) == 0

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_clear_command(
        self, mock_questionary, chat_command
    ):
        """Test chat loop with clear command."""
        # Add some messages first
        chat_command.messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        ]

        mock_questionary.text.return_value.ask.side_effect = [
            "/clear",
            "/exit"
        ]

        with patch.object(chat_command.console, "print") as mock_print:
            await chat_command._chat_loop()
            assert len(chat_command.messages) == 0
            # Check that clear message was printed
            mock_print.assert_any_call("[yellow]Conversation history cleared.[/yellow]")

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_empty_input(
        self, mock_questionary, chat_command
    ):
        """Test chat loop with empty input."""
        mock_questionary.text.return_value.ask.side_effect = [
            "",  # Empty input
            "/exit"
        ]

        with patch.object(chat_command.console, "print"):
            await chat_command._chat_loop()
            # Should not add empty message
            assert len(chat_command.messages) == 0

    @patch("vibe_coder.commands.chat.questionary")
    async def test_chat_loop_keyboard_interrupt(
        self, mock_questionary, chat_command
    ):
        """Test chat loop with keyboard interrupt."""
        mock_questionary.text.return_value.ask.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            await chat_command._chat_loop()


class TestChatCommandAIResponse:
    """Test AI response handling."""

    async def test_handle_ai_response_success(self, chat_command, mock_client):
        """Test handling successful AI response."""
        chat_command.client = mock_client
        user_message = ApiMessage(role=MessageRole.USER, content="Hello")

        with patch.object(chat_command.console, "print"):
            await chat_command._handle_ai_response(user_message)

        # Check that user message was added
        assert len(chat_command.messages) == 2
        assert chat_command.messages[0] == user_message
        assert chat_command.messages[1].role == MessageRole.ASSISTANT
        assert chat_command.messages[1].content == "Test response"

    async def test_handle_ai_response_with_context(
        self, chat_command, mock_client
    ):
        """Test handling AI response with context injection."""
        chat_command.client = mock_client
        chat_command.repo_mapper = MagicMock()
        chat_command.context_provider = MagicMock()

        # Mock context retrieval
        chat_command.context_provider.get_code_context.return_value = {
            "file_path": "test.py",
            "content": "def test(): pass"
        }

        user_message = ApiMessage(role=MessageRole.USER, content="Fix this code")

        with patch.object(chat_command.console, "print"):
            with patch.object(chat_command, "_inject_context") as mock_inject:
                await chat_command._handle_ai_response(user_message)
                mock_inject.assert_called_once()

    async def test_handle_ai_response_error(self, chat_command):
        """Test handling AI response error."""
        chat_command.client = AsyncMock()
        chat_command.client.send_request.side_effect = Exception("API Error")

        user_message = ApiMessage(role=MessageRole.USER, content="Hello")

        with patch.object(chat_command.console, "print") as mock_print:
            await chat_command._handle_ai_response(user_message)
            # Check error message was printed
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "[red]" in str(call_args)


class TestChatCommandStreaming:
    """Test streaming response functionality."""

    async def test_stream_response(self, chat_command, mock_client):
        """Test streaming AI response."""
        chat_command.client = mock_client

        # Mock streaming responses
        async def mock_stream(messages):
            yield "Hello"
            yield " there"
            yield "!"

        mock_client.stream_request.return_value = mock_stream([])

        user_message = ApiMessage(role=MessageRole.USER, content="Say hello")

        with patch("vibe_coder.commands.chat.Live") as mock_live:
            await chat_command._handle_ai_response(user_message, stream=True)
            mock_live.assert_called_once()


class TestChatCommandSlashCommands:
    """Test slash command integration."""

    async def test_handle_slash_command_help(self, chat_command):
        """Test /help slash command."""
        chat_command.slash_parser = MagicMock()
        chat_command.slash_parser.parse_and_execute = AsyncMock(return_value=True)

        with patch.object(chat_command.console, "print"):
            result = await chat_command._handle_slash_command("/help")
            assert result is True

    async def test_handle_slash_command_history(self, chat_command):
        """Test /history slash command."""
        chat_command.messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        ]

        with patch.object(chat_command.console, "print") as mock_print:
            await chat_command._handle_slash_command("/history")
            mock_print.assert_called()

    async def test_handle_slash_command_provider(self, chat_command, mock_provider):
        """Test /provider slash command."""
        chat_command.provider = mock_provider

        with patch.object(chat_command.console, "print") as mock_print:
            await chat_command._handle_slash_command("/provider")
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "test-provider" in str(call_args)

    async def test_handle_slash_command_save(self, chat_command):
        """Test /save slash command."""
        chat_command.messages = [
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi!")
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            with patch.object(chat_command.console, "print"):
                await chat_command._handle_slash_command(f"/save {temp_file}")
                assert os.path.exists(temp_file)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    async def test_handle_slash_command_invalid(self, chat_command):
        """Test handling invalid slash command."""
        with patch.object(chat_command.console, "print") as mock_print:
            result = await chat_command._handle_slash_command("/invalid")
            assert result is False
            mock_print.assert_called()


class TestChatCommandRun:
    """Test the main run method."""

    @patch("vibe_coder.commands.chat.config_manager")
    async def test_run_success(self, mock_config, chat_command, mock_provider):
        """Test successful chat run."""
        mock_config.get_current_provider.return_value = mock_provider

        with patch.object(chat_command, "_setup_provider", new_callable=AsyncMock) as mock_setup, \
             patch.object(chat_command, "_chat_loop", new_callable=AsyncMock) as mock_chat_loop:

            mock_setup.return_value = True

            result = await chat_command.run()
            assert result is True
            mock_setup.assert_called_once()
            mock_chat_loop.assert_called_once()

    @patch("vibe_coder.commands.chat.config_manager")
    async def test_run_setup_failure(self, mock_config, chat_command):
        """Test chat run with setup failure."""
        mock_config.get_current_provider.return_value = None

        with patch.object(chat_command, "_setup_provider", new_callable=AsyncMock) as mock_setup:
            mock_setup.return_value = False

            result = await chat_command.run()
            assert result is False

    async def test_run_keyboard_interrupt(self, chat_command):
        """Test chat run with keyboard interrupt."""
        with patch.object(chat_command, "_setup_provider", new_callable=AsyncMock) as mock_setup:
            mock_setup.side_effect = KeyboardInterrupt()

            result = await chat_command.run()
            assert result is True  # Should still return True for graceful exit

    async def test_run_general_exception(self, chat_command):
        """Test chat run with general exception."""
        with patch.object(chat_command, "_setup_provider", new_callable=AsyncMock) as mock_setup:
            mock_setup.side_effect = Exception("Unexpected error")

            result = await chat_command.run()
            assert result is False


# Integration Tests (5 tests)
class TestChatCommandIntegration:
    """Integration tests for ChatCommand."""

    @pytest.mark.integration
    async def test_full_chat_flow_with_mock_api(self, chat_command):
        """Test full chat flow with mocked API."""
        # This is an integration test that tests multiple components together
        with patch("vibe_coder.commands.chat.config_manager") as mock_config, \
             patch("vibe_coder.commands.chat.ClientFactory") as mock_factory, \
             patch("vibe_coder.commands.chat.questionary") as mock_questionary:

            # Setup mocks
            mock_provider = AIProvider(
                name="test",
                api_key="test-key",
                endpoint="https://api.test.com/v1"
            )
            mock_config.get_current_provider.return_value = mock_provider

            mock_client = AsyncMock()
            mock_client.send_request.return_value = ApiResponse(
                content="Integration test response",
                usage=TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
                finish_reason="stop"
            )
            mock_factory.create_client.return_value = mock_client

            # Mock user interaction
            mock_questionary.text.return_value.ask.side_effect = [
                "Hello from integration test",
                "/exit"
            ]

            # Run the chat
            result = await chat_command.run()
            assert result is True
            assert len(chat_command.messages) == 2
            assert chat_command.messages[1].content == "Integration test response"

    @pytest.mark.integration
    async def test_context_injection_integration(self, chat_command):
        """Test context injection with repository intelligence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Create a test file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def hello():\n    print('Hello, World!')")

            # Initialize repository mapper and context provider
            with patch("vibe_coder.commands.chat.config_manager") as mock_config, \
                 patch("vibe_coder.commands.chat.ClientFactory") as mock_factory:

                mock_provider = AIProvider(
                    name="test",
                    api_key="test-key",
                    endpoint="https://api.test.com/v1"
                )
                mock_config.get_current_provider.return_value = mock_provider

                mock_client = AsyncMock()
                mock_client.send_request.return_value = ApiResponse(
                    content="I see the hello function",
                    usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
                    finish_reason="stop"
                )
                mock_factory.create_client.return_value = mock_client

                # Setup repository components
                from vibe_coder.intelligence.repo_mapper import RepositoryMapper
                from vibe_coder.intelligence.code_context import CodeContextProvider

                chat_command.repo_mapper = RepositoryMapper()
                chat_command.context_provider = CodeContextProvider()

                # Wait for async initialization
                await chat_command.repo_mapper.initialize()
                await chat_command.context_provider.initialize()

                # Send a message that should trigger context injection
                user_message = ApiMessage(role=MessageRole.USER, content="What's in this file?")

                with patch.object(chat_command.console, "print"):
                    await chat_command._handle_ai_response(user_message)

                # Verify client was called with context
                mock_client.send_request.assert_called_once()
                call_args = mock_client.send_request.call_args[0][0]
                # Should contain file context
                assert any("def hello" in msg.content for msg in call_args if msg.role == MessageRole.SYSTEM)

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_real_openai_api_integration(self, chat_command):
        """Test integration with real OpenAI API if credentials available."""
        # Skip if no real API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key found")

        from vibe_coder.api.openai_client import OpenAIClient

        # Create real client
        client = OpenAIClient(
            AIProvider(
                name="openai-test",
                api_key=os.getenv("OPENAI_API_KEY"),
                endpoint="https://api.openai.com/v1",
                model="gpt-3.5-turbo"
            )
        )

        try:
            # Test actual API call
            response = await client.send_request([
                ApiMessage(role=MessageRole.USER, content="Say 'API test successful'")
            ])

            assert "API test successful" in response.content
            assert response.usage.total_tokens > 0

        finally:
            await client.close()

    @pytest.mark.integration
    async def test_mcp_tool_integration(self, chat_command):
        """Test MCP tool integration in chat."""
        with patch("vibe_coder.commands.chat.MCPManager") as mock_mcp:
            # Mock MCP manager with tools
            mock_manager = MagicMock()
            mock_manager.connect_all = AsyncMock()
            mock_manager.list_tools.return_value = ["test_tool"]
            mock_manager.call_tool = AsyncMock(return_value={"result": "tool output"})
            mock_mcp.return_value = mock_manager

            # Test slash command that uses MCP tools
            chat_command.slash_parser = MagicMock()

            with patch("vibe_coder.commands.chat.questionary") as mock_questionary:
                mock_questionary.text.return_value.ask.side_effect = [
                    "/mcp list",
                    "/exit"
                ]

                with patch.object(chat_command.console, "print"):
                    await chat_command._chat_loop()

                    # Verify MCP manager was used
                    mock_manager.list_tools.assert_called()

    @pytest.mark.integration
    async def test_git_integration_in_chat(self, chat_command):
        """Test Git operations integration in chat."""
        # Initialize a git repository
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Init git repo
            import subprocess
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], check=True)

            # Create and commit a file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('Hello')")

            subprocess.run(["git", "add", "test.py"], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

            # Test git info is captured
            with patch("vibe_coder.commands.chat.config_manager"), \
                 patch("vibe_coder.commands.chat.ClientFactory"):

                # Re-initialize to capture git info
                chat_command = ChatCommand()

                assert chat_command.git_info is not None
                assert "branch" in chat_command.git_info
                assert chat_command.git_info["branch"] == "main" or chat_command.git_info["branch"] == "master"