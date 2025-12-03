# CLI Vibe Coder - Python Implementation Plan (Part 2)

This document continues from IMPLEMENTATION_PLAN_PYTHON.md

---

## Phase 4 (Continued): Interactive Prompts & User Interface

### Task 4.2: Create Provider Selection Prompt
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**File:** `vibe_coder/prompts/select_provider.py`

```python
import questionary
from typing import Optional
from rich.console import Console
from vibe_coder.config.manager import config_manager

console = Console()

async def select_provider() -> Optional[str]:
    """
    Prompt user to select a provider.

    Returns:
        Selected provider name or None
    """
    providers = config_manager.list_providers()

    if not providers:
        console.print("[yellow]No providers configured. Run 'vibe-coder setup' first.[/yellow]")
        return None

    # Add option to create new provider
    choices = providers + ["➕ Add new provider"]

    selected = await questionary.select(
        "Select a provider:",
        choices=choices
    ).ask_async()

    if selected == "➕ Add new provider":
        return None

    return selected
```

---

### Task 4.3: Create Chat Interface
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `vibe_coder/prompts/chat_interface.py`

```python
import asyncio
from typing import List, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
import questionary

from vibe_coder.api.base_client import BaseApiClient
from vibe_coder.types.api import ApiMessage, ApiRequest, MessageRole
from vibe_coder.utils.logger import log_error, log_info
from vibe_coder.utils.token_counter import estimate_tokens, format_token_usage

console = Console()

class ChatInterface:
    """Interactive chat interface."""

    def __init__(self, client: BaseApiClient, system_prompt: Optional[str] = None):
        """Initialize chat interface."""
        self.client = client
        self.conversation_history: List[ApiMessage] = []
        self.running = True

        # Add system prompt if provided
        if system_prompt:
            self.conversation_history.append(
                ApiMessage(role=MessageRole.SYSTEM, content=system_prompt)
            )

    async def start(self):
        """Start the chat loop."""
        console.print(Panel.fit(
            "[bold cyan]Vibe Coder - Interactive Chat[/bold cyan]\n"
            f"Connected to: {self.client.provider.name}\n"
            "Type /help for commands, /exit to quit",
            border_style="cyan"
        ))

        while self.running:
            try:
                # Get user input
                user_input = await questionary.text(
                    "You:",
                    multiline=False
                ).ask_async()

                if not user_input:
                    continue

                # Check for slash commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                    continue

                # Process as chat message
                await self.handle_user_input(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Chat interrupted. Type /exit to quit.[/yellow]")
            except Exception as e:
                log_error(f"Error in chat loop: {e}")

    async def handle_user_input(self, user_input: str):
        """Handle regular chat input."""
        # Add user message to history
        self.conversation_history.append(
            ApiMessage(role=MessageRole.USER, content=user_input)
        )

        # Create request
        request = ApiRequest(
            messages=self.conversation_history,
            model=self.client.model,
            temperature=self.client.provider.temperature,
        )

        # Show spinner while waiting
        with console.status("[bold cyan]Thinking...[/bold cyan]"):
            try:
                # Get response
                response = await self.client.send_request(request)

                # Add to history
                self.conversation_history.append(
                    ApiMessage(role=MessageRole.ASSISTANT, content=response.content)
                )

                # Display response
                console.print("\n[bold cyan]Assistant:[/bold cyan]")
                console.print(Markdown(response.content))

                # Show token usage
                if response.usage:
                    console.print(f"\n[dim]{format_token_usage(response.usage)}[/dim]")

            except Exception as e:
                log_error(f"Failed to get response: {e}")

        console.print()  # Empty line for spacing

    async def handle_command(self, command: str):
        """Handle slash commands."""
        cmd_parts = command.split()
        cmd_name = cmd_parts[0].lower()

        if cmd_name == "/help":
            self.show_help()
        elif cmd_name == "/exit" or cmd_name == "/quit":
            await self.exit()
        elif cmd_name == "/clear":
            self.clear_history()
        elif cmd_name == "/save":
            filename = cmd_parts[1] if len(cmd_parts) > 1 else None
            await self.save_conversation(filename)
        elif cmd_name == "/model":
            if len(cmd_parts) > 1:
                self.client.model = cmd_parts[1]
                log_info(f"Model changed to: {cmd_parts[1]}")
            else:
                console.print(f"Current model: {self.client.model}")
        elif cmd_name == "/tokens":
            self.show_token_usage()
        else:
            console.print(f"[yellow]Unknown command: {cmd_name}[/yellow]")
            console.print("Type /help for available commands")

    def show_help(self):
        """Display help message."""
        help_text = """
[bold cyan]Available Commands:[/bold cyan]

  [bold]/help[/bold]              Show this help message
  [bold]/exit[/bold] or [bold]/quit[/bold]    Exit the chat
  [bold]/clear[/bold]             Clear conversation history
  [bold]/save [filename][/bold]   Save conversation to file
  [bold]/model [name][/bold]      Change or show current model
  [bold]/tokens[/bold]            Show token usage statistics
        """
        console.print(Panel(help_text, border_style="cyan"))

    def clear_history(self):
        """Clear conversation history."""
        # Keep system message if it exists
        system_messages = [
            msg for msg in self.conversation_history
            if msg.role == MessageRole.SYSTEM
        ]
        self.conversation_history = system_messages
        log_info("Conversation history cleared")

    async def save_conversation(self, filename: Optional[str] = None):
        """Save conversation to file."""
        from datetime import datetime
        from pathlib import Path

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.md"

        filepath = Path.cwd() / filename

        # Format as markdown
        content = "# Vibe Coder Conversation\n\n"
        for msg in self.conversation_history:
            if msg.role == MessageRole.SYSTEM:
                content += f"**System:** {msg.content}\n\n"
            elif msg.role == MessageRole.USER:
                content += f"**You:** {msg.content}\n\n"
            else:
                content += f"**Assistant:**\n\n{msg.content}\n\n"
            content += "---\n\n"

        filepath.write_text(content)
        log_info(f"Conversation saved to: {filepath}")

    def show_token_usage(self):
        """Show current token usage."""
        total_tokens = sum(
            estimate_tokens(msg.content)
            for msg in self.conversation_history
        )
        console.print(f"[cyan]Estimated tokens in context: {total_tokens}[/cyan]")

    async def exit(self):
        """Exit the chat interface."""
        confirm = await questionary.confirm(
            "Save conversation before exiting?",
            default=False
        ).ask_async()

        if confirm:
            await self.save_conversation()

        console.print("[cyan]Goodbye! 👋[/cyan]")
        self.running = False
```

