"""Tests for slash command parser."""

from unittest.mock import AsyncMock

import pytest

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.commands.slash.parser import SlashCommandParser
from vibe_coder.types.api import ApiMessage, MessageRole
from vibe_coder.types.config import AIProvider


class MockCommand(SlashCommand):
    """Mock command for testing."""

    def __init__(self, name: str, response: str = "Mock response", description: str = "Mock command for testing", **kwargs):
        super().__init__(name, description, **kwargs)
        self.response = response
        self.execute_calls = []

    async def execute(self, args, context):
        self.execute_calls.append((args, context))
        return self.response


@pytest.fixture
def parser():
    """Create a fresh parser for each test."""
    return SlashCommandParser()


@pytest.fixture
def mock_provider():
    """Create a mock AI provider."""
    return AIProvider(
        name="test-provider",
        api_key="test-key",
        endpoint="https://api.test.com",
        model="test-model",
        temperature=0.7,
    )


@pytest.fixture
def mock_context(mock_provider):
    """Create a mock command context."""
    return CommandContext(
        chat_history=[ApiMessage(role=MessageRole.USER, content="test")],
        current_provider=mock_provider,
        working_directory="/test/dir",
        git_info=None,
    )


class TestSlashCommandParser:
    """Test the SlashCommandParser class."""

    def test_register_command(self, parser):
        """Test command registration."""
        command = MockCommand("test", "test response")
        parser.register_command(command)

        assert "test" in parser.commands
        assert parser.commands["test"] == command

    def test_register_command_with_aliases(self, parser):
        """Test command registration with aliases."""
        command = MockCommand("test", "test response", aliases=["t", "mock"])
        parser.register_command(command)

        assert "test" in parser.commands
        assert "t" in parser.aliases
        assert "mock" in parser.aliases
        assert parser.aliases["t"] == "test"
        assert parser.aliases["mock"] == "test"

    def test_is_slash_command(self, parser):
        """Test slash command detection."""
        assert parser.is_slash_command("/help")
        assert parser.is_slash_command("/test command args")
        assert not parser.is_slash_command("help")
        assert parser.is_slash_command(" /help")  # Leading space is allowed
        assert not parser.is_slash_command("")

    def test_parse_command_basic(self, parser):
        """Test basic command parsing."""
        command = MockCommand("test")
        parser.register_command(command)

        result = parser.parse_command("/test")
        assert result == ("test", [])

        result = parser.parse_command("/test arg1 arg2")
        assert result == ("test", ["arg1", "arg2"])

    def test_parse_command_with_aliases(self, parser):
        """Test command parsing with aliases."""
        command = MockCommand("test", aliases=["t"])
        parser.register_command(command)

        result = parser.parse_command("/t arg1")
        assert result == ("test", ["arg1"])

    def test_parse_command_quoted_args(self, parser):
        """Test command parsing with quoted arguments."""
        command = MockCommand("test")
        parser.register_command(command)

        result = parser.parse_command('/test "hello world" another')
        assert result == ("test", ["hello world", "another"])

    def test_parse_command_invalid(self, parser):
        """Test parsing invalid commands."""
        assert parser.parse_command("/") is None
        assert parser.parse_command(" /") is None
        assert parser.parse_command("") is None

    async def test_parse_and_execute_success(self, parser, mock_context):
        """Test successful command execution."""
        command = MockCommand("test", "success response")
        parser.register_command(command)

        success, response = await parser.parse_and_execute("/test arg1", mock_context)

        assert success is True
        assert response == "success response"
        assert len(command.execute_calls) == 1
        assert command.execute_calls[0][0] == ["arg1"]
        assert command.execute_calls[0][1] == mock_context

    async def test_parse_and_execute_unknown_command(self, parser, mock_context):
        """Test execution of unknown command."""
        success, response = await parser.parse_and_execute("/unknown", mock_context)

        assert success is False
        assert "Unknown command" in response

    async def test_parse_and_execute_with_suggestions(self, parser, mock_context):
        """Test unknown command with suggestions."""
        # Register commands that might be similar
        parser.register_command(MockCommand("help"))
        parser.register_command(MockCommand("hello"))

        success, response = await parser.parse_and_execute("/hell", mock_context)

        assert success is False
        assert "Did you mean" in response
        assert "/hello" in response

    async def test_parse_and_execute_git_requirement_fail(self, parser, mock_context):
        """Test command that requires Git repo when not in one."""
        command = MockCommand("git-test")
        command.requires_git_repo = lambda: True
        parser.register_command(command)

        success, response = await parser.parse_and_execute("/git-test", mock_context)

        assert success is False
        assert "requires a Git repository" in response

    async def test_parse_and_execute_git_requirement_success(self, parser, mock_context):
        """Test command that requires Git repo when in one."""
        command = MockCommand("git-test", "git success")
        command.requires_git_repo = lambda: True
        parser.register_command(command)

        # Mock git repo context
        mock_context.git_info = {"repo": True}

        success, response = await parser.parse_and_execute("/git-test", mock_context)

        assert success is True
        assert response == "git success"

    async def test_parse_and_execute_argument_validation(self, parser, mock_context):
        """Test command with argument validation."""
        command = MockCommand("test")
        command.get_min_args = lambda: 2
        command.validate_args = lambda args: (len(args) >= 2, "Need at least 2 args")
        parser.register_command(command)

        # Test with insufficient arguments
        success, response = await parser.parse_and_execute("/test arg1", mock_context)
        assert success is False
        assert "requires at least 2 argument" in response

        # Test with sufficient arguments
        success, response = await parser.parse_and_execute("/test arg1 arg2", mock_context)
        assert success is True

    async def test_parse_and_execute_max_args_validation(self, parser, mock_context):
        """Test command with max argument validation."""
        command = MockCommand("test")
        command.get_max_args = lambda: 2
        parser.register_command(command)

        # Test with too many arguments
        success, response = await parser.parse_and_execute("/test arg1 arg2 arg3", mock_context)
        assert success is False
        assert "at most 2 argument" in response

    async def test_parse_and_execute_custom_validation(self, parser, mock_context):
        """Test command with custom validation."""
        command = MockCommand("test")
        command.validate_args = lambda args: (
            args[0].isdigit() if args else False,
            "First arg must be number",
        )
        parser.register_command(command)

        # Test with invalid argument
        success, response = await parser.parse_and_execute("/test abc", mock_context)
        assert success is False
        assert "First arg must be number" in response

        # Test with valid argument
        success, response = await parser.parse_and_execute("/test 123", mock_context)
        assert success is True

    async def test_parse_and_execute_exception_handling(self, parser, mock_context):
        """Test exception handling during command execution."""
        command = MockCommand("test")
        command.execute = AsyncMock(side_effect=Exception("Test error"))
        parser.register_command(command)

        success, response = await parser.parse_and_execute("/test", mock_context)

        assert success is False
        assert "Error executing /test" in response
        assert "Test error" in response

    def test_find_similar_commands(self, parser):
        """Test finding similar commands for suggestions."""
        parser.register_command(MockCommand("help"))
        parser.register_command(MockCommand("hello"))
        parser.register_command(MockCommand("world"))

        similar = parser._find_similar_commands("hell")
        assert "hello" in [cmd[1:] for cmd in similar]

        similar = parser._find_similar_commands("xyz")
        assert len(similar) == 0

    def test_get_command_names(self, parser):
        """Test getting all command names."""
        parser.register_command(MockCommand("help"))
        parser.register_command(MockCommand("test"))

        names = parser.get_command_names()
        assert set(names) == {"help", "test"}

    def test_get_command_by_name(self, parser):
        """Test getting command by name."""
        command = MockCommand("test", aliases=["t"])
        parser.register_command(command)

        # Test by name
        found = parser.get_command_by_name("test")
        assert found == command

        # Test by alias
        found = parser.get_command_by_name("t")
        assert found == command

        # Test non-existent
        found = parser.get_command_by_name("nonexistent")
        assert found is None

    def test_get_commands_by_category(self, parser):
        """Test getting commands grouped by category."""
        parser.register_command(MockCommand("help", category="system"))
        parser.register_command(MockCommand("test", category="debug"))
        parser.register_command(MockCommand("status", category="system"))

        categories = parser.get_commands_by_category()
        assert "system" in categories
        assert "debug" in categories
        assert len(categories["system"]) == 2
        assert len(categories["debug"]) == 1

    def test_get_help_text_general(self, parser):
        """Test getting general help text."""
        parser.register_command(MockCommand("help", "Show help", category="system"))
        parser.register_command(
            MockCommand("test", "Test command", aliases=["t"], category="debug")
        )

        help_text = parser.get_help_text()

        assert "Available commands" in help_text
        assert "System:" in help_text
        assert "Debug:" in help_text
        assert "/help" in help_text
        assert "/test|t" in help_text
        assert "Mock command for testing" in help_text

    def test_get_help_text_specific(self, parser):
        """Test getting help for specific command."""
        command = MockCommand("test", response="resp", description="Test command description", aliases=["t"])
        parser.register_command(command)

        help_text = parser.get_help_text("test")

        assert "/test|t" in help_text
        assert "Test command description" in help_text
        assert "Aliases: t" in help_text

        # Test with alias
        help_text = parser.get_help_text("t")
        assert "/test|t" in help_text

        # Test non-existent command
        help_text = parser.get_help_text("nonexistent")
        assert "Unknown command" in help_text
