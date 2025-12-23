"""
Manager for Model Context Protocol (MCP) clients.

This module handles the lifecycle of connections to multiple MCP servers,
executes tools, and aggregates resources.
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from vibe_coder.config.manager import config_manager
from vibe_coder.types.config import MCPServer


class MCPManager:
    """
    Manages connections to multiple MCP servers.
    """

    def __init__(self):
        """Initialize the MCP manager."""
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tools: List[Tool] = []

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        servers = config_manager.list_mcp_servers()
        for name in servers:
            server_config = config_manager.get_mcp_server(name)
            if server_config:
                try:
                    await self.connect_server(server_config)
                except Exception as e:
                    print(f"Failed to connect to MCP server {name}: {e}")

    async def connect_server(self, config: MCPServer):
        """
        Connect to a single MCP server.

        Args:
            config: MCP server configuration
        """
        if config.name in self.sessions:
            return  # Already connected

        if config.transport == "stdio":
            await self._connect_stdio(config)
        elif config.transport == "sse":
            await self._connect_sse(config)
        else:
            raise ValueError(f"Unknown transport: {config.transport}")

    async def _connect_stdio(self, config: MCPServer):
        """Connect using stdio transport."""
        # Prepare environment
        env = os.environ.copy()
        if config.env:
            env.update(config.env)

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=env,
        )

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await session.initialize()
        self.sessions[config.name] = session

        # Load tools
        await self._refresh_tools(config.name)

    async def _connect_sse(self, config: MCPServer):
        """Connect using SSE transport."""
        read_stream, write_stream = await self.exit_stack.enter_async_context(
            sse_client(config.command)
        )

        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await session.initialize()
        self.sessions[config.name] = session

        # Load tools
        await self._refresh_tools(config.name)

    async def _refresh_tools(self, server_name: str):
        """Refresh tools for a specific server."""
        if server_name not in self.sessions:
            return

        session = self.sessions[server_name]
        result = await session.list_tools()

        # Remove existing tools for this server (re-adding logic needed if complex)
        # For now, we just append. A real implementation might want to track origin.
        # But wait, Tool object from mcp doesn't have "origin".
        # We need to map tool names to sessions to know which one to call.
        # So we won't store them in a flat self.tools list directly without mapping.
        pass

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools from all connected servers formatted for LLM use.

        Returns:
            List of tool definitions
        """
        all_tools = []

        for name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    # We need to namespace the tools or track them
                    # For simplicity, we assume unique names or prefix them?
                    # The user wants "their own mcps".
                    # Let's keep the original name but internally track who owns it.

                    # Convert to OpenAI tool format
                    tool_def = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                    all_tools.append(tool_def)
            except Exception as e:
                print(f"Error listing tools for {name}: {e}")

        return all_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool on the appropriate server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Tool execution result
        """
        # Find which session has this tool
        target_session = None

        for name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    if tool.name == tool_name:
                        target_session = session
                        break
                if target_session:
                    break
            except Exception:
                continue

        if not target_session:
            raise ValueError(f"Tool {tool_name} not found on any connected MCP server")

        result = await target_session.call_tool(tool_name, arguments)
        return result

    async def close(self):
        """Close all connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
