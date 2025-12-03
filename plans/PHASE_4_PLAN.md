# Phase 4: Interactive Prompts - Detailed Plan

## Status: 🔄 PENDING (Next Phase)

## Overview

Phase 4 will build on the configuration system (Phase 2) and API integration (Phase 3) to create the interactive user interface. This phase focuses on the setup wizard and basic chat functionality that makes Vibe Coder usable as a CLI tool.

**Duration:** Week 4 of development (Days 20-24)
**Deliverable:** Interactive setup wizard and basic chat interface ⏳

---

## Phase 4: Interactive Prompts

### Goal
Build an interactive user interface that allows users to:
- Configure AI providers through a friendly setup wizard
- Have basic conversations with AI models
- Experience smooth terminal-based interaction

### Architecture

```
Interactive Interface Flow:
┌─────────────────────────────────────────┐
│  User runs: vibe-coder setup            │
│  First-time user experience             │
└────────┬───────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Setup Wizard (Questionary)             │
│  - Provider selection                  │
│  - API key collection                  │
│  - Model configuration                 │
│  - Connection testing                  │
└────────┬───────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Configuration Persistence              │
│  (Phase 2 ConfigManager)               │
└────────┬───────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  User runs: vibe-coder chat             │
│  Interactive chat session               │
└────────┬───────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Chat Interface                         │
│  - Rich terminal output                 │
│  - Message history                     │
│  - Streaming responses                 │
│  - Error handling                      │
└─────────────────────────────────────────┘
```

---

## Task Breakdown

### Task 4.1: Create Setup Wizard

**File:** `vibe_coder/commands/setup.py`
**Difficulty:** Medium
**Time Estimate:** 6-8 hours

#### What We're Building:
A comprehensive setup wizard using Questionary that guides users through configuring their first AI provider.

#### Implementation Steps:

1. **Create SetupCommand class** (lines 1-50)
   - Use Questionary for interactive prompts
   - Implement step-by-step wizard flow
   - Add validation at each step
   - Handle user cancellation gracefully

2. **Provider Selection** (lines 51-100)
   - Present list of supported providers
   - Show provider descriptions
   - Handle custom endpoint option
   - Pre-select common choices

3. **API Configuration** (lines 101-150)
   - Secure API key collection (password masking)
   - Endpoint URL input with validation
   - Model selection with defaults
   - Temperature and token limits

4. **Connection Testing** (lines 151-200)
   - Test API connectivity using Phase 3 clients
   - Show progress indicators
   - Display success/failure with helpful messages
   - Retry mechanism for failed connections

5. **Save Configuration** (lines 201-250)
   - Save to ConfigManager from Phase 2
   - Set as current provider
   - Show confirmation with Rich formatting
   - Provide next steps guidance

#### Code Structure:
```python
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from vibe_coder.api.factory import ClientFactory
from vibe_coder.config.manager import config_manager
from vibe_coder.types.config import AIProvider

class SetupCommand:
    """Interactive setup wizard for Vibe Coder."""

    def __init__(self):
        self.console = Console()

    async def run(self):
        """Run the complete setup wizard."""
        self.console.print("[bold green]🚀 Welcome to Vibe Coder Setup![/bold green]")
        self.console.print("Let's configure your first AI provider.\n")

        # Step 1: Provider selection
        provider_type = await self._select_provider_type()

        # Step 2: Provider configuration
        provider_config = await self._configure_provider(provider_type)

        # Step 3: Connection testing
        await self._test_connection(provider_config)

        # Step 4: Save configuration
        await self._save_configuration(provider_config)

        # Step 5: Success and next steps
        self._show_success_message()

    async def _select_provider_type(self) -> str:
        """Let user select provider type."""
        providers = [
            {
                "name": "OpenAI",
                "description": "GPT models (GPT-4, GPT-3.5)",
                "value": "openai"
            },
            {
                "name": "Anthropic",
                "description": "Claude models (Claude-3.5 Sonnet, Haiku)",
                "value": "anthropic"
            },
            {
                "name": "Local/Ollama",
                "description": "Local models via Ollama",
                "value": "ollama"
            },
            {
                "name": "Custom Endpoint",
                "description": "Any OpenAI-compatible API",
                "value": "custom"
            }
        ]

        choice = await questionary.select(
            "Which AI provider would you like to configure?",
            choices=providers
        ).ask_async()

        return choice
```

