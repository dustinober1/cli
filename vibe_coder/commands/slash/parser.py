"""Slash command parser and router."""

import re
import shlex
from typing import Dict, List, Optional, Callable, Any

from .base import SlashCommand, CommandContext


class SlashCommandParser:
    """Parse and route slash commands in chat."""

    def __init__(self):
        self.commands: Dict[str, SlashCommand] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command_name

    def register_command(
        self,
        command: SlashCommand,
        aliases: Optional[List[str]] = None
    ) -> None:
        """Register a slash command with optional aliases."""
        # Register main command
        self.commands[command.name] = command

        # Register aliases
        for alias in command.aliases:
            self.aliases[alias] = command.name

        # Register additional aliases if provided
        if aliases:
            for alias in aliases:
                self.aliases[alias] = command.name

    def is_slash_command(self, message: str) -> bool:
        """Check if message contains a slash command."""
        return message.strip().startswith('/')

    def parse_command(self, message: str) -> Optional[tuple[str, List[str]]]:
        """
        Parse a slash command message.
        Returns (command_name, args) if valid, None otherwise.
        """
        if not self.is_slash_command(message):
            return None

        # Remove leading slash and strip whitespace
        command_part = message.strip()[1:].strip()
        if not command_part:
            return None

        # Use shlex to properly handle quoted arguments
        try:
            parts = shlex.split(command_part)
        except ValueError:
            # Fallback to simple split if shlex fails
            parts = command_part.split()

        if not parts:
            return None

        command_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Check if it's an alias
        if command_name in self.aliases:
            command_name = self.aliases[command_name]

        return command_name, args

    async def parse_and_execute(
        self,
        message: str,
        context: CommandContext
    ) -> tuple[bool, str]:
        """
        Parse message and execute appropriate command.
        Returns (success, response).
        """
        parsed = self.parse_command(message)
        if not parsed:
            return False, "Invalid command format"

        command_name, args = parsed

        if command_name not in self.commands:
            # Find similar commands for suggestions
            similar = self._find_similar_commands(command_name)
            if similar:
                suggestion = f"Did you mean: {', '.join(similar)}?"
                return False, f"Unknown command: /{command_name}. {suggestion}"
            else:
                return False, f"Unknown command: /{command_name}. Type /help for available commands."

        command = self.commands[command_name]

        # Check Git repository requirement
        if command.requires_git_repo() and not context.is_git_repo():
            return False, f"Command /{command_name} requires a Git repository."

        # Validate arguments
        min_args = command.get_min_args()
        max_args = command.get_max_args()

        if len(args) < min_args:
            return False, f"Command /{command_name} requires at least {min_args} argument(s)."

        if max_args is not None and len(args) > max_args:
            return False, f"Command /{command_name} accepts at most {max_args} argument(s)."

        # Validate specific arguments
        is_valid, error_msg = command.validate_args(args)
        if not is_valid:
            return False, f"Invalid arguments: {error_msg}"

        try:
            # Execute the command
            response = await command.execute(args, context)
            return True, response
        except Exception as e:
            return False, f"Error executing /{command_name}: {str(e)}"

    def _find_similar_commands(self, command_name: str, max_suggestions: int = 3) -> List[str]:
        """Find similar command names for suggestions."""
        import difflib

        all_commands = list(self.commands.keys()) + list(self.aliases.keys())
        similar = difflib.get_close_matches(command_name, all_commands, n=max_suggestions, cutoff=0.6)
        return [f"/{cmd}" for cmd in similar]

    def get_command_names(self) -> List[str]:
        """Get list of all registered command names."""
        return list(self.commands.keys())

    def get_command_by_name(self, name: str) -> Optional[SlashCommand]:
        """Get command by name or alias."""
        # Check if it's an alias
        if name in self.aliases:
            name = self.aliases[name]

        return self.commands.get(name)

    def get_commands_by_category(self) -> Dict[str, List[SlashCommand]]:
        """Get commands grouped by category."""
        categories = {}
        for command in self.commands.values():
            if command.category not in categories:
                categories[command.category] = []
            categories[command.category].append(command)
        return categories

    def get_help_text(self, command_name: Optional[str] = None) -> str:
        """Generate help text for commands."""
        if command_name:
            command = self.get_command_by_name(command_name)
            if command:
                return command.get_help()
            else:
                return f"Unknown command: /{command_name}"
        else:
            # Show all commands grouped by category
            help_text = "Available commands:\n\n"

            categories = self.get_commands_by_category()
            for category, commands in sorted(categories.items()):
                help_text += f"{category.title()}:\n"
                for command in sorted(commands, key=lambda c: c.name):
                    alias_list = f"|{'|'.join(command.aliases)}" if command.aliases else ""
                    help_text += f"  /{command.name}{alias_list} - {command.description}\n"
                help_text += "\n"

            help_text += "Type /help <command> for detailed help on a specific command."
            return help_text