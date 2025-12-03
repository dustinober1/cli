"""Chat command implementation for Vibe Coder."""

import os
from typing import List, Optional

import questionary
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from vibe_coder.api.factory import ClientFactory
from vibe_coder.config.manager import config_manager
from vibe_coder.types.api import ApiMessage, MessageRole
from vibe_coder.commands.slash.registry import command_registry
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.commands.slash.git_ops import GitOperations


class ChatCommand:
    """Interactive chat interface for Vibe Coder."""

    def __init__(self):
        self.console = Console()
        self.messages: List[ApiMessage] = []
        self.client = None
        self.provider = None
        self.slash_parser = None
        self.git_info = None

        # Initialize slash command system
        self._initialize_slash_commands()

    def _initialize_slash_commands(self):
        """Initialize the slash command system."""
        # Import all commands to register them
        try:
            # Import command modules to register them
            import vibe_coder.commands.slash.commands.system
            import vibe_coder.commands.slash.commands.code
            import vibe_coder.commands.slash.commands.debug
            import vibe_coder.commands.slash.commands.test
            import vibe_coder.commands.slash.commands.git
            import vibe_coder.commands.slash.commands.project

            self.slash_parser = command_registry.get_parser()

            # Initialize git info if we're in a git repo
            working_dir = os.getcwd()
            git_ops = GitOperations(working_dir)
            if git_ops.is_git_repo():
                self.git_info = git_ops.get_git_info()

        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to initialize slash commands: {e}[/yellow]")
            self.slash_parser = None

    async def run(
        self,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> bool:
        """Run the interactive chat session.

        Args:
            provider_name: Override provider name
            model: Override model
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            True if chat completed successfully, False otherwise
        """
        try:
            # Setup provider
            if not await self._setup_provider(provider_name, model, temperature, max_tokens):
                return False

            # Welcome message
            self._show_welcome()

            # Chat loop
            await self._chat_loop()

            return True

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Chat interrupted by user.[/yellow]")
            return True
        except Exception as e:
            self.console.print(f"\n[red]Chat error: {e}[/red]")
            return False
        finally:
            if self.client:
                await self.client.close()

    async def _setup_provider(
        self,
        provider_name: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> bool:
        """Setup the AI provider and client.

        Args:
            provider_name: Override provider name
            model: Override model
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            True if setup successful, False otherwise
        """
        # Get provider configuration
        if provider_name:
            provider = config_manager.get_provider(provider_name)
            if not provider:
                self.console.print(f"[red]Provider '{provider_name}' not found.[/red]")
                self.console.print(
                    f"Available providers: {', '.join(config_manager.list_providers())}"
                )
                return False
        else:
            provider = config_manager.get_current_provider()
            if not provider:
                self.console.print(
                    "[red]No provider configured. Run 'vibe-coder setup' first.[/red]"
                )
                return False

        # Apply overrides
        if model:
            provider.model = model
        if temperature is not None:
            provider.temperature = temperature
        if max_tokens is not None:
            provider.max_tokens = max_tokens

        # Create client
        try:
            self.client = ClientFactory.create_client(provider)
            self.provider = provider
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to create client: {e}[/red]")
            return False

    def _show_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("🤖 ", style="blue")
        welcome_text.append("Welcome to Vibe Coder Chat!\n\n", style="bold")
        welcome_text.append("Provider: ", style="cyan")
        welcome_text.append(f"{self.provider.name}\n", style="yellow")
        welcome_text.append(f"Model: {self.provider.model or 'default'}\n", style="yellow")
        welcome_text.append(f"Temperature: {self.provider.temperature}\n\n", style="yellow")
        welcome_text.append("Type your message and press Enter.\n", style="green")
        welcome_text.append("Type ", style="green")
        welcome_text.append("/help", style="bold yellow")
        welcome_text.append(" for commands or ", style="green")
        welcome_text.append("/exit", style="bold yellow")
        welcome_text.append(" to quit.\n", style="green")

        self.console.print(Panel.fit(welcome_text, title="Chat Session", border_style="blue"))

    async def _chat_loop(self):
        """Main chat interaction loop."""
        while True:
            try:
                # Get user input
                user_input = await questionary.text(
                    "[bold green]You:[/bold green] ",
                    multiline=True,
                    validate=lambda x: len(x.strip()) > 0 or "Please enter a message or command",
                    qmark="",
                ).ask_async()

                if not user_input:
                    continue

                user_input = user_input.strip()

                # Handle commands
                if user_input.startswith("/"):
                    should_continue = await self._handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Add user message
                user_message = ApiMessage(role=MessageRole.USER, content=user_input)
                self.messages.append(user_message)

                # Get AI response
                await self._get_ai_response()

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]Error in chat loop: {e}[/red]")
                continue

    async def _handle_command(self, command: str) -> bool:
        """Handle chat commands using the slash command system.

        Args:
            command: Command string starting with /

        Returns:
            True to continue chat, False to exit
        """
        # Use the slash command parser if available
        if self.slash_parser and self.slash_parser.is_slash_command(command):
            return await self._handle_slash_command(command)
        else:
            # Fallback to legacy command handling
            return await self._handle_legacy_command(command)

    async def _handle_slash_command(self, command: str) -> bool:
        """Handle slash commands using the new parser system.

        Args:
            command: Command string starting with /

        Returns:
            True to continue chat, False to exit
        """
        # Create command context
        context = CommandContext(
            chat_history=self.messages,
            current_provider=self.provider,
            working_directory=os.getcwd(),
            git_info=self.git_info
        )

        # Parse and execute the command
        success, response = await self.slash_parser.parse_and_execute(command, context)

        if success:
            # Display the command response
            self.console.print(Panel(
                Markdown(response),
                title="[bold yellow]Command Result[/bold yellow]",
                border_style="yellow"
            ))

            # Check if command wants to exit
            parsed = self.slash_parser.parse_command(command)
            if parsed:
                command_name, _ = parsed
                if command_name in ["exit", "quit"]:
                    return False
        else:
            # Display error
            self.console.print(f"[red]{response}[/red]")

        return True

    async def _handle_legacy_command(self, command: str) -> bool:
        """Handle legacy commands for backward compatibility.

        Args:
            command: Command string starting with /

        Returns:
            True to continue chat, False to exit
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/exit" or cmd == "/quit":
            return False
        elif cmd == "/help":
            self._show_help()
        elif cmd == "/clear":
            self._clear_history()
        elif cmd == "/history":
            self._show_history()
        elif cmd == "/provider":
            self._show_provider_info()
        elif cmd == "/save":
            await self._save_conversation(args)
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("Type /help for available commands")

        return True

    def _show_help(self):
        """Display help information."""
        # Use slash command system help if available
        if self.slash_parser:
            help_text = self.slash_parser.get_help_text()
            self.console.print(Panel(
                Markdown(help_text),
                title="📚 Slash Commands",
                border_style="cyan"
            ))
        else:
            # Fallback help
            help_text = Text()
            help_text.append("📚 Available Commands:\n\n", style="bold cyan")
            help_text.append("/help, /?      ", style="yellow")
            help_text.append("Show this help message\n", style="white")
            help_text.append("/exit, /quit   ", style="yellow")
            help_text.append("Exit the chat\n", style="white")
            help_text.append("/clear         ", style="yellow")
            help_text.append("Clear conversation history\n", style="white")
            help_text.append("/history       ", style="yellow")
            help_text.append("Show conversation history\n", style="white")
            help_text.append("/provider      ", style="yellow")
            help_text.append("Show current provider info\n", style="white")
            help_text.append("/save [name]   ", style="yellow")
            help_text.append("Save conversation to file\n", style="white")

            self.console.print(Panel(help_text, title="Help", border_style="cyan"))

    def _clear_history(self):
        """Clear conversation history."""
        self.messages = []
        self.console.print("[green]✓ Conversation history cleared[/green]")

    def _show_history(self):
        """Show conversation history."""
        if not self.messages:
            self.console.print("[yellow]No messages in history[/yellow]")
            return

        history_text = Text()
        history_text.append("💬 Conversation History:\n\n", style="bold cyan")

        for i, message in enumerate(self.messages, 1):
            role_color = "blue" if message.role == MessageRole.USER else "green"
            role_name = "You" if message.role == MessageRole.USER else "AI"
            history_text.append(f"{i}. [{role_name}]", style=role_color)
            history_text.append(f": {message.content[:100]}")
            if len(message.content) > 100:
                history_text.append("...")
            history_text.append("\n\n", style="white")

        self.console.print(Panel(history_text, title="History", border_style="cyan"))

    def _show_provider_info(self):
        """Show current provider information."""
        info_text = Text()
        info_text.append("🔧 Current Provider Information:\n\n", style="bold cyan")
        info_text.append("Name: ", style="yellow")
        info_text.append(f"{self.provider.name}\n", style="white")
        info_text.append("Model: ", style="yellow")
        info_text.append(f"{self.provider.model or 'default'}\n", style="white")
        info_text.append("Endpoint: ", style="yellow")
        info_text.append(f"{self.provider.endpoint}\n", style="white")
        info_text.append("Temperature: ", style="yellow")
        info_text.append(f"{self.provider.temperature}\n", style="white")
        if self.provider.max_tokens:
            info_text.append("Max Tokens: ", style="yellow")
            info_text.append(f"{self.provider.max_tokens}\n", style="white")

        self.console.print(Panel(info_text, title="Provider Info", border_style="cyan"))

    async def _save_conversation(self, filename: Optional[str]):
        """Save conversation to file.

        Args:
            filename: Optional filename for saving
        """
        if not self.messages:
            self.console.print("[yellow]No messages to save[/yellow]")
            return

        if not filename:
            filename = await questionary.text(
                "Enter filename to save conversation:",
                default="conversation.md",
                validate=lambda x: len(x.strip()) > 0 or "Filename is required",
            ).ask_async()
            if not filename:
                return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# Vibe Coder Conversation\n\n")
                f.write(f"Provider: {self.provider.name}\n")
                f.write(f"Model: {self.provider.model or 'default'}\n")
                f.write(f"Temperature: {self.provider.temperature}\n\n")
                f.write("---\n\n")

                for message in self.messages:
                    role_name = "You" if message.role == MessageRole.USER else "AI"
                    f.write(f"## {role_name}\n\n")
                    f.write(f"{message.content}\n\n")
                    f.write("---\n\n")

            self.console.print(f"[green]✓ Conversation saved to {filename}[/green]")

        except Exception as e:
            self.console.print(f"[red]Failed to save conversation: {e}[/red]")

    async def _get_ai_response(self):
        """Get and display AI response."""
        try:
            # Show progress indicator for non-streaming display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                progress.add_task("Thinking...", total=None)

                response_chunks = []
                current_response = ""

                # Create live display for streaming
                with Live(console=self.console, refresh_per_second=4) as live:
                    # Start streaming
                    async for chunk in self.client.stream_request(self.messages):
                        if chunk:
                            response_chunks.append(chunk)
                            current_response += chunk

                            # Update the live display
                            panel = Panel(
                                Markdown(current_response),
                                title=f"[bold blue]{self.provider.name}[/bold blue]",
                                border_style="blue",
                            )
                            live.update(panel)

                final_response = "".join(response_chunks)

                # Add AI message to history
                ai_message = ApiMessage(role=MessageRole.ASSISTANT, content=final_response)
                self.messages.append(ai_message)

                # Show final response in a nice panel
                final_panel = Panel(
                    Markdown(final_response),
                    title=f"[bold blue]{self.provider.name}[/bold blue]",
                    border_style="blue",
                )
                self.console.print(final_panel)
                self.console.print()  # Add spacing

        except Exception as e:
            self.console.print(f"[red]Error getting response: {e}[/red]")
            error_message = ApiMessage(
                role=MessageRole.ASSISTANT, content=f"Sorry, I encountered an error: {e}"
            )
            self.messages.append(error_message)