---

## Phase 5: CLI Commands Implementation

### Task 5.1: Implement Chat Command
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/commands/chat.py`

```python
import asyncio
from typing import Optional
import typer
from rich.console import Console

from vibe_coder.config.manager import config_manager
from vibe_coder.api.client_factory import create_client
from vibe_coder.prompts.chat_interface import ChatInterface
from vibe_coder.prompts.select_provider import select_provider
from vibe_coder.utils.logger import log_error, log_info

console = Console()

async def chat_command_async(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
):
    """Start an interactive chat session."""
    try:
        # Get provider
        if not provider:
            provider = await select_provider()
            if not provider:
                console.print("[yellow]No provider selected. Exiting.[/yellow]")
                return

        # Load provider config
        provider_config = config_manager.get_provider(provider)
        if not provider_config:
            log_error(f"Provider '{provider}' not found")
            console.print("Run 'vibe-coder setup' to configure a provider")
            return

        # Override settings if provided
        if model:
            provider_config.model = model
        if temperature is not None:
            provider_config.temperature = temperature

        # Create client
        log_info(f"Connecting to {provider_config.name}...")
        client = create_client(provider_config)

        # Validate connection
        with console.status("[cyan]Validating connection...[/cyan]"):
            is_valid = await client.validate_connection()

        if not is_valid:
            log_error("Failed to connect to API")
            console.print("Please check your configuration and try again")
            return

        log_info("Connection validated ✓")

        # Start chat interface
        chat = ChatInterface(client)
        await chat.start()

    except Exception as e:
        log_error(f"Chat error: {e}")
        raise typer.Exit(code=1)

def chat_command(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider to use"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature"),
):
    """Start an interactive chat session."""
    asyncio.run(chat_command_async(provider, model, temperature))
```

---

### Task 5.2: Implement Setup Command
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**File:** `vibe_coder/commands/setup.py`

```python
import asyncio
import typer
from rich.console import Console

from vibe_coder.config.manager import config_manager
from vibe_coder.prompts.setup_wizard import run_setup_wizard
from vibe_coder.api.client_factory import create_client
from vibe_coder.utils.logger import log_success, log_error, log_info

console = Console()

async def setup_command_async():
    """Run the setup wizard."""
    try:
        # Run wizard
        provider = await run_setup_wizard()

        # Save configuration
        config_manager.set_provider(provider.name, provider)
        config_manager.set_current_provider(provider.name)

        log_success(f"Provider '{provider.name}' configured successfully!")

        # Ask to test connection
        import questionary
        test_conn = await questionary.confirm(
            "Test connection now?",
            default=True
        ).ask_async()

        if test_conn:
            log_info("Testing connection...")
            client = create_client(provider)

            with console.status("[cyan]Validating connection...[/cyan]"):
                is_valid = await client.validate_connection()

            if is_valid:
                log_success("Connection test successful! ✓")
            else:
                log_error("Connection test failed")
                console.print("Please check your API key and endpoint")

    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/yellow]")
        raise typer.Exit()
    except Exception as e:
        log_error(f"Setup failed: {e}")
        raise typer.Exit(code=1)

