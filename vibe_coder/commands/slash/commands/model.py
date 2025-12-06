"""Model switching command."""

from typing import List, Tuple

import questionary

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.config.manager import config_manager


class ModelCommand(SlashCommand):
    """
    Switch current model or provider.

    Usage:
        /model [model_name]
    """

    name = "model"
    description = "Switch AI model"

    async def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, str]:
        provider = context.current_provider

        if not args:
            # Interactive selection
            # We don't have a direct way to fetch ALL models from the provider dynamically
            # without an API call, but we can try to list them if supported,
            # or just let user type.

            # Since we are in a slash command context, interactive prompts might be tricky
            # if the context doesn't expose the client directly to list models.
            # However, we can use `questionary` here.

            # Note: listing models usually requires an API client.
            # For now, we will just allow updating the config.

            current_model = provider.model or "default"
            new_model = await questionary.text(
                f"Current model is '{current_model}'. Enter new model name:",
                default=current_model
            ).ask_async()

            if new_model and new_model != current_model:
                provider.model = new_model
                config_manager.set_provider(provider.name, provider)
                return True, f"Model switched to: {new_model}"

            return True, f"Model kept as: {current_model}"

        else:
            new_model = args[0]
            provider.model = new_model
            config_manager.set_provider(provider.name, provider)
            return True, f"Model switched to: {new_model}"
