"""Web and knowledge integration commands."""

from typing import List

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.mcp.manager import MCPManager


class WebCommand(SlashCommand):
    """Search the web via MCP."""

    def __init__(self):
        super().__init__(
            name="web",
            description="Search the web using connected MCP tools",
            aliases=["search", "google"],
            category="web",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        if not args:
            return "Usage: /web <query>"

        query = " ".join(args)

        if not hasattr(context, "mcp_manager") or not context.mcp_manager:
            return "MCP Manager not available."

        mcp_manager: MCPManager = context.mcp_manager # type: ignore

        # Look for a search tool
        tools = await mcp_manager.get_all_tools()
        search_tool = None
        for tool in tools:
            name = tool.get("function", {}).get("name", "").lower()
            if "search" in name or "web" in name:
                search_tool = tool.get("function", {}).get("name")
                break

        if not search_tool:
            return "No web search tool found. Connect an MCP server with search capabilities (e.g., Brave Search)."

        try:
            # We assume a standard 'query' or 'q' parameter. This is heuristic.
            # A robust implementation would inspect schema or ask AI to map it.
            # For this command, we try to call it directly.
            result = await mcp_manager.execute_tool(search_tool, {"query": query})
            return f"🌍 **Search Result**\n\n{result}"
        except Exception as e:
            return f"Search failed: {e}"


class DocsCommand(SlashCommand):
    """Search documentation via MCP."""

    def __init__(self):
        super().__init__(
            name="docs",
            description="Search documentation using connected MCP tools",
            aliases=["doc"],
            category="web",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # Very similar to WebCommand but looking for docs tool
        if not args:
            return "Usage: /docs <query>"

        query = " ".join(args)

        if not hasattr(context, "mcp_manager") or not context.mcp_manager:
            return "MCP Manager not available."

        mcp_manager: MCPManager = context.mcp_manager # type: ignore

        # Look for a docs tool
        tools = await mcp_manager.get_all_tools()
        docs_tool = None
        for tool in tools:
            name = tool.get("function", {}).get("name", "").lower()
            if "doc" in name:
                docs_tool = tool.get("function", {}).get("name")
                break

        if not docs_tool:
            return "No documentation search tool found."

        try:
            result = await mcp_manager.execute_tool(docs_tool, {"query": query})
            return f"📚 **Docs Result**\n\n{result}"
        except Exception as e:
            return f"Docs search failed: {e}"
