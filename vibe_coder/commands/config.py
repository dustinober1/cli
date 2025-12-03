"""Config command implementation for Vibe Coder."""

from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vibe_coder.api.factory import ClientFactory
from vibe_coder.commands.setup import SetupCommand
from vibe_coder.config.manager import config_manager


class ConfigCommand:
    """Configuration management command for Vibe Coder."""

    def __init__(self):
        self.console = Console()

    async def run(self, action: str, name: Optional[str] = None) -> bool:
        """Run config command with specified action.

        Args:
            action: Action to perform (list, show, add, edit, delete)
            name: Provider name for actions that require it

        Returns:
            True if command completed successfully, False otherwise
        """
        try:
            if action == "list":
                await self.list_providers()
                return True
            elif action == "show":
                return await self.show_provider(name)
            elif action == "add":
                return await self.add_provider()
            elif action == "edit":
                return await self.edit_provider(name)
            elif action == "delete":
                return await self.delete_provider(name)
            else:
                self.console.print(f"[red]Unknown action: {action}[/red]")
                self._show_available_actions()
                return False

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Command cancelled.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return False

    async def list_providers(self):
        """List all configured providers."""
        providers = config_manager.list_providers()
        current_provider = config_manager.get_current_provider()
        current = current_provider.name if current_provider else None

        if not providers:
            self.console.print("[yellow]No providers configured.[/yellow]")
            self.console.print("Use 'vibe-coder config add' to add a provider.")
            return

        table = Table(title="Configured AI Providers")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Model", style="magenta")
        table.add_column("Endpoint", style="green")
        table.add_column("Temperature", style="yellow")
        table.add_column("Current", justify="center", style="bold yellow")

        for provider_name in providers:
            provider = config_manager.get_provider(provider_name)
            current_marker = "✓" if provider_name == current else ""
            table.add_row(
                provider_name,
                provider.model or "default",
                provider.endpoint,
                str(provider.temperature),
                current_marker,
            )

        self.console.print(table)

        # Show current provider info
        if current:
            self.console.print(f"\n[green]Current provider: {current}[/green]")

    async def show_provider(self, name: Optional[str]) -> bool:
        """Show detailed information about a provider.

        Args:
            name: Provider name to show

        Returns:
            True if successful, False otherwise
        """
        if not name:
            # Show current provider if no name specified
            current_provider = config_manager.get_current_provider()
            if not current_provider:
                self.console.print("[red]No current provider set.[/red]")
                return False
            name = current_provider.name

        provider = config_manager.get_provider(name)
        if not provider:
            self.console.print(f"[red]Provider '{name}' not found.[/red]")
            return False

        # Show provider details (hide sensitive info)
        details = {}
        details["Name"] = provider.name
        details["Endpoint"] = provider.endpoint
        details["Model"] = provider.model or "default"
        details["Temperature"] = provider.temperature
        details["Max Tokens"] = provider.max_tokens or "unlimited"
        details["API Key"] = self._mask_api_key(provider.api_key) if provider.api_key else "None"
        details["Custom Headers"] = "Yes" if provider.headers else "No"

        # Format details
        detail_lines = []
        for key, value in details.items():
            detail_lines.append(f"[cyan]{key}:[/cyan] {value}")

        # Check if it's the current provider
        current_provider = config_manager.get_current_provider()
        if current_provider and name == current_provider.name:
            detail_lines.insert(0, "")
            detail_lines.insert(0, "[bold green]✓ Current Provider[/bold green]")

        panel = Panel(
            "\n".join(detail_lines), title=f"Provider Details: {name}", border_style="blue"
        )
        self.console.print(panel)

        # Test connection
        self.console.print("\n[cyan]Testing connection...[/cyan]")
        try:
            client = ClientFactory.create_client(provider)
            is_valid = await client.validate_connection()
            await client.close()

            if is_valid:
                self.console.print("[green]✓ Connection test successful![/green]")
            else:
                self.console.print("[red]✗ Connection test failed[/red]")
        except Exception as e:
            self.console.print(f"[red]Connection test error: {e}[/red]")

        return True

    async def add_provider(self) -> bool:
        """Add a new provider using the setup wizard.

        Returns:
            True if successful, False otherwise
        """
        self.console.print("[blue]Adding new provider...[/blue]")
        self.console.print("This will launch the setup wizard to configure a new provider.\n")

        # Use the setup command logic for adding
        setup_command = SetupCommand()
        success = await setup_command.run()

        if success:
            self.console.print("[green]Provider added successfully![/green]")
        else:
            self.console.print("[yellow]Provider addition cancelled or failed.[/yellow]")

        return success

    async def edit_provider(self, name: Optional[str]) -> bool:
        """Edit an existing provider configuration.

        Args:
            name: Provider name to edit

        Returns:
            True if successful, False otherwise
        """
        if not name:
            # Let user select provider to edit
            providers = config_manager.list_providers()
            if not providers:
                self.console.print("[red]No providers configured to edit.[/red]")
                return False

            name = await questionary.select(
                "Select provider to edit:", choices=providers
            ).ask_async()

            if not name:
                return False

        # Check if provider exists
        provider = config_manager.get_provider(name)
        if not provider:
            self.console.print(f"[red]Provider '{name}' not found.[/red]")
            return False

        self.console.print(f"[blue]Editing provider: {name}[/blue]")
        self.console.print("Leave fields empty to keep current values.\n")

        # Edit each field
        edited_provider = await self._edit_provider_fields(provider)
        if not edited_provider:
            self.console.print("[yellow]Edit cancelled.[/yellow]")
            return False

        # Test connection before saving
        self.console.print("\n[cyan]Testing edited configuration...[/cyan]")
        try:
            client = ClientFactory.create_client(edited_provider)
            is_valid = await client.validate_connection()
            await client.close()

            if not is_valid:
                keep = await questionary.confirm(
                    "Connection test failed. Keep changes anyway?", default=False
                ).ask_async()
                if not keep:
                    self.console.print("[yellow]Changes discarded.[/yellow]")
                    return False
        except Exception as e:
            self.console.print(f"[red]Connection test error: {e}[/red]")
            keep = await questionary.confirm(
                f"Connection test error: {e}. Keep changes anyway?", default=False
            ).ask_async()
            if not keep:
                return False

        # Save changes
        config_manager.set_provider(name, edited_provider)
        self.console.print(f"[green]✓ Provider '{name}' updated successfully![/green]")
        return True

    async def _edit_provider_fields(self, provider) -> Optional[object]:
        """Edit provider fields interactively.

        Args:
            provider: Existing provider to edit

        Returns:
            Edited provider object or None if cancelled
        """
        # Endpoint
        endpoint = await questionary.text(
            f"Endpoint [current: {provider.endpoint}]:",
            default=provider.endpoint,
            validate=lambda x: self._validate_endpoint(x) if x.strip() else True,
        ).ask_async()

        if endpoint is None:
            return None

        # API key
        api_key = None
        if (
            provider.api_key
            or await questionary.confirm("Edit API key?", default=False).ask_async()
        ):
            if provider.api_key:
                api_key = await questionary.password(
                    f"API key [current: {self._mask_api_key(provider.api_key)}]:",
                    validate=lambda x: len(x.strip()) >= 10
                    or "API key must be at least 10 characters",
                ).ask_async()
            else:
                api_key = await questionary.password(
                    "API key:",
                    validate=lambda x: len(x.strip()) >= 10
                    or "API key must be at least 10 characters",
                ).ask_async()

        if api_key is None and provider.api_key:  # Cancelled but had existing key
            return None

        # Model
        model = await questionary.text(
            f"Model [current: {provider.model or 'default'}]:", default=provider.model or ""
        ).ask_async()

        if model is None:
            return None

        # Temperature
        temperature = await questionary.text(
            f"Temperature [current: {provider.temperature}]:",
            default=str(provider.temperature),
            validate=lambda x: self._validate_temperature(x) if x.strip() else True,
        ).ask_async()

        if temperature is None:
            return None

        # Max tokens
        max_tokens = await questionary.text(
            f"Max tokens [current: {provider.max_tokens or 'unlimited'}]:",
            default=str(provider.max_tokens) if provider.max_tokens else "",
            validate=lambda x: self._validate_max_tokens(x) if x.strip() else True,
        ).ask_async()

        if max_tokens is None:
            return None

        # Convert to proper types
        temp_float = float(temperature) if temperature.strip() else 0.7
        max_tokens_int = int(max_tokens) if max_tokens.strip() else None

        # Create updated provider
        from vibe_coder.types.config import AIProvider

        return AIProvider(
            name=provider.name,
            endpoint=endpoint.strip(),
            api_key=api_key.strip() if api_key else provider.api_key,
            model=model.strip() if model.strip() else None,
            temperature=temp_float,
            max_tokens=max_tokens_int,
            headers=provider.headers,  # Keep existing headers
        )

    async def delete_provider(self, name: Optional[str]) -> bool:
        """Delete a provider configuration.

        Args:
            name: Provider name to delete

        Returns:
            True if successful, False otherwise
        """
        if not name:
            # Let user select provider to delete
            providers = config_manager.list_providers()
            if not providers:
                self.console.print("[red]No providers configured to delete.[/red]")
                return False

            name = await questionary.select(
                "Select provider to delete:", choices=providers
            ).ask_async()

            if not name:
                return False

        # Check if provider exists
        if not config_manager.has_provider(name):
            self.console.print(f"[red]Provider '{name}' not found.[/red]")
            return False

        # Check if it's the current provider
        current_provider = config_manager.get_current_provider()
        is_current = current_provider and current_provider.name == name

        # Show provider info before deletion
        provider = config_manager.get_provider(name)
        self.console.print(
            Panel(
                f"About to delete provider: [yellow]{name}[/yellow]\n"
                f"Endpoint: {provider.endpoint}\n"
                f"Model: {provider.model or 'default'}",
                title="Confirm Deletion",
                border_style="red",
            )
        )

        # Confirm deletion
        confirm_msg = f"Delete provider '{name}'?"
        if is_current:
            confirm_msg += " (This is your current provider)"

        confirmed = await questionary.confirm(confirm_msg, default=False).ask_async()

        if not confirmed:
            self.console.print("[yellow]Deletion cancelled.[/yellow]")
            return False

        # Delete provider
        config_manager.delete_provider(name)

        self.console.print(f"[green]✓ Provider '{name}' deleted successfully![/green]")

        if is_current:
            # Show remaining providers or message about no providers
            remaining = config_manager.list_providers()
            if remaining:
                self.console.print(f"[yellow]Note: '{name}' was your current provider.[/yellow]")
                self.console.print(
                    "[yellow]Use 'vibe-coder config set-current' to choose a new "
                    "current provider.[/yellow]"
                )
            else:
                self.console.print(
                    "[yellow]No providers remaining. Use 'vibe-coder setup' to add one.[/yellow]"
                )

        return True

    def _show_available_actions(self):
        """Show available config actions."""
        actions = [
            "list      - List all configured providers",
            "show      - Show detailed provider information",
            "add       - Add a new provider",
            "edit      - Edit existing provider configuration",
            "delete    - Delete a provider configuration",
        ]

        self.console.print(Panel("\n".join(actions), title="Available Actions", border_style="red"))

    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for display.

        Args:
            api_key: API key string

        Returns:
            Masked API key
        """
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

    def _validate_endpoint(self, value: str) -> bool:
        """Validate endpoint URL.

        Args:
            value: Endpoint URL string

        Returns:
            True if valid, False with error message if invalid
        """
        if not value.strip():
            return True  # Empty means keep current
        try:
            from urllib.parse import urlparse

            parsed = urlparse(value.strip())
            if parsed.scheme in ["http", "https"] and parsed.netloc:
                return True
            return "Please enter a valid URL with http:// or https://"
        except Exception:
            return "Please enter a valid URL"

    def _validate_temperature(self, value: str) -> bool:
        """Validate temperature input.

        Args:
            value: Temperature string value

        Returns:
            True if valid, False with error message if invalid
        """
        if not value.strip():
            return True  # Empty means keep current
        try:
            temp = float(value)
            if 0.0 <= temp <= 2.0:
                return True
            return "Temperature must be between 0.0 and 2.0"
        except ValueError:
            return "Please enter a valid number"

    def _validate_max_tokens(self, value: str) -> bool:
        """Validate max tokens input.

        Args:
            value: Max tokens string value

        Returns:
            True if valid, False with error message if invalid
        """
        if not value.strip():
            return True  # Empty means unlimited
        try:
            tokens = int(value)
            if tokens > 0:
                return True
            return "Max tokens must be a positive integer"
        except ValueError:
            return "Please enter a valid integer or leave empty"
