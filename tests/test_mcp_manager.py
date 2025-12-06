"""Tests for MCP manager."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from vibe_coder.mcp.manager import MCPManager
from vibe_coder.types.config import MCPServer

@pytest.fixture
def mcp_manager():
    return MCPManager()

@pytest.mark.asyncio
async def test_connect_stdio(mcp_manager):
    server_config = MCPServer(
        name="test-server",
        command="echo",
        args=["hello"],
        transport="stdio"
    )

    with patch("vibe_coder.mcp.manager.stdio_client") as mock_stdio:
        mock_stdio.return_value.__aenter__.return_value = (MagicMock(), MagicMock())

        with patch("vibe_coder.mcp.manager.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            await mcp_manager.connect_server(server_config)

            assert "test-server" in mcp_manager.sessions
            mock_session.initialize.assert_awaited_once()

@pytest.mark.asyncio
async def test_connect_sse(mcp_manager):
    server_config = MCPServer(
        name="test-sse",
        command="http://localhost:8000/sse",
        transport="sse"
    )

    with patch("vibe_coder.mcp.manager.sse_client") as mock_sse:
        mock_sse.return_value.__aenter__.return_value = (MagicMock(), MagicMock())

        with patch("vibe_coder.mcp.manager.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            await mcp_manager.connect_server(server_config)

            assert "test-sse" in mcp_manager.sessions
            mock_session.initialize.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_all_tools(mcp_manager):
    mock_session = AsyncMock()
    mock_tool = MagicMock()
    mock_tool.name = "tool1"
    mock_tool.description = "desc1"
    mock_tool.inputSchema = {}

    mock_result = MagicMock()
    mock_result.tools = [mock_tool]
    mock_session.list_tools.return_value = mock_result

    mcp_manager.sessions["test"] = mock_session

    tools = await mcp_manager.get_all_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "tool1"

@pytest.mark.asyncio
async def test_execute_tool(mcp_manager):
    mock_session = AsyncMock()
    mock_tool = MagicMock()
    mock_tool.name = "tool1"

    mock_result = MagicMock()
    mock_result.tools = [mock_tool]
    mock_session.list_tools.return_value = mock_result
    mock_session.call_tool.return_value = "result"

    mcp_manager.sessions["test"] = mock_session

    result = await mcp_manager.execute_tool("tool1", {})
    assert result == "result"

@pytest.mark.asyncio
async def test_execute_tool_not_found(mcp_manager):
    mcp_manager.sessions = {}
    with pytest.raises(ValueError, match="not found"):
        await mcp_manager.execute_tool("unknown", {})

@pytest.mark.asyncio
async def test_connect_server_already_connected(mcp_manager):
    config = MCPServer(name="test", command="echo", transport="stdio")
    mcp_manager.sessions["test"] = MagicMock()

    # Should return immediately
    await mcp_manager.connect_server(config)
    # No way to verify 'return' easily other than coverage or no side effects

@pytest.mark.asyncio
async def test_connect_server_invalid_transport(mcp_manager):
    config = MCPServer(name="test", command="echo", transport="invalid")
    with pytest.raises(ValueError, match="Unknown transport"):
        await mcp_manager.connect_server(config)

@pytest.mark.asyncio
async def test_connect_all(mcp_manager):
    with patch("vibe_coder.mcp.manager.config_manager") as mock_config:
        mock_config.list_mcp_servers.return_value = ["s1", "s2"]
        mock_config.get_mcp_server.side_effect = [
            MCPServer(name="s1", command="c1", transport="stdio"),
            MCPServer(name="s2", command="c2", transport="sse")
        ]

        # Mock connect_server to avoid real connection logic
        with patch.object(mcp_manager, "connect_server", new_callable=AsyncMock) as mock_connect:
            await mcp_manager.connect_all()
            assert mock_connect.call_count == 2

@pytest.mark.asyncio
async def test_connect_all_with_error(mcp_manager):
    with patch("vibe_coder.mcp.manager.config_manager") as mock_config:
        mock_config.list_mcp_servers.return_value = ["s1"]
        mock_config.get_mcp_server.return_value = MCPServer(name="s1", command="c1", transport="stdio")

        with patch.object(mcp_manager, "connect_server", side_effect=Exception("Fail")):
            # Should not raise exception (it prints)
            await mcp_manager.connect_all()