def setup_command():
    """Run the setup wizard to configure providers."""
    asyncio.run(setup_command_async())
```

---

## Phase 6: Utilities & Helpers

### Task 6.1: Create Logger Utility
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**File:** `vibe_coder/utils/logger.py`

```python
import os
from rich.console import Console

console = Console()

DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

def log_success(message: str) -> None:
    """Log a success message."""
    console.print(f"[green]✓[/green] {message}")

def log_error(message: str) -> None:
    """Log an error message."""
    console.print(f"[red]✗[/red] {message}", style="red")

def log_warning(message: str) -> None:
    """Log a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")

def log_info(message: str) -> None:
    """Log an info message."""
    console.print(f"[blue]ℹ[/blue] {message}", style="blue")

def log_debug(message: str) -> None:
    """Log a debug message (only if DEBUG=true)."""
    if DEBUG_MODE:
        console.print(f"[dim][DEBUG][/dim] {message}", style="dim")

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return DEBUG_MODE
```

---

### Task 6.2: Create Token Counter Utility
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/utils/token_counter.py`

```python
from typing import Optional
from vibe_coder.types.api import TokenUsage

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    This is a rough estimation. For accurate counts,
    use tiktoken library.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    # Rough estimate: ~4 characters per token
    return len(text) // 4

def format_token_usage(usage: TokenUsage) -> str:
    """
    Format token usage for display.

    Args:
        usage: Token usage data

    Returns:
        Formatted string
    """
    return (
        f"Tokens: {usage.total_tokens} "
        f"(prompt: {usage.prompt_tokens}, "
        f"completion: {usage.completion_tokens})"
    )

def estimate_cost(tokens: int, model: str) -> float:
    """
    Estimate cost for token usage.

    Args:
        tokens: Number of tokens
        model: Model name

    Returns:
        Estimated cost in USD
    """
    # Pricing per 1M tokens (approximate)
    pricing = {
        "gpt-4": 30.0,
        "gpt-4-turbo": 10.0,
        "gpt-3.5-turbo": 0.50,
        "claude-3-opus": 15.0,
        "claude-3-sonnet": 3.0,
        "claude-3-haiku": 0.25,
    }

    # Find matching model
    cost_per_million = 1.0  # Default
    for model_key, price in pricing.items():
        if model_key in model.lower():
            cost_per_million = price
            break

    return (tokens / 1_000_000) * cost_per_million
```

---

### Task 6.3: Create Code Formatter Utility
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `vibe_coder/utils/code_formatter.py`

```python
import re
from typing import List, Tuple
from rich.syntax import Syntax
from rich.console import Console

console = Console()

def detect_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Detect code blocks in markdown text.

    Args:
        text: Markdown text

    Returns:
        List of (language, code) tuples
    """
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    return [(lang or "text", code.strip()) for lang, code in matches]

def format_code_response(text: str) -> None:
    """
    Format and display code response with syntax highlighting.

    Args:
        text: Response text containing code blocks
    """
    # Split by code blocks
    parts = re.split(r"(```\w*\n.*?```)", text, flags=re.DOTALL)

    for part in parts:
        if part.startswith("```"):
            # Extract language and code
            match = re.match(r"```(\w+)?\n(.*?)```", part, re.DOTALL)
            if match:
                lang, code = match.groups()
                lang = lang or "text"

                # Display with syntax highlighting
                syntax = Syntax(code.strip(), lang, theme="monokai", line_numbers=True)
                console.print(syntax)
        else:
            # Regular text
            if part.strip():
                console.print(part.strip())

def extract_code(text: str, language: Optional[str] = None) -> str:
    """
    Extract code blocks from markdown.

    Args:
        text: Markdown text
        language: Optional language to filter by

    Returns:
        Extracted code
    """
    blocks = detect_code_blocks(text)

    if language:
        blocks = [(lang, code) for lang, code in blocks if lang == language]

    return "\n\n".join(code for _, code in blocks)
```

---

### Task 6.4: Create File Operations Utility
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

**File:** `vibe_coder/utils/file_ops.py`

```python
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from vibe_coder.types.api import ApiMessage

