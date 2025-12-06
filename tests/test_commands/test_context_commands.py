"""Tests for context commands."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from vibe_coder.commands.slash.commands.context import ContextCommand, SummarizeCommand, IgnoreCommand
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, MessageRole, ApiResponse

@pytest.fixture
def context():
    return CommandContext(
        chat_history=[
            ApiMessage(role=MessageRole.SYSTEM, content="System prompt"),
            ApiMessage(role=MessageRole.USER, content="Hello"),
            ApiMessage(role=MessageRole.ASSISTANT, content="Hi"),
        ],
        current_provider=AIProvider(name="test", api_key="key", endpoint="url"),
        working_directory="."
    )

@pytest.mark.asyncio
async def test_context_command(context):
    cmd = ContextCommand()
    response = await cmd.execute([], context)
    assert "Context Summary" in response
    assert "**Messages:** 3" in response
    assert "Provider:** test" in response or "Provider:** test" in response # Markdown format

@pytest.mark.asyncio
async def test_summarize_command(context):
    cmd = SummarizeCommand()

    with patch("vibe_coder.api.factory.ClientFactory.create_client") as mock_factory:
        mock_client = AsyncMock()
        mock_client.send_request.return_value = ApiResponse(content="Summary text")
        mock_factory.return_value = mock_client

        response = await cmd.execute([], context)

        assert "Summary" in response
        assert "Summary text" in response
        mock_client.send_request.assert_awaited_once()
        mock_client.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_ignore_command(context):
    cmd = IgnoreCommand()
    response = await cmd.execute(["*.log"], context)
    assert "Added '*.log' to ignore list" in response

    response = await cmd.execute([], context)
    assert "Usage" in response
