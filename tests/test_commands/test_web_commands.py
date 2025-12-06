"""Tests for web commands."""

import pytest
from unittest.mock import AsyncMock

from vibe_coder.commands.slash.commands.web import WebCommand, DocsCommand
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.types.config import AIProvider

@pytest.fixture
def context():
    ctx = CommandContext(
        chat_history=[],
        current_provider=AIProvider(name="test", api_key="key", endpoint="url"),
        working_directory="."
    )
    ctx.mcp_manager = AsyncMock()
    return ctx

@pytest.mark.asyncio
async def test_web_command(context):
    context.mcp_manager.get_all_tools.return_value = [
        {"function": {"name": "search_web", "description": "Search web"}}
    ]
    context.mcp_manager.execute_tool.return_value = "Search results"

    cmd = WebCommand()
    response = await cmd.execute(["python"], context)

    assert "Search Result" in response
    assert "Search results" in response
    context.mcp_manager.execute_tool.assert_awaited_with("search_web", {"query": "python"})

@pytest.mark.asyncio
async def test_web_command_no_tool(context):
    context.mcp_manager.get_all_tools.return_value = []

    cmd = WebCommand()
    response = await cmd.execute(["python"], context)

    assert "No web search tool found" in response

@pytest.mark.asyncio
async def test_docs_command(context):
    context.mcp_manager.get_all_tools.return_value = [
        {"function": {"name": "search_docs", "description": "Search docs"}}
    ]
    context.mcp_manager.execute_tool.return_value = "Docs results"

    cmd = DocsCommand()
    response = await cmd.execute(["python"], context)

    assert "Docs Result" in response
    assert "Docs results" in response
