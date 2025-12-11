"""Tests for slash command base classes."""

import pytest
from unittest.mock import Mock, patch

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.types.api import ApiMessage, MessageRole
from vibe_coder.types.config import AIProvider


class TestCommandContext:
    """Test CommandContext class."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock AI provider."""
        return AIProvider(
            name="test-provider",
            api_key="test-key",
            endpoint="https://api.test.com",
            model="test-model",
            temperature=0.7,
        )

    @pytest.fixture
    def sample_context(self, mock_provider):
        """Create a sample command context."""
        return CommandContext(
            chat_history=[
                ApiMessage(role=MessageRole.USER, content="Hello"),
                ApiMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
            ],
            current_provider=mock_provider,
            working_directory="/test/dir",
        )

    def test_command_context_creation(self, sample_context):
        """Test CommandContext can be created."""
        assert len(sample_context.chat_history) == 2
        assert sample_context.current_provider.name == "test-provider"
        assert sample_context.working_directory == "/test/dir"

    def test_get_file_path(self, sample_context):
        """Test getting absolute file path."""
        result = sample_context.get_file_path("subdir/file.py")
        assert result == "/test/dir/subdir/file.py"

    def test_get_file_path_with_absolute(self, sample_context):
        """Test getting file path with absolute path."""
        result = sample_context.get_file_path("/absolute/path.py")
        # Should join as-is even if absolute
        assert result == "/test/dir/absolute/path.py"

    def test_is_git_repo_no_info(self, sample_context):
        """Test is_git_repo when no git info."""
        assert not sample_context.is_git_repo()

    def test_is_git_repo_with_info(self, sample_context):
        """Test is_git_repo with git info."""
        sample_context.git_info = {"branch": "main", "commit": "abc123"}
        assert sample_context.is_git_repo()


class TestSlashCommand:
    """Test SlashCommand base class."""

    class ConcreteCommand(SlashCommand):
        """Concrete implementation for testing."""

        async def execute(self, args, context):
            return f"Executed with args: {args}"

    @pytest.fixture
    def command(self):
        """Create a concrete command for testing."""
        return self.ConcreteCommand(
            name="test",
            description="Test command",
            aliases=["t", "test-cmd"],
            category="testing"
        )

    def test_command_creation(self, command):
        """Test command creation."""
        assert command.name == "test"
        assert command.description == "Test command"
        assert command.aliases == ["t", "test-cmd"]
        assert command.category == "testing"

    def test_command_creation_defaults(self):
        """Test command creation with default values."""
        cmd = self.ConcreteCommand("simple", "Simple command")
        assert cmd.name == "simple"
        assert cmd.description == "Simple command"
        assert cmd.aliases == []
        assert cmd.category == "general"

    def test_get_usage_no_aliases(self):
        """Test get_usage with no aliases."""
        cmd = self.ConcreteCommand("cmd", "Command")
        assert cmd.get_usage() == "/cmd"

    def test_get_usage_with_aliases(self, command):
        """Test get_usage with aliases."""
        assert command.get_usage() == "/test|t|test-cmd"

    def test_get_help(self, command):
        """Test get_help method."""
        help_text = command.get_help()
        assert "/test|t|test-cmd" in help_text
        assert "Test command" in help_text
        assert "Aliases: t, test-cmd" in help_text

    def test_validate_args_default(self, command):
        """Test default argument validation."""
        valid, error = command.validate_args([])
        assert valid
        assert error == ""

    def test_requires_git_repo_default(self, command):
        """Test default git repo requirement."""
        assert not command.requires_git_repo()

    def test_requires_file_default(self, command):
        """Test default file requirement."""
        assert not command.requires_file()

    def test_get_min_args_default(self, command):
        """Test default minimum args."""
        assert command.get_min_args() == 0

    def test_get_max_args_default(self, command):
        """Test default maximum args."""
        assert command.get_max_args() is None

    @pytest.mark.asyncio
    async def test_execute(self, command):
        """Test command execution."""
        result = await command.execute(["arg1", "arg2"], None)
        assert result == "Executed with args: ['arg1', 'arg2']"


class TestExtendedSlashCommand:
    """Test extended SlashCommand with overridden methods."""

    class ExtendedCommand(SlashCommand):
        """Extended command for testing."""

        def __init__(self):
            super().__init__("extended", "Extended command")
            self._min_args = 1
            self._max_args = 3
            self._requires_git = True
            self._requires_file = True

        async def execute(self, args, context):
            if len(args) < self._min_args:
                return f"Need at least {self._min_args} args"
            return f"Executed with {len(args)} args"

        def validate_args(self, args):
            if len(args) < self._min_args:
                return False, f"Need at least {self._min_args} arguments"
            if len(args) > self._max_args:
                return False, f"Too many arguments, max {self._max_args}"
            return True, ""

        def requires_git_repo(self):
            return self._requires_git

        def requires_file(self):
            return self._requires_file

        def get_min_args(self):
            return self._min_args

        def get_max_args(self):
            return self._max_args

    @pytest.fixture
    def extended_command(self):
        """Create an extended command."""
        return self.ExtendedCommand()

    def test_extended_command_properties(self, extended_command):
        """Test overridden properties."""
        assert extended_command.requires_git_repo()
        assert extended_command.requires_file()
        assert extended_command.get_min_args() == 1
        assert extended_command.get_max_args() == 3

    def test_validate_args_success(self, extended_command):
        """Test successful argument validation."""
        valid, error = extended_command.validate_args(["arg1", "arg2"])
        assert valid
        assert error == ""

    def test_validate_args_too_few(self, extended_command):
        """Test validation with too few args."""
        valid, error = extended_command.validate_args([])
        assert not valid
        assert "at least 1" in error

    def test_validate_args_too_many(self, extended_command):
        """Test validation with too many args."""
        valid, error = extended_command.validate_args(["a", "b", "c", "d"])
        assert not valid
        assert "Too many" in error
        assert "max 3" in error

    @pytest.mark.asyncio
    async def test_extended_execute_success(self, extended_command):
        """Test successful execution."""
        result = await extended_command.execute(["arg1"], None)
        assert result == "Executed with 1 args"

    @pytest.mark.asyncio
    async def test_extended_execute_failure(self, extended_command):
        """Test execution failure."""
        result = await extended_command.execute([], None)
        assert "Need at least 1" in result