#!/usr/bin/env python3
"""
Vibe Coder - Main CLI Entry Point

A provider-independent CLI coding assistant built with Python.
"""
from typing import Optional

import typer
from rich.console import Console

from vibe_coder.commands.chat import ChatCommand
from vibe_coder.commands.config import ConfigCommand
from vibe_coder.commands.setup import SetupCommand

app = typer.Typer(
    name="vibe-coder",
    help="🐍 A configurable CLI coding assistant that works with any AI API",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def chat(
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider name to use for this session"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use (overrides provider default)"
    ),
    temperature: Optional[float] = typer.Option(
        None, "--temperature", "-t", help="Temperature for response generation (0.0-2.0)"
    ),
):
    """
    Start an interactive chat session with the AI.

    Examples:
        vibe-coder chat
        vibe-coder chat --provider my-openai
        vibe-coder chat --model gpt-4 --temperature 0.9

    Chat Commands:
        /help          Show available commands
        /exit, /quit   Exit the chat
        /clear         Clear conversation history
        /history       Show conversation history
        /provider      Show current provider info
        /save [name]   Save conversation to file
    """
    import asyncio

    chat_command = ChatCommand()
    success = asyncio.run(
        chat_command.run(provider_name=provider, model=model, temperature=temperature)
    )

    if not success:
        raise typer.Exit(1)


@app.command()
def setup():
    """
    Run the interactive setup wizard to configure providers.

    This will guide you through configuring:
    - Provider selection (OpenAI, Anthropic, Ollama, etc.)
    - API endpoint and key configuration
    - Model selection and parameters
    - Connection testing
    """
    import asyncio

    setup_command = SetupCommand()
    success = asyncio.run(setup_command.run())

    if not success:
        raise typer.Exit(1)


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: list, show, add, edit, delete"),
    name: Optional[str] = typer.Argument(None, help="Provider name (for show, edit, delete)"),
):
    """
    Manage provider configurations.

    Actions:
        list      - List all configured providers
        show      - Show detailed provider information
        add       - Add a new provider (launches setup wizard)
        edit      - Edit existing provider configuration
        delete    - Delete a provider configuration

    Examples:
        vibe-coder config list
        vibe-coder config show my-openai
        vibe-coder config add
        vibe-coder config edit my-claude
        vibe-coder delete old-provider
    """
    import asyncio

    config_command = ConfigCommand()
    success = asyncio.run(config_command.run(action, name))

    if not success:
        raise typer.Exit(1)


@app.command()
def test(
    provider: Optional[str] = typer.Argument(
        None, help="Provider name to test (uses current if not specified)"
    ),
):
    """
    Test connection to an AI provider.

    Examples:
        vibe-coder test
        vibe-coder test my-openai
        vibe-coder test --all
    """
    import asyncio

    from vibe_coder.commands.test import TestCommand

    test_command = TestCommand()
    success = asyncio.run(test_command.run(provider))

    if not success:
        raise typer.Exit(1)


@app.callback()
def main():
    """
    Vibe Coder - Your AI coding assistant 🐍✨

    A powerful, provider-independent CLI tool that works with OpenAI,
    Anthropic, Ollama, and any custom AI API endpoint.
    """
    pass


if __name__ == "__main__":
    app()
