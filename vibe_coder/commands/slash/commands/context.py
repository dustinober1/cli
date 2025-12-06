"""Context and memory management slash commands."""

from typing import List

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.types.api import MessageRole


class ContextCommand(SlashCommand):
    """Show current context information."""

    def __init__(self):
        super().__init__(
            name="context",
            description="Show summary of current chat context and memory",
            aliases=["ctx", "memory"],
            category="context",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        history_len = len(context.chat_history)

        # Calculate token usage approximation
        total_chars = sum(len(m.content) for m in context.chat_history)
        approx_tokens = total_chars // 4

        result = f"🧠 **Context Summary**\n\n"
        result += f"**Messages:** {history_len}\n"
        result += f"**Approx. Tokens:** {approx_tokens}\n"
        result += f"**Provider:** {context.current_provider.name} ({context.current_provider.model})\n"
        result += f"**Working Directory:** {context.working_directory}\n"

        # If we had file context tracking, we'd list it here
        # For now, we list the last few messages roles
        result += "\n**Recent History:**\n"
        for i, msg in enumerate(context.chat_history[-5:], 1):
            role_icon = "👤" if msg.role == MessageRole.USER else "🤖" if msg.role == MessageRole.ASSISTANT else "🛠️" if msg.role == MessageRole.TOOL else "⚙️"
            preview = msg.content[:50].replace("\n", " ") + "..." if len(msg.content) > 50 else msg.content
            result += f"{role_icon} **{msg.role.name}**: {preview}\n"

        return result


class SummarizeCommand(SlashCommand):
    """Summarize conversation or content."""

    def __init__(self):
        super().__init__(
            name="summarize",
            description="Summarize the current conversation",
            aliases=["summary", "sum"],
            category="context",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # This requires calling the AI, which is usually done via the Chat loop.
        # However, SlashCommands execute and return a string.
        # To make the AI actually summarize, we might need to inject a message into the chat history
        # that triggers the AI to summarize, OR we return a special signal.

        # But wait, the user wants the command to *do* it.
        # Since we don't have access to the `client` in `CommandContext` (only `current_provider`),
        # we can't make an API call easily here without refactoring `CommandContext`.

        # Let's check `CommandContext` in `base.py`. It has `current_provider`.
        # It does NOT have the client.

        # Option A: Add `client` to `CommandContext`.
        # Option B: Use `ClientFactory` to create a temporary client.

        # I'll go with Option B for now as it's cleaner than passing the stateful client around if not needed.

        from vibe_coder.api.factory import ClientFactory
        from vibe_coder.types.api import ApiMessage, MessageRole

        client = ClientFactory.create_client(context.current_provider)

        try:
            # Construct a summarization prompt
            # We use the existing history but append a system instruction for summarization
            # actually we can just send a user message "Summarize the conversation above"
            # but that adds to the history.

            # If we want a "meta" summary without polluting history too much:
            prompt = "Please provide a concise summary of our conversation so far, highlighting key decisions and code changes."

            # Create a temporary history for this request
            temp_history = context.chat_history.copy()
            temp_history.append(ApiMessage(role=MessageRole.USER, content=prompt))

            response = await client.send_request(temp_history)
            return f"📝 **Summary**\n\n{response.content}"

        except Exception as e:
            return f"Failed to generate summary: {e}"
        finally:
            await client.close()


class IgnoreCommand(SlashCommand):
    """Manage ignored files for context."""

    def __init__(self):
        super().__init__(
            name="ignore",
            description="Add pattern to session ignore list",
            aliases=["exclude"],
            category="context",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return "Usage: /ignore <pattern>. Currently ignored: (Not tracked in this MVP yet)"

        pattern = args[0]
        # context doesn't have a place to store this yet.
        # We need to update CommandContext to support session state.
        # But CommandContext is re-created on every command in `chat.py`.
        # So we need to store it in `chat.py` (ChatCommand) and pass it in.

        # For now, return a placeholder until we update `chat.py` state management.
        return f"Added '{pattern}' to ignore list (Placeholder - Context state update needed)."
