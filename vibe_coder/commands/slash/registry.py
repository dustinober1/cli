"""Command registry for slash commands."""

from typing import Dict, List, Optional

from .base import SlashCommand
from .parser import SlashCommandParser


class CommandRegistry:
    """Registry for managing slash commands."""

    def __init__(self):
        self.parser = SlashCommandParser()
        self._initialized = False

    def register(self, command: SlashCommand) -> None:
        """Register a slash command."""
        self.parser.register_command(command)

    def get_parser(self) -> SlashCommandParser:
        """Get the command parser."""
        return self.parser

    def is_initialized(self) -> bool:
        """Check if the registry has been initialized."""
        return self._initialized

    def mark_initialized(self) -> None:
        """Mark the registry as initialized."""
        self._initialized = True

    def get_all_commands(self) -> List[SlashCommand]:
        """Get all registered commands."""
        return list(self.parser.commands.values())

    def get_command_count(self) -> int:
        """Get the total number of registered commands."""
        return len(self.parser.commands)


# Global instance
command_registry = CommandRegistry()