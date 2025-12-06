"""Tests for MCP tool commands."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from vibe_coder.commands.slash.commands.mcp_tools import ToolsCommand, ToolHelpCommand, InspectMCPCommand
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
async def test_tools_command(context):
    context.mcp_manager.get_all_tools.return_value = [
        {"function": {"name": "tool1", "description": "desc1"}}
    ]

    cmd = ToolsCommand()
    response = await cmd.execute([], context)
    assert "Available Tools" in response
    assert "tool1" in response
    assert "desc1" in response

@pytest.mark.asyncio
async def test_tools_command_empty(context):
    context.mcp_manager.get_all_tools.return_value = []

    cmd = ToolsCommand()
    response = await cmd.execute([], context)
    assert "No tools available" in response

@pytest.mark.asyncio
async def test_tools_command_no_manager():
    ctx = CommandContext(chat_history=[], current_provider=None, working_directory=".")
    cmd = ToolsCommand()
    response = await cmd.execute([], ctx)
    assert "MCP Manager not available" in response

@pytest.mark.asyncio
async def test_tool_help_command(context):
    context.mcp_manager.get_all_tools.return_value = [
        {"function": {"name": "tool1", "description": "desc1", "parameters": {"type": "object"}}}
    ]

    cmd = ToolHelpCommand()
    response = await cmd.execute(["tool1"], context)
    assert "Tool: tool1" in response
    assert "desc1" in response
    assert "Parameters" in response

@pytest.mark.asyncio
async def test_tool_help_not_found(context):
    context.mcp_manager.get_all_tools.return_value = []
    cmd = ToolHelpCommand()
    response = await cmd.execute(["tool1"], context)
    assert "not found" in response

@pytest.mark.asyncio
async def test_inspect_mcp_command(context):
    context.mcp_manager.sessions = {"server1": MagicMock()}
    cmd = InspectMCPCommand()
    response = await cmd.execute([], context)
    assert "server1" in response
    assert "Connected" in response
