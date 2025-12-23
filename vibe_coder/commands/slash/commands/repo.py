"""Repository-related slash commands for Vibe Coder."""

import os
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.intelligence.importance_scorer import ImportanceScorer
from vibe_coder.intelligence.repo_mapper import RepositoryMapper


class ScanCommand(SlashCommand):
    """Scan repository for intelligent context."""

    def __init__(self):
        super().__init__(
            name="scan",
            description="Scan repository for intelligent context analysis",
            aliases=["sc"],
            category="repository",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the scan command."""
        console = Console()

        # Use provided path or current directory
        scan_path = args[0] if args else context.working_directory

        try:
            # Initialize repository mapper
            repo_mapper = RepositoryMapper(
                root_path=scan_path,
                enable_monitoring=False,  # Don't start monitoring for scan
                enable_importance_scoring=True,
                enable_reference_resolution=True,
            )

            # Scan repository
            with console.status("[bold green]Scanning repository..."):
                await repo_mapper.scan_repository()

            # Get statistics
            stats = repo_mapper.get_stats()
            repo_map = repo_mapper._repo_map

            if repo_map:
                # Create summary table
                table = Table(title="Repository Scan Results")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="magenta")

                table.add_row("Root Path", stats["root_path"])
                table.add_row("Total Files", str(stats["total_files"]))
                table.add_row("Total Lines", str(stats["total_lines"]))
                table.add_row("Entry Points", str(stats["entry_points"]))
                table.add_row("Test Files", str(stats["test_files"]))

                # Add language breakdown
                if stats["languages"]:
                    table.add_row("", "")  # Separator
                    table.add_row("Languages", "")
                    for lang, count in sorted(
                        stats["languages"].items(), key=lambda x: x[1], reverse=True
                    ):
                        table.add_row(f"  {lang}", str(count))

                # Render table
                console.print(Panel(table, title="📊 Repository Analysis"))

                # Show top important files
                if repo_mapper.importance_scorer:
                    console.print("\n[bold]Top Important Files:[/bold]")
                    top_files = await repo_mapper.importance_scorer.get_top_files(limit=5)
                    for file_path, score in top_files:
                        console.print(f"  • {file_path} (score: {score:.2f})")

            return f"Repository scan complete: {stats['total_files']} files found"

        except Exception as e:
            return f"Error scanning repository: {e}"


class ContextCommand(SlashCommand):
    """Show current repository context being sent to AI."""

    name = "context"
    help_text = "Show what repository context is being sent to AI"

    async def execute(self, ctx: CommandContext, file: Optional[str] = None) -> str:
        """Execute the context command."""
        if not ctx.chat_command or not ctx.chat_command.context_provider:
            return "Repository context is not available. Make sure you're in chat mode."

        try:
            # Get context for specified file or general context
            if file:
                context = ctx.chat_command.repo_mapper.get_context_for_file(file)
            else:
                # Get compressed representation
                context = await ctx.chat_command.repo_mapper.compress_with_importance(
                    max_tokens=4000
                )

            # Display context
            console = Console()
            console.print(Panel(context, title="📝 Repository Context", border_style="blue"))

            # Show token estimate
            estimated_tokens = len(context) // 4
            console.print(f"\n[dim]Estimated tokens: {estimated_tokens}[/dim]")

            return f"Showing context for {file or 'repository'}"

        except Exception as e:
            return f"Error getting context: {e}"


class ReferencesCommand(SlashCommand):
    """Find all references to a symbol in the repository."""

    name = "references"
    help_text = "Find all references to a symbol in the codebase"

    async def execute(self, ctx: CommandContext, symbol: str, file: Optional[str] = None) -> str:
        """Execute the references command."""
        if not ctx.chat_command or not ctx.chat_command.repo_mapper:
            return "Repository mapper not available. Make sure you're in chat mode."

        repo_mapper = ctx.chat_command.repo_mapper
        if not repo_mapper.reference_resolver:
            return "Reference resolution not enabled."

        console = Console()

        try:
            # Find references
            refs = await repo_mapper.reference_resolver.find_references(symbol, file)

            if not refs:
                console.print(f"[yellow]No references found for symbol '{symbol}'[/yellow]")
                return f"No references found for '{symbol}'"

            # Create results table
            table = Table(title=f"References to '{symbol}'")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Context", style="white")

            # Group by file for cleaner display
            refs_by_file = {}
            for ref in refs:
                if ref.file_path not in refs_by_file:
                    refs_by_file[ref.file_path] = []
                refs_by_file[ref.file_path].append(ref)

            # Display references
            for file_path, file_refs in refs_by_file.items():
                console.print(f"\n[bold]📄 {file_path}[/bold]")
                for ref in file_refs[:5]:  # Limit to 5 per file
                    console.print(
                        f"  Line {ref.line_number}: {ref.reference_type} - {ref.context[:50]}..."
                    )
                if len(file_refs) > 5:
                    console.print(f"  ... and {len(file_refs) - 5} more")

            return f"Found {len(refs)} references to '{symbol}'"

        except Exception as e:
            return f"Error finding references: {e}"


class ImportanceCommand(SlashCommand):
    """Show file importance scores."""

    name = "importance"
    help_text = "Show file importance scores in the repository"

    async def execute(self, ctx: CommandContext, limit: int = 10) -> str:
        """Execute the importance command."""
        if not ctx.chat_command or not ctx.chat_command.repo_mapper:
            return "Repository mapper not available. Make sure you're in chat mode."

        repo_mapper = ctx.chat_command.repo_mapper
        if not repo_mapper.importance_scorer:
            return "Importance scoring not enabled."

        console = Console()

        try:
            # Get top files by importance
            top_files = await repo_mapper.importance_scorer.get_top_files(limit=limit)

            if not top_files:
                console.print("[yellow]No files found in repository[/yellow]")
                return "No files found in repository"

            # Create results table
            table = Table(title=f"Top {len(top_files)} Most Important Files")
            table.add_column("Rank", style="cyan", width=5)
            table.add_column("File", style="magenta")
            table.add_column("Score", style="green", width=8)
            table.add_column("Factors", style="white")

            for i, (file_path, score) in enumerate(top_files, 1):
                # Get factor breakdown if available
                factors = repo_mapper.importance_scorer.get_importance_factors(file_path)
                if factors:
                    top_factors = sorted(
                        [(k, v) for k, v in factors.items() if v > 0.1],
                        key=lambda x: x[1],
                        reverse=True,
                    )[:2]
                    factors_str = ", ".join([f"{k}: {v:.2f}" for k, v in top_factors])
                else:
                    factors_str = "N/A"

                table.add_row(str(i), file_path, f"{score:.2f}", factors_str)

            console.print(table)

            return f"Showing top {len(top_files)} files by importance"

        except Exception as e:
            return f"Error calculating importance: {e}"


class MonitorCommand(SlashCommand):
    """Toggle real-time file monitoring."""

    name = "monitor"
    help_text = "Toggle real-time file monitoring (on/off/status)"

    async def execute(self, ctx: CommandContext, action: str = "status") -> str:
        """Execute the monitor command."""
        if not ctx.chat_command or not ctx.chat_command.repo_mapper:
            return "Repository mapper not available. Make sure you're in chat mode."

        repo_mapper = ctx.chat_command.repo_mapper
        console = Console()

        try:
            if action == "status":
                # Get monitor status
                if repo_mapper.file_watcher:
                    status = repo_mapper.file_watcher.get_status()
                    if status["is_monitoring"]:
                        console.print(
                            "[green]✓ File monitoring is ACTIVE[/green]\n"
                            f"Watching {status['monitored_paths']}"
                        )
                    else:
                        console.print("[yellow]File monitoring is INACTIVE[/yellow]")
                else:
                    console.print("[yellow]File monitoring is not initialized[/yellow]")

            elif action == "on":
                # Start monitoring
                repo_mapper.start_monitoring()
                console.print("[green]✓ File monitoring started[/green]")

            elif action == "off":
                # Stop monitoring
                repo_mapper.stop_monitoring()
                console.print("[yellow]File monitoring stopped[/yellow]")

            else:
                return f"Unknown action: {action}. Use 'on', 'off', or 'status'"

            return f"Monitor action '{action}' completed"

        except Exception as e:
            return f"Error with file monitor: {e}"


# Register commands
def register():
    """Register all repository commands."""
    return [
        ScanCommand(),
        ContextCommand(),
        ReferencesCommand(),
        ImportanceCommand(),
        MonitorCommand(),
    ]