def save_conversation(
    messages: List[ApiMessage],
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save conversation to markdown file.

    Args:
        messages: Conversation messages
        filename: Optional filename
        output_dir: Optional output directory

    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = Path.cwd()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.md"

    filepath = output_dir / filename

    # Format as markdown
    content = "# Vibe Coder Conversation\n\n"
    content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    content += "---\n\n"

    for msg in messages:
        role = msg.role.value.title()
        content += f"## {role}\n\n{msg.content}\n\n"

    filepath.write_text(content)
    return filepath

def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path
    """
    path.mkdir(parents=True, exist_ok=True)

def load_conversation(filepath: Path) -> List[ApiMessage]:
    """
    Load conversation from markdown file.

    Args:
        filepath: Path to conversation file

    Returns:
        List of messages
    """
    # Simple implementation - can be enhanced
    content = filepath.read_text()
    messages = []

    # Parse markdown sections
    sections = re.split(r"## (User|Assistant|System)\n\n", content)

    role_map = {
        "User": MessageRole.USER,
        "Assistant": MessageRole.ASSISTANT,
        "System": MessageRole.SYSTEM,
    }

    for i in range(1, len(sections), 2):
        role_str = sections[i]
        content = sections[i + 1].strip()

        if role_str in role_map:
            messages.append(
                ApiMessage(role=role_map[role_str], content=content)
            )

    return messages
```

---

## Phase 7: Testing

### Task 7.1: Set Up pytest Configuration
**Difficulty:** Junior-friendly
**Estimated Complexity:** Simple

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=vibe_coder --cov-report=term-missing --cov-report=html"
asyncio_mode = "auto"
```

---

### Task 7.2: Write Configuration Tests
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `tests/test_config/test_manager.py`

```python
import pytest
from pathlib import Path
import tempfile
import shutil

from vibe_coder.config.manager import ConfigManager
from vibe_coder.types.config import AIProvider

@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def config_manager(temp_config_dir):
    """Create ConfigManager with temp directory."""
    return ConfigManager(config_dir=temp_config_dir)

def test_create_default_config(config_manager):
    """Test default configuration creation."""
    assert config_manager.config_file.exists()

def test_set_and_get_provider(config_manager):
    """Test setting and getting a provider."""
    provider = AIProvider(
        name="test-provider",
        api_key="test-key-123456",
        endpoint="https://api.test.com/v1",
        model="test-model",
    )

    config_manager.set_provider("test", provider)
    retrieved = config_manager.get_provider("test")

    assert retrieved is not None
    assert retrieved.name == "test-provider"
    assert retrieved.api_key == "test-key-123456"
    assert retrieved.endpoint == "https://api.test.com/v1"

def test_list_providers(config_manager):
    """Test listing providers."""
    provider1 = AIProvider(
        name="provider1",
        api_key="key1-1234567890",
        endpoint="https://api.test1.com/v1"
    )
    provider2 = AIProvider(
        name="provider2",
        api_key="key2-1234567890",
        endpoint="https://api.test2.com/v1"
    )

    config_manager.set_provider("p1", provider1)
    config_manager.set_provider("p2", provider2)

    providers = config_manager.list_providers()
    assert len(providers) == 2
    assert "p1" in providers
    assert "p2" in providers

def test_delete_provider(config_manager):
    """Test deleting a provider."""
    provider = AIProvider(
        name="test",
        api_key="test-key-123456",
        endpoint="https://api.test.com/v1"
    )

    config_manager.set_provider("test", provider)
    assert "test" in config_manager.list_providers()

    config_manager.delete_provider("test")
    assert "test" not in config_manager.list_providers()

def test_current_provider(config_manager):
    """Test setting and getting current provider."""
    provider = AIProvider(
        name="current",
        api_key="key-1234567890",
        endpoint="https://api.test.com/v1"
    )

    config_manager.set_provider("current", provider)
    config_manager.set_current_provider("current")

    current = config_manager.get_current_provider()
    assert current is not None
    assert current.name == "current"
```

---

## Summary

This Python implementation plan mirrors the TypeScript plan but leverages Python's strengths:

### Key Python Advantages:
1. **Rich & Typer** - Better CLI experience than Commander.js
2. **Built-in AST** - No need for @babel/parser
3. **Official SDKs** - Direct OpenAI and Anthropic libraries
4. **Async/Await** - Native async support with asyncio
5. **Type Hints** - Optional but recommended (like TypeScript)
6. **Poetry** - Modern packaging (better than old setup.py)

### Installation:
```bash
# As a user
pip install vibe-coder
# or
pipx install vibe-coder

# For development
poetry install
```

### Development Workflow:
```bash
# Format code
make format

# Run linter
make lint

# Run tests
make test

# Run with coverage
make test-cov
```

### Next Steps:
1. Continue with remaining phases (Slash Commands, Provider Independence)
2. Create Python-specific ROADMAP
3. Create Python-specific QUICK_START_GUIDE
4. Begin implementation

The total task count remains the same (~75 tasks), but some tasks are simpler in Python due to better library support.