"""MCP slash commands."""

from typing import List, Tuple

import questionary
from rich.table import Table

from vibe_coder.commands.slash.base import BaseSlashCommand, CommandContext
from vibe_coder.config.manager import config_manager
from vibe_coder.types.config import MCPServer


class MCPCommand(BaseSlashCommand):
    """
    Manage Model Context Protocol (MCP) servers.

    Usage:
        /mcp list
        /mcp add <name> <transport> <command> [args...]
        /mcp remove <name>
    """

    name = "mcp"
    description = "Manage MCP servers"

    async def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, str]:
        if not args:
            return await self._list_servers()

        subcommand = args[0]

        if subcommand == "list":
            return await self._list_servers()
        elif subcommand == "add":
            return await self._add_server(args[1:])
        elif subcommand == "remove" or subcommand == "rm":
            return await self._remove_server(args[1:])
        else:
            return False, f"Unknown subcommand: {subcommand}"

    async def _list_servers(self) -> Tuple[bool, str]:
        servers = config_manager.list_mcp_servers()
        if not servers:
            return True, "No MCP servers configured."

        # Create a table using rich (but return string for markdown)
        # Since we return markdown, we'll format it as a markdown table

        output = ["| Name | Transport | Command |", "| --- | --- | --- |"]
        for name in servers:
            server = config_manager.get_mcp_server(name)
            cmd = server.command
            if server.args:
                cmd += f" {' '.join(server.args)}"
            output.append(f"| {server.name} | {server.transport} | `{cmd}` |")

        return True, "\n".join(output)

    async def _add_server(self, args: List[str]) -> Tuple[bool, str]:
        # args: name transport command [args...]
        if len(args) < 3:
            # If not enough args, launch interactive mode?
            # For now, just return error
            return False, "Usage: /mcp add <name> <transport> <command> [args...]"

        name = args[0]
        transport = args[1]
        command = args[2]
        cmd_args = args[3:] if len(args) > 3 else []

        if transport not in ["stdio", "sse"]:
            return False, "Transport must be 'stdio' or 'sse'"

        server = MCPServer(
            name=name,
            transport=transport,
            command=command,
            args=cmd_args
        )

        config_manager.set_mcp_server(name, server)
        return True, f"Added MCP server '{name}'"

    async def _remove_server(self, args: List[str]) -> Tuple[bool, str]:
        if not args:
            return False, "Usage: /mcp remove <name>"

        name = args[0]
        if not config_manager.get_mcp_server(name):
            return False, f"MCP server '{name}' not found"

        config_manager.delete_mcp_server(name)
        return True, f"Removed MCP server '{name}'"
