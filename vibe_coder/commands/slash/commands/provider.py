"""Provider switching command."""

from typing import List, Tuple

import questionary

from vibe_coder.commands.slash.base import BaseSlashCommand, CommandContext
from vibe_coder.config.manager import config_manager


class ProviderCommand(BaseSlashCommand):
    """
    Switch AI provider.

    Usage:
        /provider [name]
    """

    name = "provider"
    description = "Switch AI provider"

    async def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, str]:
        if not args:
            # Interactive selection
            providers = config_manager.list_providers()
            if not providers:
                return False, "No providers configured."

            choice = await questionary.select(
                "Select provider:",
                choices=providers,
                default=context.current_provider.name
            ).ask_async()

            if choice:
                config_manager.set_current_provider(choice)
                # We need to signal the chat loop to reload the client.
                # The ChatCommand checks `config_manager.get_current_provider()`
                # but might hold a reference to the old client.
                # Returning a message is fine, the user might need to restart chat
                # or we rely on ChatCommand re-checking.
                # Looking at chat.py, it calls `_setup_provider` at start of `run`,
                # but inside `_chat_loop` it doesn't refresh automatically.
                # However, slash commands return `True` to continue chat.
                # The ChatCommand context holds `current_provider` which is just a reference.

                # To make this seamless, the ChatCommand needs to know about the change.
                # But SlashCommand architecture returns (success, message).
                # We can return a specific message that tells user to restart or handle it.

                return True, f"Provider switched to: {choice}. (Note: You may need to restart chat for full effect if connection is persistent)"

            return True, "Selection cancelled."

        else:
            name = args[0]
            if not config_manager.has_provider(name):
                return False, f"Provider '{name}' not found."

            config_manager.set_current_provider(name)
            return True, f"Provider switched to: {name}"
