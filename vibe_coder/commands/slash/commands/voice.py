"""Voice and interaction commands."""

from typing import List

from vibe_coder.commands.slash.base import CommandContext, SlashCommand


class SpeakCommand(SlashCommand):
    """Read text out loud."""

    def __init__(self):
        super().__init__(
            name="speak",
            description="Read the last AI response out loud",
            aliases=["say", "tts"],
            category="voice",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # Check for dependencies
        try:
            import pyttsx3
        except ImportError:
            return "Voice support requires `pyttsx3`. Install it with `pip install pyttsx3`."

        if not context.chat_history:
            return "No history to speak."

        last_ai_msg = None
        for msg in reversed(context.chat_history):
            if msg.role.value == "assistant":
                last_ai_msg = msg
                break

        if not last_ai_msg:
            return "No AI response found to speak."

        text = last_ai_msg.content
        if not text:
            return "Last response was empty."

        try:
            # Run TTS in a thread or separate process to avoid blocking async loop?
            # pyttsx3 runAndWait is blocking.
            import threading

            def speak():
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()

            threading.Thread(target=speak).start()
            return "🗣️ Speaking..."

        except Exception as e:
            return f"TTS failed: {e}"


class ListenCommand(SlashCommand):
    """Listen for voice input."""

    def __init__(self):
        super().__init__(
            name="listen",
            description="Listen for voice input",
            aliases=["hear", "stt"],
            category="voice",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        return "Voice input requires additional setup and UI integration. (Placeholder)"
