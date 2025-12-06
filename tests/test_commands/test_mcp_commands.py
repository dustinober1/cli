"""Tests for MCP commands."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from vibe_coder.commands.slash.commands.mcp import MCPCommand
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.types.config import AIProvider, MCPServer
from vibe_coder.config.manager import config_manager

@pytest.fixture
def context():
    return CommandContext(
        chat_history=[],
        current_provider=AIProvider(name="test", api_key="key", endpoint="url"),
        working_directory="."
    )

@pytest.fixture
def mcp_command():
    return MCPCommand()

@pytest.mark.asyncio
async def test_mcp_list(mcp_command, context):
    # Mock config_manager
    with patch("vibe_coder.commands.slash.commands.mcp.config_manager") as mock_config:
        mock_config.list_mcp_servers.return_value = ["server1"]
        mock_config.get_mcp_server.return_value = MCPServer(name="server1", command="cmd", args=[])

        success, response = await mcp_command.execute(["list"], context)
        assert success is True
        assert "server1" in response
        assert "stdio" in response

@pytest.mark.asyncio
async def test_mcp_list_empty(mcp_command, context):
    with patch("vibe_coder.commands.slash.commands.mcp.config_manager") as mock_config:
        mock_config.list_mcp_servers.return_value = []

        success, response = await mcp_command.execute(["list"], context)
        assert success is True
        assert "No MCP servers configured" in response

@pytest.mark.asyncio
async def test_mcp_add(mcp_command, context):
    with patch("vibe_coder.commands.slash.commands.mcp.config_manager") as mock_config:
        success, response = await mcp_command.execute(
            ["add", "myserver", "stdio", "npx", "-y", "server"],
            context
        )
        assert success is True
        assert "Added MCP server 'myserver'" in response
        mock_config.set_mcp_server.assert_called_once()

@pytest.mark.asyncio
async def test_mcp_add_invalid_transport(mcp_command, context):
    success, response = await mcp_command.execute(["add", "s", "invalid", "cmd"], context)
    assert success is False
    assert "Transport must be 'stdio' or 'sse'" in response

@pytest.mark.asyncio
async def test_mcp_remove(mcp_command, context):
    with patch("vibe_coder.commands.slash.commands.mcp.config_manager") as mock_config:
        mock_config.get_mcp_server.return_value = MagicMock()

        success, response = await mcp_command.execute(["remove", "myserver"], context)
        assert success is True
        assert "Removed MCP server 'myserver'" in response
        mock_config.delete_mcp_server.assert_called_with("myserver")

@pytest.mark.asyncio
async def test_mcp_remove_not_found(mcp_command, context):
    with patch("vibe_coder.commands.slash.commands.mcp.config_manager") as mock_config:
        mock_config.get_mcp_server.return_value = None

        success, response = await mcp_command.execute(["remove", "myserver"], context)
        assert success is False
        assert "not found" in response

@pytest.mark.asyncio
async def test_mcp_unknown_subcommand(mcp_command, context):
    success, response = await mcp_command.execute(["unknown"], context)
    assert success is False
    assert "Unknown subcommand" in response
