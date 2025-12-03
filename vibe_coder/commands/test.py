"""Test command implementation for Vibe Coder."""

import asyncio
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from vibe_coder.api.factory import ClientFactory
from vibe_coder.config.manager import config_manager


class TestCommand:
    """Connection testing command for Vibe Coder."""

    def __init__(self):
        self.console = Console()

    async def run(self, provider_name: Optional[str] = None) -> bool:
        """Test connection to AI provider(s).

        Args:
            provider_name: Specific provider to test, or None for current/all

        Returns:
            True if all tests passed, False otherwise
        """
        try:
            if provider_name:
                # Test specific provider
                return await self._test_single_provider(provider_name)
            else:
                # Test current provider or all providers
                current_provider = config_manager.get_current_provider()
                if current_provider:
                    self.console.print(
                        f"[blue]Testing current provider: {current_provider.name}[/blue]"
                    )
                    return await self._test_single_provider(current_provider.name)
                else:
                    # No current provider, test all
                    providers = config_manager.list_providers()
                    if not providers:
                        self.console.print("[red]No providers configured to test.[/red]")
                        self.console.print("Use 'vibe-coder setup' to configure a provider.")
                        return False

                    return await self._test_all_providers(providers)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Test interrupted by user.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Test error: {e}[/red]")
            return False

    async def _test_single_provider(self, provider_name: str) -> bool:
        """Test a single provider connection.

        Args:
            provider_name: Name of provider to test

        Returns:
            True if test passed, False otherwise
        """
        provider = config_manager.get_provider(provider_name)
        if not provider:
            self.console.print(f"[red]Provider '{provider_name}' not found.[/red]")
            return False

        self.console.print(f"[blue]Testing connection to {provider_name}...[/blue]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                # Create client
                task = progress.add_task("Creating client...", total=None)
                client = ClientFactory.create_client(provider)

                # Test connection
                progress.update(task, description="Validating API credentials...")
                is_valid = await client.validate_connection()

                await client.close()

                if is_valid:
                    progress.update(task, description="✅ Connection successful!")
                    await asyncio.sleep(1)  # Brief pause to show success

                    # Show provider details
                    self._show_provider_success(provider)
                    return True
                else:
                    progress.update(task, description="❌ Connection failed")
                    await asyncio.sleep(1)  # Brief pause to show failure

                    self._show_provider_failure(provider, "API validation failed")
                    return False

        except Exception as e:
            self._show_provider_failure(provider, str(e))
            return False

    async def _test_all_providers(self, providers: list) -> bool:
        """Test all configured providers.

        Args:
            providers: List of provider names to test

        Returns:
            True if all tests passed, False otherwise
        """
        self.console.print(f"[blue]Testing {len(providers)} configured provider(s)...[/blue]\n")

        results = []
        current_provider = config_manager.get_current_provider()
        current_name = current_provider.name if current_provider else None

        for provider_name in providers:
            is_current = provider_name == current_name
            result = await self._test_single_provider_with_indicator(provider_name, is_current)
            results.append((provider_name, result))
            self.console.print()  # Add spacing between tests

        # Show summary
        self._show_test_summary(results)

        # Return True only if all tests passed
        return all(result for _, result in results)

    async def _test_single_provider_with_indicator(
        self, provider_name: str, is_current: bool
    ) -> bool:
        """Test a single provider with current indicator.

        Args:
            provider_name: Name of provider to test
            is_current: Whether this is the current provider

        Returns:
            True if test passed, False otherwise
        """
        # Create header
        current_text = " [yellow](Current)[/yellow]" if is_current else ""
        self.console.print(f"[cyan]Testing: {provider_name}{current_text}[/cyan]")

        provider = config_manager.get_provider(provider_name)
        if not provider:
            self.console.print("[red]  ✗ Provider not found in configuration[/red]")
            return False

        try:
            # Create and test client
            client = ClientFactory.create_client(provider)
            is_valid = await client.validate_connection()
            await client.close()

            if is_valid:
                self.console.print("[green]  ✅ Connection successful[/green]")
                return True
            else:
                self.console.print(
                    "[red]  ✗ Connection failed - Invalid credentials or endpoint[/red]"
                )
                return False

        except Exception as e:
            self.console.print(f"[red]  ✗ Connection failed - {e}[/red]")
            return False

    def _show_provider_success(self, provider):
        """Show successful connection details.

        Args:
            provider: Provider configuration that was tested
        """
        details = Table(show_header=False, box=None)
        details.add_column("Field", style="cyan")
        details.add_column("Value", style="green")

        details.add_row("Provider", provider.name)
        details.add_row("Endpoint", provider.endpoint)
        details.add_row("Model", provider.model or "default")
        details.add_row("Temperature", str(provider.temperature))
        if provider.max_tokens:
            details.add_row("Max Tokens", str(provider.max_tokens))

        panel = Panel(
            details,
            title="[bold green]✅ Connection Test Successful[/bold green]",
            border_style="green",
        )
        self.console.print(panel)

    def _show_provider_failure(self, provider, error_message: str):
        """Show failed connection details.

        Args:
            provider: Provider configuration that was tested
            error_message: Error message from the test
        """
        details = Table(show_header=False, box=None)
        details.add_column("Field", style="cyan")
        details.add_column("Value", style="red")

        details.add_row("Provider", provider.name)
        details.add_row("Endpoint", provider.endpoint)
        details.add_row("Error", error_message)

        # Show troubleshooting tips
        tips = []
        if "401" in str(error_message) or "unauthorized" in str(error_message).lower():
            tips.append("• Check your API key is valid and active")
        if "connection" in str(error_message).lower() or "network" in str(error_message).lower():
            tips.append("• Check your internet connection")
            tips.append("• Verify the endpoint URL is correct")
        if "timeout" in str(error_message).lower():
            tips.append("• The request timed out - try again")
        if not tips:
            tips.append("• Check your provider configuration")
            tips.append("• Verify API key and endpoint are correct")

        tips_text = "\n".join(tips)

        panel = Panel(
            details, title="[bold red]✗ Connection Test Failed[/bold red]", border_style="red"
        )
        self.console.print(panel)

        if tips:
            tips_panel = Panel(tips_text, title="Troubleshooting Tips", border_style="yellow")
            self.console.print(tips_panel)

    def _show_test_summary(self, results: list):
        """Show test results summary.

        Args:
            results: List of (provider_name, success) tuples
        """
        total = len(results)
        passed = sum(1 for _, success in results if success)
        failed = total - passed

        # Create summary table
        summary_table = Table(title="Test Summary")
        summary_table.add_column("Provider", style="cyan")
        summary_table.add_column("Status", justify="center", style="bold")
        summary_table.add_column("Result", style="white")

        current_provider = config_manager.get_current_provider()
        current_name = current_provider.name if current_provider else None

        for provider_name, success in results:
            is_current = provider_name == current_name
            current_marker = " [yellow](Current)[/yellow]" if is_current else ""

            if success:
                status = "✅"
                status_style = "green"
                result = "Connected"
                result_style = "green"
            else:
                status = "❌"
                status_style = "red"
                result = "Failed"
                result_style = "red"

            summary_table.add_row(
                f"{provider_name}{current_marker}",
                f"[{status_style}]{status}[/{status_style}]",
                f"[{result_style}]{result}[/{result_style}]",
            )

        self.console.print(summary_table)

        # Show overall status
        if failed == 0:
            status_text = f"[bold green]All {total} provider(s) working correctly![/bold green]"
        elif passed == 0:
            status_text = f"[bold red]All {total} provider(s) failed to connect[/bold red]"
        else:
            status_text = (
                f"[yellow]{passed} of {total} provider(s) working, {failed} failed[/yellow]"
            )

        self.console.print(f"\n{status_text}")

        # Show next steps if there are failures
        if failed > 0:
            self.console.print("\n[cyan]Next steps:[/cyan]")
            self.console.print("  • Run 'vibe-coder config edit <provider>' to fix configuration")
            self.console.print("  • Run 'vibe-coder setup' to configure a new provider")
            self.console.print("  • Check your API keys and network connection")
