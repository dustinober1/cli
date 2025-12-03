"""Base classes for slash commands."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from vibe_coder.types.api import ApiMessage
from vibe_coder.types.config import AIProvider


@dataclass
class CommandContext:
    """Context for slash command execution."""
    chat_history: List[ApiMessage]
    current_provider: AIProvider
    working_directory: str
    git_info: Optional[Dict[str, Any]] = None
    file_cache: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def get_file_path(self, relative_path: str) -> str:
        """Get absolute file path from relative path."""
        import os
        return os.path.join(self.working_directory, relative_path)

    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        return self.git_info is not None


class SlashCommand(ABC):
    """Base class for all slash commands."""

    def __init__(
        self,
        name: str,
        description: str,
        aliases: Optional[List[str]] = None,
        category: str = "general"
    ):
        self.name = name
        self.description = description
        self.aliases = aliases or []
        self.category = category

    @abstractmethod
    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the command with given arguments and context."""
        pass

    def validate_args(self, args: List[str]) -> Tuple[bool, str]:
        """
        Validate command arguments.
        Returns (is_valid, error_message).
        """
        return True, ""

    def get_usage(self) -> str:
        """Get usage string for the command."""
        alias_list = f"|{'|'.join(self.aliases)}" if self.aliases else ""
        return f"/{self.name}{alias_list}"

    def get_help(self) -> str:
        """Get detailed help for the command."""
        help_text = f"{self.get_usage()}\n"
        help_text += f"  {self.description}\n"

        if self.aliases:
            help_text += f"  Aliases: {', '.join(self.aliases)}\n"

        return help_text

    def requires_git_repo(self) -> bool:
        """Check if command requires a Git repository."""
        return False

    def requires_file(self) -> bool:
        """Check if command requires a file argument."""
        return False

    def get_min_args(self) -> int:
        """Get minimum number of arguments required."""
        return 0

    def get_max_args(self) -> Optional[int]:
        """Get maximum number of arguments allowed (None for unlimited)."""
        return None