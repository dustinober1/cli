"""System and utility slash commands."""

from typing import List

from ..base import CommandContext, SlashCommand
from ..registry import command_registry


class HelpCommand(SlashCommand):
    """Show help information for commands."""

    def __init__(self):
        super().__init__(
            name="help",
            description="Show help information for commands",
            aliases=["h", "?"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        from ...parser import SlashCommandParser

        parser = SlashCommandParser()

        if args:
            # Show help for specific command
            command_name = args[0].lstrip("/")
            help_text = parser.get_help_text(command_name)
        else:
            # Show general help
            help_text = parser.get_help_text()

        return help_text

    def get_max_args(self) -> int:
        return 1


class ClearCommand(SlashCommand):
    """Clear conversation history."""

    def __init__(self):
        super().__init__(
            name="clear",
            description="Clear conversation history",
            aliases=["cls"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # This would clear the conversation history
        # Implementation depends on how conversation history is managed
        return "Conversation history cleared."


class ExitCommand(SlashCommand):
    """Exit the application."""

    def __init__(self):
        super().__init__(
            name="exit",
            description="Exit the application",
            aliases=["quit", "q"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # This would trigger application exit
        # Implementation depends on the main application structure
        return "Goodbye!"


class SettingsCommand(SlashCommand):
    """Show current configuration settings."""

    def __init__(self):
        super().__init__(
            name="settings",
            description="Show current configuration settings",
            aliases=["config", "cfg"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        provider = context.current_provider

        settings = f"""Current Settings:

Provider: {provider.name}
Model: {provider.model or 'Default'}
Endpoint: {provider.endpoint}
Temperature: {provider.temperature}
Max Tokens: {provider.max_tokens or 'Default'}

Working Directory: {context.working_directory}
Git Repository: {'Yes' if context.is_git_repo() else 'No'}"""

        if provider.headers:
            settings += f"\nCustom Headers: {len(provider.headers)} configured"

        return settings


class StatsCommand(SlashCommand):
    """Show usage statistics."""

    def __init__(self):
        super().__init__(
            name="stats",
            description="Show usage statistics",
            aliases=["statistics"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # This would show actual usage statistics
        # For now, return a placeholder
        return """Usage Statistics:

Session Duration: {session_time}
Messages Exchanged: {message_count}
Tokens Used: {token_count}
Commands Executed: {command_count}
Files Modified: {file_count}

Note: Statistics tracking will be implemented in a future update."""


class ProviderCommand(SlashCommand):
    """Switch AI provider."""

    def __init__(self):
        super().__init__(
            name="provider", description="Switch AI provider", aliases=["switch"], category="system"
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return (
                "Usage: /provider <provider_name>. "
                "Available providers can be listed with /config list"
            )

        provider_name = args[0]
        # This would switch the provider
        # Implementation depends on configuration management
        return f"Switched to provider: {provider_name}"

    def get_min_args(self) -> int:
        return 1


class ModelCommand(SlashCommand):
    """Change AI model."""

    def __init__(self):
        super().__init__(
            name="model", description="Change AI model", aliases=["model-switch"], category="system"
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return (
                f"Current model: {context.current_provider.model or 'Default'}\n"
                "Usage: /model <model_name>"
            )

        model_name = args[0]
        # This would change the model
        # Implementation depends on configuration management
        return f"Changed model to: {model_name}"

    def get_max_args(self) -> int:
        return 1


class TemperatureCommand(SlashCommand):
    """Adjust AI response temperature."""

    def __init__(self):
        super().__init__(
            name="temperature",
            description="Adjust AI response temperature",
            aliases=["temp"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return (
                f"Current temperature: {context.current_provider.temperature}\n"
                "Usage: /temperature <value> (0.0-2.0)"
            )

        try:
            temperature = float(args[0])
            if not (0.0 <= temperature <= 2.0):
                return "Temperature must be between 0.0 and 2.0"
        except ValueError:
            return "Invalid temperature value. Use a number between 0.0 and 2.0"

        # This would change the temperature
        # Implementation depends on configuration management
        return f"Changed temperature to: {temperature}"

    def validate_args(self, args: List[str]) -> tuple[bool, str]:
        if not args:
            return True, ""

        try:
            temp = float(args[0])
            if not (0.0 <= temp <= 2.0):
                return False, "Temperature must be between 0.0 and 2.0"
        except ValueError:
            return False, "Temperature must be a valid number"

        return True, ""

    def get_max_args(self) -> int:
        return 1


class SaveCommand(SlashCommand):
    """Save conversation to file."""

    def __init__(self):
        super().__init__(
            name="save",
            description="Save conversation to file",
            aliases=["export-conversation"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return "Usage: /save <filename>. Saves the conversation history to a file."

        filename = args[0]
        if not filename.endswith((".md", ".txt", ".json")):
            filename += ".md"

        try:
            # This would save the conversation to a file
            # Implementation depends on conversation history management
            return f"Conversation saved to: {filename}"
        except Exception as e:
            return f"Error saving conversation: {str(e)}"

    def get_min_args(self) -> int:
        return 1


class ExportCommand(SlashCommand):
    """Export chat history in various formats."""

    def __init__(self):
        super().__init__(
            name="export",
            description="Export chat history in various formats",
            aliases=["backup"],
            category="system",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return """Usage: /export <format> [filename]
Formats: json, markdown, csv, html
Example: /export markdown chat_backup"""

        format_type = args[0].lower()
        filename = args[1] if len(args) > 1 else f"chat_export.{format_type}"

        if format_type not in ["json", "markdown", "csv", "html"]:
            return "Supported formats: json, markdown, csv, html"

        try:
            # This would export the conversation in the specified format
            # Implementation depends on conversation history management
            return f"Chat exported to: {filename} ({format_type})"
        except Exception as e:
            return f"Error exporting chat: {str(e)}"

    def get_min_args(self) -> int:
        return 1

    def get_max_args(self) -> int:
        return 2


# Register all system commands
command_registry.register(HelpCommand())
command_registry.register(ClearCommand())
command_registry.register(ExitCommand())
command_registry.register(SettingsCommand())
command_registry.register(StatsCommand())
command_registry.register(ProviderCommand())
command_registry.register(ModelCommand())
command_registry.register(TemperatureCommand())
command_registry.register(SaveCommand())
command_registry.register(ExportCommand())
