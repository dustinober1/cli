"""Tests for voice commands."""

import pytest
from unittest.mock import patch, MagicMock

from vibe_coder.commands.slash.commands.voice import SpeakCommand, ListenCommand
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.types.api import ApiMessage, MessageRole
from vibe_coder.types.config import AIProvider

@pytest.fixture
def context():
    return CommandContext(
        chat_history=[ApiMessage(role=MessageRole.ASSISTANT, content="Hello")],
        current_provider=AIProvider(name="test", api_key="key", endpoint="url"),
        working_directory="."
    )

@pytest.mark.asyncio
async def test_speak_command_success(context):
    with patch("builtins.__import__") as mock_import:
        mock_pyttsx3 = MagicMock()

        # When pyttsx3 is imported, return mock
        def side_effect(name, *args, **kwargs):
            if name == "pyttsx3":
                return mock_pyttsx3
            return __import__(name, *args, **kwargs)

        # This is tricky because we are patching builtins.import which is used everywhere.
        # Easier to patch the module if it's already imported or mock it in sys.modules
        pass

    with patch.dict("sys.modules", {"pyttsx3": MagicMock()}):
        cmd = SpeakCommand()
        response = await cmd.execute([], context)
        assert "Speaking" in response

@pytest.mark.asyncio
async def test_speak_command_no_history():
    ctx = CommandContext(chat_history=[], current_provider=None, working_directory=".")
    cmd = SpeakCommand()
    with patch.dict("sys.modules", {"pyttsx3": MagicMock()}):
        response = await cmd.execute([], ctx)
        assert "No history" in response

@pytest.mark.asyncio
async def test_listen_command(context):
    cmd = ListenCommand()
    response = await cmd.execute([], context)
    assert "Placeholder" in response
