"""MCP tool discovery commands."""

import json
from typing import List, Tuple

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.mcp.manager import MCPManager


class ToolsCommand(SlashCommand):
    """List available MCP tools."""

    def __init__(self):
        super().__init__(
            name="tools",
            description="List available tools from connected MCP servers",
            aliases=["list-tools", "ls-tools"],
            category="mcp",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # We need access to the MCP Manager.
        # It's not in CommandContext.
        # We should update CommandContext to include mcp_manager or access it via a singleton/global if configured.
        # Since `chat.py` initializes it, maybe we can access it via a module-level instance if we refactor,
        # but properly we should pass it in context.

        # NOTE: `chat.py` creates `MCPManager` instance.
        # To make this work without major refactoring of `CommandContext` injection in `chat.py`,
        # I will assume `CommandContext` will be updated to have `mcp_manager`.

        if not hasattr(context, "mcp_manager") or not context.mcp_manager:
            return "MCP Manager not available in this context."

        mcp_manager: MCPManager = context.mcp_manager # type: ignore

        tools = await mcp_manager.get_all_tools()

        if not tools:
            return "No tools available. Connect MCP servers using `/mcp add`."

        result = "🛠️ **Available Tools**\n\n"
        for tool in tools:
            # tool structure from get_all_tools is OpenAI format:
            # {"type": "function", "function": {"name": "...", "description": "..."}}

            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "No description")
            result += f"- **{name}**: {desc}\n"

        return result


class ToolHelpCommand(SlashCommand):
    """Show details for a specific tool."""

    def __init__(self):
        super().__init__(
            name="tool-help",
            description="Show details and schema for a tool",
            aliases=["tool", "inspect-tool"],
            category="mcp",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return "Usage: /tool-help <tool_name>"

        tool_name = args[0]

        if not hasattr(context, "mcp_manager") or not context.mcp_manager:
            return "MCP Manager not available."

        mcp_manager: MCPManager = context.mcp_manager # type: ignore
        tools = await mcp_manager.get_all_tools()

        found_tool = None
        for tool in tools:
            if tool.get("function", {}).get("name") == tool_name:
                found_tool = tool
                break

        if not found_tool:
            return f"Tool '{tool_name}' not found."

        func = found_tool.get("function", {})
        desc = func.get("description", "No description")
        params = func.get("parameters", {})

        result = f"🔧 **Tool: {tool_name}**\n\n"
        result += f"{desc}\n\n"
        result += "**Parameters:**\n"
        result += f"```json\n{json.dumps(params, indent=2)}\n```"

        return result


class InspectMCPCommand(SlashCommand):
    """Inspect MCP server status."""

    def __init__(self):
        super().__init__(
            name="inspect-mcp",
            description="Inspect MCP server status",
            aliases=["mcp-status"],
            category="mcp",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not hasattr(context, "mcp_manager") or not context.mcp_manager:
            return "MCP Manager not available."

        mcp_manager: MCPManager = context.mcp_manager # type: ignore

        if not mcp_manager.sessions:
            return "No active MCP sessions."

        result = "🔌 **MCP Server Status**\n\n"
        for name, session in mcp_manager.sessions.items():
            # We can't easily get latency/resources without pinging, but we can list them.
            # session object doesn't expose much public state about health directly.
            result += f"- **{name}**: Connected\n"

        return result