#### Acceptance Criteria:
- ✅ Interactive wizard flows smoothly
- ✅ All providers supported (OpenAI, Anthropic, Generic)
- ✅ Real-time connection testing
- ✅ Secure API key handling
- ✅ Rich terminal output with progress indicators
- ✅ Error handling with helpful messages

---

### Task 4.2: Create Basic Chat Interface

**File:** `vibe_coder/commands/chat.py`
**Difficulty:** Medium
**Time Estimate:** 8-10 hours

#### What We're Building:
A basic interactive chat interface that connects to configured AI providers and handles streaming responses.

#### Implementation Steps:

1. **Create ChatCommand class** (lines 1-50)
   - Initialize Rich console for formatted output
   - Load current provider from ConfigManager
   - Handle provider selection and overrides
   - Setup message history tracking

2. **Chat Loop Implementation** (lines 51-150)
   - Interactive input loop with prompts
   - Message history management
   - Handle special commands (/help, /exit, /clear)
   - Graceful error handling and recovery

3. **API Integration** (lines 151-200)
   - Use Phase 3 ClientFactory to create clients
   - Send messages with proper formatting
   - Handle streaming responses
   - Display responses with Rich formatting

4. **User Experience** (lines 201-250)
   - Typing indicators during responses
   - Error messages in context
   - Session statistics (tokens, response time)
   - Exit confirmation with save option

#### Code Structure:
```python
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
import questionary

from vibe_coder.api.factory import ClientFactory
from vibe_coder.config.manager import config_manager
from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, MessageRole

class ChatCommand:
    """Interactive chat interface for Vibe Coder."""

    def __init__(self):
        self.console = Console()
        self.messages = []
        self.client = None

    async def run(self, provider_name: str = None, model: str = None):
        """Run the interactive chat session."""
        # Setup provider
        await self._setup_provider(provider_name, model)

        # Welcome message
        self._show_welcome()

        # Chat loop
        await self._chat_loop()

    async def _setup_provider(self, provider_name: str, model: str):
        """Setup the AI provider and client."""
        if provider_name:
            provider = config_manager.get_provider(provider_name)
            if not provider:
                self.console.print(f"[red]Provider '{provider_name}' not found.[/red]")
                return
        else:
            provider = config_manager.get_current_provider()
            if not provider:
                self.console.print("[red]No provider configured. Run 'vibe-coder setup' first.[/red]")
                return

        # Override model if specified
        if model:
            provider.model = model

        # Create client
        self.client = ClientFactory.create_client(provider)
        self.provider = provider

    async def _chat_loop(self):
        """Main chat interaction loop."""
        while True:
            try:
                # Get user input
                user_input = await questionary.text(
                    "You:",
                    multiline=True,
                    validate=lambda x: len(x.strip()) > 0 or "Please enter a message"
                ).ask_async()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    if await self._handle_command(user_input):
                        continue
                    else:
                        break

                # Add user message
                user_message = ApiMessage(role=MessageRole.USER, content=user_input)
                self.messages.append(user_message)

                # Get AI response
                await self._get_ai_response()

            except KeyboardInterrupt:
                if await questionary.confirm("Exit chat?").ask_async():
                    break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

    async def _get_ai_response(self):
        """Get and display AI response."""
        try:
            # Show typing indicator
            with self.console.status("[bold green]Thinking...[/bold green]"):
                # Get streaming response
                response_chunks = []
                async for chunk in self.client.stream_request(self.messages):
                    response_chunks.append(chunk)

            # Join chunks and add to history
            ai_response = "".join(response_chunks)
            ai_message = ApiMessage(role=MessageRole.ASSISTANT, content=ai_response)
            self.messages.append(ai_message)

            # Display response
            self._display_ai_response(ai_response)

        except Exception as e:
            self.console.print(f"[red]Error getting response: {e}[/red]")

    def _display_ai_response(self, response: str):
        """Display AI response with nice formatting."""
        panel = Panel(
            Markdown(response),
            title=f"[bold blue]{self.provider.name}[/bold blue]",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()  # Add spacing
```

