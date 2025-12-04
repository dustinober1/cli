"""
Slash command system for Vibe Coder.

This module provides the infrastructure for parsing and executing
slash commands within the chat interface.
"""

from .base import CommandContext, SlashCommand
from .parser import SlashCommandParser
from .registry import command_registry

__all__ = [
    "SlashCommandParser",
    "SlashCommand",
    "CommandContext",
    "command_registry",
]
