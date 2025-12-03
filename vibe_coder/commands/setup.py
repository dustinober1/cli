"""Setup command implementation for Vibe Coder."""

import asyncio
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from vibe_coder.api.factory import ClientFactory
from vibe_coder.config.manager import config_manager
from vibe_coder.types.config import AIProvider


class SetupCommand:
    """Interactive setup wizard for Vibe Coder."""

    def __init__(self):
        self.console = Console()

    async def run(self) -> bool:
        """Run the complete setup wizard.

        Returns:
            True if setup completed successfully, False otherwise
        """
        try:
            self.console.print(
                Panel.fit(
                    "[bold green]🚀 Welcome to Vibe Coder Setup![/bold green]\n\n"
                    "Let's configure your first AI provider. This wizard will guide you through "
                    "the process step by step.",
                    title="Setup Wizard",
                    border_style="green",
                )
            )

            # Step 1: Check for existing configuration
            if await self._check_existing_config():
                return True

            # Step 2: Provider selection
            provider_type = await self._select_provider_type()
            if not provider_type:
                self.console.print("[yellow]Setup cancelled.[/yellow]")
                return False

            # Step 3: Provider configuration
            provider_config = await self._configure_provider(provider_type)
            if not provider_config:
                self.console.print("[yellow]Setup cancelled.[/yellow]")
                return False

            # Step 4: Connection testing
            if not await self._test_connection(provider_config):
                self.console.print("[red]Setup failed: Connection test failed.[/red]")
                return False

            # Step 5: Save configuration
            await self._save_configuration(provider_config)

            # Step 6: Success and next steps
            self._show_success_message()
            return True

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Setup cancelled by user.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"\n[red]Setup error: {e}[/red]")
            return False

    async def _check_existing_config(self) -> bool:
        """Check for existing configuration and ask user what to do.

        Returns:
            True if user wants to keep existing config, False to continue setup
        """
        providers = config_manager.list_providers()
        if not providers:
            return False

        self.console.print(
            f"[blue]Found {len(providers)} existing provider configuration(s):[/blue]"
        )

        table = Table(title="Existing Providers")
        table.add_column("Name", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Endpoint", style="green")
        table.add_column("Current", style="yellow")

        current = config_manager.get_current_provider_name()
        for provider_name in providers:
            provider = config_manager.get_provider(provider_name)
            current_marker = "✓" if provider_name == current else ""
            table.add_row(
                provider_name, provider.model or "default", provider.endpoint, current_marker
            )

        self.console.print(table)

        choice = await questionary.select(
            "What would you like to do?",
            choices=[
                {"name": "Keep existing configuration", "value": "keep"},
                {"name": "Add a new provider", "value": "add"},
                {"name": "Replace existing configuration", "value": "replace"},
                {"name": "Exit setup", "value": "exit"},
            ],
        ).ask_async()

        if choice == "keep":
            self.console.print("[green]Keeping existing configuration.[/green]")
            return True
        elif choice == "exit":
            self.console.print("[yellow]Exiting setup.[/yellow]")
            raise KeyboardInterrupt()
        elif choice == "replace":
            if await questionary.confirm(
                "This will remove all existing providers. Are you sure?", default=False
            ).ask_async():
                config_manager.reset_config()
                self.console.print("[yellow]Existing configuration removed.[/yellow]")
                return False
            else:
                return True  # User cancelled the replace
        else:  # add
            return False

    async def _select_provider_type(self) -> Optional[str]:
        """Let user select provider type.

        Returns:
            Selected provider type or None if cancelled
        """
        providers = [
            {
                "name": "OpenAI",
                "description": "GPT models (GPT-4, GPT-3.5, etc.)",
                "value": "openai",
            },
            {
                "name": "Anthropic",
                "description": "Claude models (Claude-3.5 Sonnet, Haiku, etc.)",
                "value": "anthropic",
            },
            {"name": "Ollama (Local)", "description": "Local models via Ollama", "value": "ollama"},
            {
                "name": "LM Studio (Local)",
                "description": "Local models via LM Studio",
                "value": "lmstudio",
            },
            {
                "name": "Custom Endpoint",
                "description": "Any OpenAI-compatible API",
                "value": "custom",
            },
        ]

        choice = await questionary.select(
            "Which AI provider would you like to configure?", choices=providers, use_indicator=True
        ).ask_async()

        return choice

    async def _configure_provider(self, provider_type: str) -> Optional[AIProvider]:
        """Configure provider details.

        Args:
            provider_type: Type of provider being configured

        Returns:
            Configured AIProvider or None if cancelled
        """
        self.console.print(f"\n[blue]Configuring {provider_type.upper()} provider...[/blue]\n")

        # Provider name
        name = await questionary.text(
            "Enter a name for this provider (e.g., 'my-openai', 'claude-pro'):",
            validate=lambda x: len(x.strip()) > 0 or "Provider name is required",
        ).ask_async()

        if not name:
            return None

        # Check for existing name
        if config_manager.has_provider(name):
            overwrite = await questionary.confirm(
                f"Provider '{name}' already exists. Overwrite?", default=False
            ).ask_async()
            if not overwrite:
                return None

        # API endpoint
        endpoint = await self._get_endpoint_for_provider(provider_type, name)

        if not endpoint:
            return None

        # API key (skip for some local providers)
        api_key = None
        if provider_type not in ["ollama", "lmstudio"]:
            api_key = await questionary.password(
                "Enter your API key:",
                validate=lambda x: len(x.strip()) >= 10 or "API key must be at least 10 characters",
            ).ask_async()

            if not api_key:
                return None

        # Model selection
        model = await self._get_model_for_provider(provider_type)

        # Advanced settings
        self.console.print("\n[cyan]Advanced settings (press Enter for defaults):[/cyan]")

        temperature = await questionary.text(
            "Temperature (0.0-2.0, default 0.7):",
            default="0.7",
            validate=lambda x: self._validate_temperature(x),
        ).ask_async()

        max_tokens = await questionary.text(
            "Max tokens (default 4096, leave empty for unlimited):",
            default="",
            validate=lambda x: self._validate_max_tokens(x),
        ).ask_async()

        # Convert to proper types
        temp_float = float(temperature) if temperature else 0.7
        max_tokens_int = int(max_tokens) if max_tokens.strip() else None

        return AIProvider(
            name=name.strip(),
            endpoint=endpoint.strip(),
            api_key=api_key.strip() if api_key else "",
            model=model.strip() if model else None,
            temperature=temp_float,
            max_tokens=max_tokens_int,
        )

    async def _get_endpoint_for_provider(self, provider_type: str, name: str) -> Optional[str]:
        """Get endpoint URL for provider type.

        Args:
            provider_type: Type of provider
            name: Provider name (for custom endpoint suggestion)

        Returns:
            Endpoint URL or None if cancelled
        """
        if provider_type == "openai":
            return "https://api.openai.com/v1"
        elif provider_type == "anthropic":
            return "https://api.anthropic.com"
        elif provider_type == "ollama":
            endpoint = await questionary.text(
                "Ollama endpoint URL:",
                default="http://localhost:11434/v1",
                validate=lambda x: self._validate_endpoint(x),
            ).ask_async()
            return endpoint
        elif provider_type == "lmstudio":
            endpoint = await questionary.text(
                "LM Studio endpoint URL:",
                default="http://localhost:1234/v1",
                validate=lambda x: self._validate_endpoint(x),
            ).ask_async()
            return endpoint
        else:  # custom
            endpoint = await questionary.text(
                "Custom endpoint URL:", validate=lambda x: self._validate_endpoint(x)
            ).ask_async()
            return endpoint

    async def _get_model_for_provider(self, provider_type: str) -> Optional[str]:
        """Get model for provider type.

        Args:
            provider_type: Type of provider

        Returns:
            Model name or None if cancelled
        """
        if provider_type == "openai":
            models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        elif provider_type == "anthropic":
            models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
        elif provider_type in ["ollama", "lmstudio"]:
            # For local providers, suggest common models but allow custom
            model = await questionary.text(
                "Model name (e.g., llama3, codellama, mistral):",
                default="llama3",
                validate=lambda x: len(x.strip()) > 0 or "Model name is required",
            ).ask_async()
            return model
        else:  # custom
            model = await questionary.text(
                "Model name:", validate=lambda x: len(x.strip()) > 0 or "Model name is required"
            ).ask_async()
            return model

        # For OpenAI and Anthropic, show selection
        model = await questionary.select("Select model:", choices=models).ask_async()
        return model

    def _validate_temperature(self, value: str) -> bool:
        """Validate temperature input.

        Args:
            value: Temperature string value

        Returns:
            True if valid, False with error message if invalid
        """
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

    def _validate_endpoint(self, value: str) -> bool:
        """Validate endpoint URL.

        Args:
            value: Endpoint URL string

        Returns:
            True if valid, False with error message if invalid
        """
        if not value.strip():
            return "Endpoint URL is required"
        try:
            from urllib.parse import urlparse

            parsed = urlparse(value.strip())
            if parsed.scheme in ["http", "https"] and parsed.netloc:
                return True
            return "Please enter a valid URL with http:// or https://"
        except Exception:
            return "Please enter a valid URL"

    async def _test_connection(self, provider: AIProvider) -> bool:
        """Test connection to the provider.

        Args:
            provider: Provider configuration to test

        Returns:
            True if connection test passes, False otherwise
        """
        self.console.print("\n[cyan]Testing connection...[/cyan]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Initializing connection...", total=None)

                # Create client
                client = ClientFactory.create_client(provider)
                progress.update(task, description="Validating API credentials...")

                # Test connection
                is_valid = await client.validate_connection()

                if is_valid:
                    progress.update(task, description="✅ Connection successful!")
                    await asyncio.sleep(1)  # Brief pause to show success
                    return True
                else:
                    progress.update(task, description="❌ Connection failed")
                    return False

        except Exception as e:
            self.console.print(f"[red]Connection test error: {e}[/red]")
            return False

    async def _save_configuration(self, provider: AIProvider):
        """Save the provider configuration.

        Args:
            provider: Provider configuration to save
        """
        self.console.print("\n[cyan]Saving configuration...[/cyan]")

        # Save provider
        config_manager.set_provider(provider.name, provider)

        # Set as current provider
        config_manager.set_current_provider(provider.name)

        self.console.print("[green]✅ Configuration saved successfully![/green]")

    def _show_success_message(self):
        """Display success message and next steps."""
        success_text = Text()
        success_text.append("🎉 ", style="green")
        success_text.append("Setup completed successfully!\n\n", style="bold green")
        success_text.append("You can now start chatting:\n", style="cyan")
        success_text.append("  vibe-coder chat\n\n", style="yellow")
        success_text.append("Or manage your configuration:\n", style="cyan")
        success_text.append("  vibe-coder config list\n", style="yellow")
        success_text.append("  vibe-coder config show\n\n", style="yellow")
        success_text.append("Test your connection:\n", style="cyan")
        success_text.append("  vibe-coder test\n", style="yellow")

        self.console.print(
            Panel.fit(success_text, title="Setup Complete! 🚀", border_style="green")
        )