#### Acceptance Criteria:
- ✅ Interactive chat loop works smoothly
- ✅ Streaming responses displayed in real-time
- ✅ Rich formatting for messages
- ✅ Message history maintained
- ✅ Basic slash commands (/help, /exit, /clear)
- ✅ Error handling with user-friendly messages
- ✅ Provider and model overrides work

---

### Task 4.3: Create Config Command

**File:** `vibe_coder/commands/config.py`
**Difficulty:** Easy-Medium
**Time Estimate:** 4-5 hours

#### What We're Building:
A configuration management command that allows users to list, show, add, edit, and delete AI provider configurations.

#### Implementation Steps:

1. **Create ConfigCommand class** (lines 1-50)
   - Use Typer subcommands for different operations
   - Integrate with Phase 2 ConfigManager
   - Add Rich formatting for output

2. **List Providers** (lines 51-100)
   - Show all configured providers
   - Mark current provider
   - Display key information in table format

3. **Show Provider Details** (lines 101-150)
   - Display complete provider configuration
   - Hide sensitive information (API keys)
   - Show connection status

4. **Add/Edit/Delete Providers** (lines 151-250)
   - Interactive prompts for adding providers
   - Safe editing with validation
   - Confirmation before deletion
   - Error handling for edge cases

#### Code Structure:
```python
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import questionary

from vibe_coder.config.manager import config_manager
from vibe_coder.commands.setup import SetupCommand

app = typer.Typer(help="Manage AI provider configurations")
console = Console()

@app.command()
def list():
    """List all configured providers."""
    providers = config_manager.list_providers()
    current = config_manager.get_current_provider_name()

    if not providers:
        console.print("[yellow]No providers configured. Use 'vibe-coder setup' to add one.[/yellow]")
        return

    table = Table(title="Configured AI Providers")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Model", style="magenta")
    table.add_column("Endpoint", style="green")
    table.add_column("Current", style="yellow")

    for provider_name in providers:
        provider = config_manager.get_provider(provider_name)
        current_marker = "✓" if provider_name == current else ""
        table.add_row(
            provider_name,
            provider.model or "default",
            provider.endpoint,
            current_marker
        )

    console.print(table)

@app.command()
def show(name: str):
    """Show detailed information about a provider."""
    provider = config_manager.get_provider(name)
    if not provider:
        console.print(f"[red]Provider '{name}' not found.[/red]")
        return

    # Hide API key for security
    safe_config = {
        "name": provider.name,
        "endpoint": provider.endpoint,
        "model": provider.model,
        "temperature": provider.temperature,
        "max_tokens": provider.max_tokens,
        "api_key": f"{provider.api_key[:8]}..." if provider.api_key else None
    }

    config_text = "\n".join([f"{k}: {v}" for k, v in safe_config.items() if v is not None])

    panel = Panel(
        config_text,
        title=f"Provider: {name}",
        border_style="blue"
    )
    console.print(panel)
```

#### Acceptance Criteria:
- ✅ All CRUD operations for providers
- ✅ Secure display of sensitive information
- ✅ Rich table formatting for lists
- ✅ Interactive prompts for operations
- ✅ Integration with setup wizard

---

### Task 4.4: Create Test Command

**File:** `vibe_coder/commands/test.py`
**Difficulty:** Easy
**Time Estimate:** 2-3 hours

#### What We're Building:
A command to test AI provider connections and display status information.

#### Implementation Steps:

1. **Create TestCommand class** (lines 1-50)
   - Test single or all providers
   - Show connection status
   - Display latency and response time
   - Format results with Rich

#### Acceptance Criteria:
- ✅ Connection testing for all providers
- ✅ Detailed status reporting
- ✅ Performance metrics
- ✅ Error diagnosis

---

## Testing Strategy for Phase 4

### Test Files to Create:

1. **tests/test_commands/test_setup.py** (lines 1-100)
   - Test setup wizard flow
   - Mock user inputs
   - Test connection validation
   - Test error handling

2. **tests/test_commands/test_chat.py** (lines 1-100)
   - Test chat loop functionality
   - Mock AI responses
   - Test command handling
   - Test message history

3. **tests/test_commands/test_config.py** (lines 1-80)
   - Test config command operations
   - Test provider CRUD operations
   - Test Rich formatting

4. **Integration Tests** (lines 1-50)
   - Test full setup workflow
   - Test chat with real/mock providers
   - Test CLI integration

