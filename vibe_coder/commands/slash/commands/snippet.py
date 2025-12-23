"""Code snippet management slash commands."""

import json
from pathlib import Path
from typing import List, Optional

from vibe_coder.utils.snippet_manager import SnippetManager

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class SnippetCommand(SlashCommand):
    """Save and reuse code snippets."""

    def __init__(self):
        super().__init__(
            name="snippet",
            description="Save, search, and reuse code snippets",
            aliases=["save-snippet", "code-snippet"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the snippet command."""
        if not args:
            return """Usage: /snippet <action> [arguments]

Actions:
- save <name> <language> [description] - Save current file or selection
- get <name> - Get a snippet by name
- search <query> - Search snippets
- list [category] [language] - List snippets
- delete <name> - Delete a snippet
- stats - Show snippet statistics

Examples:
- /snippet save quicksort python "Quick sort implementation"
- /snippet get quicksort
- /snippet search "sort algorithm"
- /snippet list python
- /snippet stats"""

        action = args[0].lower()

        # Initialize snippet manager
        snippet_manager = SnippetManager(context.working_directory)

        if action == "save":
            return await self._save_snippet(snippet_manager, args[1:], context)
        elif action == "get":
            return await self._get_snippet(snippet_manager, args[1:], context)
        elif action == "search":
            return await self._search_snippets(snippet_manager, args[1:], context)
        elif action == "list":
            return await self._list_snippets(snippet_manager, args[1:], context)
        elif action == "delete":
            return await self._delete_snippet(snippet_manager, args[1:], context)
        elif action == "stats":
            return await self._show_stats(snippet_manager, context)
        else:
            return f"Unknown action: {action}. Use /snippet to see available actions."

    async def _save_snippet(
        self, snippet_manager: SnippetManager, args: List[str], context: CommandContext
    ) -> str:
        """Save a code snippet."""
        if len(args) < 2:
            return "Usage: /snippet save <name> <language> [description]"

        name = args[0]
        language = args[1]
        description = " ".join(args[2:]) if len(args) > 2 else ""

        # Get code content
        # TODO: In a real implementation, this would get selected text from editor
        # For now, we'll look for a file or read from stdin
        file_ops = FileOperations(context.working_directory)

        # Try to find a file to save as snippet
        code_files = list(Path(context.working_directory).glob("*"))
        code_files = [
            f
            for f in code_files
            if f.suffix in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
        ]

        if not code_files:
            return "No code file found. Please specify a file or have code in current directory."

        # For demo, use the first code file found
        code_file = code_files[0]
        code_content = await file_ops.read_file(str(code_file))

        # Determine category based on content or file type
        category = self._determine_category(code_content, language)

        # Extract tags from content
        tags = self._extract_tags(code_content, name)

        # Save snippet
        result = snippet_manager.save_snippet(
            name=name,
            code=code_content,
            language=language,
            description=description,
            category=category,
            tags=tags,
        )

        return f"{result}\n\n📝 File saved: {code_file.name}\n🏷️  Category: {category}\n📌 Tags: {', '.join(tags) if tags else 'None'}"

    def _determine_category(self, code: str, language: str) -> str:
        """Determine category from code content."""
        code_lower = code.lower()

        # Common patterns
        if "def test" in code_lower or "test_" in code_lower:
            return "test"
        elif "class test" in code_lower or "unittest" in code_lower or "pytest" in code_lower:
            return "test"
        elif "api" in code_lower or "endpoint" in code_lower or "route" in code_lower:
            return "api"
        elif "component" in code_lower or "react" in code_lower or "vue" in code_lower:
            return "ui"
        elif "model" in code_lower or "schema" in code_lower or "table" in code_lower:
            return "database"
        elif "async def" in code_lower or "async/await" in code_lower:
            return "async"
        elif "function(" in code_lower or "def " in code_lower:
            return "function"

        # Language-specific categories
        if language == "python":
            if "import unittest" in code_lower or "import pytest" in code_lower:
                return "test"
            elif "class " in code_lower:
                return "class"
            elif "def " in code_lower:
                return "function"
        elif language in ["javascript", "typescript"]:
            if "function " in code_lower or "=>" in code_lower:
                return "function"
            elif "class " in code_lower:
                return "class"
            elif "component" in code_lower:
                return "react"

        return "general"

    def _extract_tags(self, code: str, name: str) -> List[str]:
        """Extract relevant tags from code."""
        tags = []
        code_lower = code.lower()
        name_lower = name.lower()

        # Common patterns
        if "sort" in code_lower or "sort" in name_lower:
            tags.append("algorithm")
            if "quick" in code_lower or "quick" in name_lower:
                tags.append("quick-sort")
            elif "merge" in code_lower or "merge" in name_lower:
                tags.append("merge-sort")

        if "search" in code_lower or "search" in name_lower:
            tags.append("algorithm")
            if "binary" in code_lower:
                tags.append("binary-search")

        if "recurs" in code_lower:
            tags.append("recursive")

        if "async" in code_lower:
            tags.append("async")

        if "test" in code_lower:
            tags.append("test")

        # Data structures
        if "list" in code_lower or "array" in code_lower:
            tags.append("array")
        if "dict" in code_lower or "map" in code_lower:
            tags.append("map")
        if "tree" in code_lower:
            tags.append("tree")
        if "graph" in code_lower:
            tags.append("graph")

        # Design patterns
        if "singleton" in code_lower:
            tags.append("singleton")
        if "factory" in code_lower:
            tags.append("factory")
        if "observer" in code_lower:
            tags.append("observer")

        return list(set(tags))  # Remove duplicates

    async def _get_snippet(
        self, snippet_manager: SnippetManager, args: List[str], context: CommandContext
    ) -> str:
        """Get a snippet by name."""
        if not args:
            return "Usage: /snippet get <name>"

        name = args[0]
        snippet = snippet_manager.get_snippet(name)

        if not snippet:
            # Try search as fallback
            results = snippet_manager.search_snippets(name)
            if results:
                return f"Snippet '{name}' not found. Did you mean:\n" + "\n".join(
                    [f"  • {r['name']} ({r['language']})" for r in results[:5]]
                )
            return f"Snippet '{name}' not found"

        if isinstance(snippet, dict) and snippet.get("type") == "tag_list":
            return f"'{name}' is a tag with {len(snippet['snippets'])} snippets. Use /snippet list --tag {name}"

        # Return formatted snippet
        output = [f"📝 {snippet['name']}"]
        output.append(f"🏷️  Language: {snippet['language']}")
        output.append(f"📂 Category: {snippet['category']}")
        output.append(f"📖 Description: {snippet['description']}")
        output.append(f"📌 Tags: {', '.join(snippet['tags']) if snippet['tags'] else 'None'}")
        output.append(f"📊 Used: {snippet['uses']} times")
        output.append(f"📅 Created: {snippet['created_at'][:10]}")
        output.append("\n```" + snippet["language"])
        output.append(snippet["code"])
        output.append("```")

        return "\n".join(output)

    async def _search_snippets(
        self, snippet_manager: SnippetManager, args: List[str], context: CommandContext
    ) -> str:
        """Search for snippets."""
        if not args:
            return "Usage: /snippet search <query>"

        query = " ".join(args)
        results = snippet_manager.search_snippets(query)

        if not results:
            return f"No snippets found for: {query}"

        output = [f"🔍 Search results for '{query}':\n"]

        for result in results:
            output.append(f"  📝 {result['name']} ({result['language']})")
            output.append(
                f"     {result['description'][:80]}..."
                if len(result["description"]) > 80
                else f"     {result['description']}"
            )
            if result.get("match_type") == "code":
                output.append(f"     🔍 Match found in code")
            output.append("")

        return "\n".join(output)

    async def _list_snippets(
        self, snippet_manager: SnippetManager, args: List[str], context: CommandContext
    ) -> str:
        """List snippets with optional filters."""
        category = None
        language = None

        for arg in args:
            arg_lower = arg.lower()
            if arg_lower in [
                "python",
                "javascript",
                "typescript",
                "java",
                "go",
                "rust",
                "cpp",
                "c",
            ]:
                language = arg_lower
            else:
                category = arg_lower

        snippets = snippet_manager.list_snippets(category=category, language=language)

        if not snippets:
            filter_msg = []
            if category:
                filter_msg.append(f"category: {category}")
            if language:
                filter_msg.append(f"language: {language}")
            filter_str = f" with {', '.join(filter_msg)}" if filter_msg else ""
            return f"No snippets found{filter_str}"

        output = [f"📋 Snippets"]
        if category or language:
            filters = []
            if category:
                filters.append(f"Category: {category}")
            if language:
                filters.append(f"Language: {language}")
            output.append(f"   Filters: {', '.join(filters)}")
        output.append(f"\nFound {len(snippets)} snippets:\n")

        # Group by category
        by_category = {}
        for snippet in snippets:
            cat = snippet["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(snippet)

        for category, cat_snippets in sorted(by_category.items()):
            output.append(f"📂 {category.title()}:")
            for snippet in sorted(cat_snippets, key=lambda x: x["uses"], reverse=True):
                tags = f" [{', '.join(snippet['tags'][:3])}]" if snippet["tags"] else ""
                output.append(f"  • {snippet['name']} ({snippet['language']}){tags}")
                if snippet["description"]:
                    output.append(f"    {snippet['description'][:60]}...")
                output.append(f"    Used {snippet['uses']} times")
            output.append("")

        return "\n".join(output)

    async def _delete_snippet(
        self, snippet_manager: SnippetManager, args: List[str], context: CommandContext
    ) -> str:
        """Delete a snippet."""
        if not args:
            return "Usage: /snippet delete <name>"

        name = args[0]
        return snippet_manager.delete_snippet(name)

    async def _show_stats(self, snippet_manager: SnippetManager, context: CommandContext) -> str:
        """Show snippet statistics."""
        stats = snippet_manager.get_stats()

        output = ["📊 Snippet Statistics"]
        output.append(f"Total snippets: {stats['total_snippets']}")
        output.append(f"Total uses: {stats['total_uses']}")

        if stats["languages"]:
            output.append("\n📝 Languages:")
            for lang, count in sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True):
                output.append(f"  • {lang}: {count} snippets")

        if stats["categories"]:
            output.append("\n📂 Categories:")
            for cat, count in sorted(stats["categories"].items(), key=lambda x: x[1], reverse=True):
                output.append(f"  • {cat}: {count} snippets")

        if stats["most_popular"]:
            output.append("\n⭐ Most Popular:")
            for popular in stats["most_popular"][:5]:
                output.append(f"  • {popular['name']}: {popular['uses']} uses")

        # Storage info
        import os

        snippet_dir_size = 0
        for root, dirs, files in os.walk(snippet_manager.snippets_dir):
            for file in files:
                snippet_dir_size += os.path.getsize(os.path.join(root, file))

        output.append(f"\n💾 Storage: {snippet_dir_size / 1024:.1f} KB")
        output.append(f"📁 Location: {snippet_manager.snippets_dir}")

        return "\n".join(output)

    def get_min_args(self) -> int:
        return 1


class ImportSnippetsCommand(SlashCommand):
    """Import snippets from various formats."""

    def __init__(self):
        super().__init__(
            name="import-snippets",
            description="Import snippets from JSON file",
            aliases=["snippet-import"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the import command."""
        if not args:
            return "Usage: /import-snippets <file.json>"

        file_path = args[0]
        snippet_manager = SnippetManager(context.working_directory)
        return snippet_manager.import_snippets(file_path)


class ExportSnippetsCommand(SlashCommand):
    """Export snippets to various formats."""

    def __init__(self):
        super().__init__(
            name="export-snippets",
            description="Export snippets to JSON file",
            aliases=["snippet-export"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the export command."""
        if not args:
            return "Usage: /export-snippets <file.json>"

        file_path = args[0]
        snippet_manager = SnippetManager(context.working_directory)
        return snippet_manager.export_snippets(file_path)


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(SnippetCommand())
command_registry.register(ImportSnippetsCommand())
command_registry.register(ExportSnippetsCommand())


def register():
    """Register all snippet commands."""
    return [
        SnippetCommand(),
        ImportSnippetsCommand(),
        ExportSnippetsCommand(),
    ]