### Mocking Strategy:
- Use pytest-asyncio for async tests
- Mock questionary prompts for consistent testing
- Mock API responses for reliable tests
- Integration tests with real endpoints (optional)

---

## Development Workflow

### Step-by-Step:

**Day 1 (Task 4.1 Part 1):**
1. Create SetupCommand structure
2. Implement provider selection
3. Add Questionary integration
4. Test basic wizard flow

**Day 2 (Task 4.1 Part 2):**
1. Complete setup wizard
2. Add connection testing
3. Save configuration properly
4. Test error handling

**Day 3 (Task 4.2):**
1. Create basic chat interface
2. Implement chat loop
3. Add streaming responses
4. Test with mock providers

**Day 4 (Task 4.3 & 4.4):**
1. Create config command
2. Create test command
3. Add Rich formatting
4. Test all functionality

**Day 5 (Testing & Polish):**
1. Write comprehensive tests
2. Fix any issues found
3. Update documentation
4. Final testing and review

### Commands to Run Daily:

```bash
# Format code
make format

# Check for issues
make lint

# Run tests
make test

# Run with coverage
make test-cov

# Test CLI manually
poetry run vibe-coder --help
```

---

## Integration Points

### How Phase 4 Connects to Previous Phases:

**Phase 4 → Phase 2 (Configuration System):**
- Setup wizard uses ConfigManager to save provider settings
- Config command uses ConfigManager for all operations
- Validation from Phase 2 ensures data integrity

**Phase 4 → Phase 3 (API Integration):**
- Chat interface uses ClientFactory to create API clients
- Setup wizard tests connections using Phase 3 clients
- Error handling from Phase 3 propagated to user

**Phase 4 → CLI (commands/cli.py):**
- Commands integrated into main CLI interface
- Help system updated with new functionality
- Error handling consistent across commands

### Data Flow Example:
```
User runs: vibe-coder setup
    ↓
SetupCommand wizard collects provider info
    ↓
ConfigManager.save_provider() (Phase 2)
    ↓
ClientFactory.create_client() for testing (Phase 3)
    ↓
Connection validation and save confirmation
    ↓
User runs: vibe-coder chat
    ↓
ChatCommand loads current provider from ConfigManager
    ↓
ClientFactory.create_client() creates API client (Phase 3)
    ↓
Interactive chat with streaming responses
```

---

## File Structure After Phase 4

```
vibe_coder/
├── commands/
│   ├── __init__.py
│   ├── setup.py            # NEW: Setup wizard
│   ├── chat.py             # NEW: Chat interface
│   ├── config.py           # NEW: Config management
│   └── test.py             # NEW: Connection testing
├── api/                    # ✅ From Phase 3
├── config/                 # ✅ From Phase 2
├── types/                  # ✅ From Phase 2
├── prompts/                # Phase 5+
├── utils/                  # Phase 6+
└── cli.py                  # ✅ Updated with new commands

tests/
├── test_config/            # ✅ From Phase 2
├── test_api/               # ✅ From Phase 3
└── test_commands/          # NEW: Command tests
    ├── test_setup.py
    ├── test_chat.py
    ├── test_config.py
    └── test_integration.py
```

---

## Success Criteria for Phase 4

By end of this phase:
- ✅ Interactive setup wizard working smoothly
- ✅ Basic chat interface with streaming responses
- ✅ Config command for provider management
- ✅ Test command for connection validation
- ✅ Rich terminal formatting throughout
- ✅ Error handling with user-friendly messages
- ✅ Integration with Phase 2 and Phase 3 systems
- ✅ All tests passing (>70% coverage)
- ✅ Code formatted and linted
- ✅ Documentation updated

---

## User Experience Goals

### First-Time User Flow:
1. `git clone && poetry install`
2. `poetry run vibe-coder setup` - Guided wizard
3. `poetry run vibe-coder chat` - Start chatting
4. `poetry run vibe-coder config list` - Manage providers

### Power User Features:
- Multiple provider support
- Runtime provider/model switching
- Configuration backup and restore
- Connection performance monitoring

---

Phase 4 will transform Vibe Coder from a framework into a usable CLI tool that real users can interact with immediately. By building on the solid foundations of Phase 2 (Configuration) and Phase 3 (API Integration), this phase delivers the core user experience.

Let's build Phase 4! 💬✨