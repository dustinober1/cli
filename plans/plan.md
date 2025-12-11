# Vibe Coder CLI - 100% Test Coverage Implementation Plan

## Executive Summary

**Current State:** 19% coverage (9,688 statements, 7,803 untested), 327 tests passing
**Target State:** 100% coverage, 100% tests passing, all bugs fixed
**Strategy:** Parallel development + real API integration + immediate bug fixes
**Estimated Timeline:** 8-12 weeks with parallel team development
**Estimated Deliverables:** 58+ new test files, ~980+ new test functions

---

## User Requirements (Confirmed)

✅ **100% Test Coverage** - Every statement must be tested
✅ **100% Tests Passing** - All tests must pass
✅ **Code Fixes First** - If tests fail due to bugs, fix code immediately (not tests)
✅ **Real API Testing** - Include integration tests with actual OpenAI/Anthropic APIs
✅ **Comprehensive Integration** - E2E workflows, component integration, MCP, performance
✅ **Parallel Development** - Designed for team-based simultaneous development

---

## Testing Philosophy

### Three-Tier Testing Strategy

1. **Unit Tests (Mocked)** - Fast, isolated, no external dependencies
   - Mock all external APIs (OpenAI, Anthropic)
   - Mock file system operations (use `tmp_path`)
   - Mock subprocess calls (git, pytest, linters)
   - Run in CI/CD pipeline
   - **Target: 95%+ of all tests**

2. **Integration Tests (Real APIs)** - Slower, requires credentials
   - Real OpenAI API calls (requires `OPENAI_API_KEY`)
   - Real Anthropic API calls (requires `ANTHROPIC_API_KEY`)
   - Marked with `@pytest.mark.integration`
   - Skipped by default (`pytest` runs mocks only)
   - Run with `pytest -m integration` or `make test-integration`
   - **Target: 5% of tests, high confidence**

3. **End-to-End Tests** - Complete workflows
   - Full user journeys (setup → chat → code generation)
   - Component integration (repo mapper + AI client)
   - MCP tool execution
   - Performance benchmarks
   - **Target: 20-30 comprehensive scenarios**

---

## Parallel Development Workflow

### Team Organization (3-5 Developers)

**Developer 1: Foundation - API Clients & Core**
- Week 1-2: API client testing (OpenAI, Anthropic, Generic)
- Week 3-4: Integration tests with real APIs
- Week 5-6: MCP integration testing

**Developer 2: Intelligence & Healing**
- Week 1-3: Intelligence system (repo mapper, context, AST)
- Week 4-5: Healing system (auto-healer, validators)
- Week 6-7: Utilities (security scanner, templates, snippets)

**Developer 3: CLI Commands**
- Week 1-2: Main CLI commands (chat, setup, config, test)
- Week 3-5: Core slash commands (code, debug, fix, git)
- Week 6-8: Advanced slash commands

**Developer 4: Integration & Performance**
- Week 1-4: Wait for foundation components
- Week 5-8: End-to-end workflows
- Week 9-10: Component integration tests
- Week 11-12: Performance benchmarks

**Developer 5: Quality & Coverage**
- Week 1-8: Code reviews, coverage monitoring
- Week 9-10: Fill coverage gaps across all modules
- Week 11-12: Final verification, documentation

### Coordination Requirements

**Daily Sync:**
- Share coverage reports
- Identify blocked dependencies
- Coordinate on shared fixtures

**Weekly Reviews:**
- Run full test suite (`make test`)
- Review combined coverage report
- Identify gaps and reassign as needed

**Shared Resources:**
- `tests/conftest.py` - Central fixture library (version controlled)
- `.env.test` - Shared test environment variables
- Coverage dashboard - Track progress

---

## Phase 1: Foundation Layer (Weeks 1-3)

### 1.1 API Client Testing (Developer 1, Week 1-2)

**Coverage Gap:** 13-17% → Target: 100%
**Files:** 4 test files, ~95 test functions

#### Test Files to Create:
```
tests/test_api/
├── test_base.py (15 tests)
├── test_openai_client.py (30 tests: 25 mocked + 5 integration)
├── test_anthropic_client.py (30 tests: 25 mocked + 5 integration)
└── test_generic_client.py (30 tests: all mocked)
```

#### Testing Approach

**Unit Tests (Mocked) - 85 tests**

Mock Strategy:
- `unittest.mock.AsyncMock` for SDK clients
- Pre-defined responses for various scenarios
- Error injection for failure testing

Key Test Categories:
1. Client initialization (valid/invalid configs)
2. Request/response handling (success cases)
3. Streaming responses (chunk aggregation)
4. Tool calling (MCP integration)
5. Error handling (rate limits, auth, network)
6. Connection validation

**Integration Tests (Real APIs) - 10 tests**

Setup:
```python
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
async def test_real_openai_request():
    """Test real OpenAI API request."""
    provider = AIProvider(
        name="openai-test",
        api_key=os.getenv("OPENAI_API_KEY"),
        endpoint="https://api.openai.com/v1",
        model="gpt-3.5-turbo",
    )
    client = OpenAIClient(provider)

    messages = [
        ApiMessage(role=MessageRole.USER, content="Say 'test passed'")
    ]

    response = await client.send_request(messages, max_tokens=10)

    assert response.content is not None
    assert len(response.content) > 0
    assert response.usage.total_tokens > 0
```

Integration Test Categories:
1. Real OpenAI request (GPT-3.5-turbo, cheap)
2. Real OpenAI streaming
3. Real Anthropic request (Claude-3-haiku, cheap)
4. Real Anthropic streaming
5. Real tool calling (if applicable)

**Cost Mitigation:**
- Use cheapest models (gpt-3.5-turbo, claude-3-haiku)
- Set `max_tokens=10` for minimal responses
- Estimated cost: $0.10-0.50 per full test run

#### Critical Files
- `/Users/dustinober/Projects/cli/vibe_coder/api/openai_client.py`
- `/Users/dustinober/Projects/cli/vibe_coder/api/anthropic_client.py`
- `/Users/dustinober/Projects/cli/vibe_coder/api/generic_client.py`
- `/Users/dustinober/Projects/cli/vibe_coder/api/base.py`

---

### 1.2 Intelligence System Testing (Developer 2, Weeks 1-3)

**Coverage Gap:** 10-23% → Target: 100%
**Files:** 6 test files, ~120 test functions

#### Test Files to Create:
```
tests/test_intelligence/
├── test_repo_mapper.py (25 tests)
├── test_code_context.py (20 tests)
├── test_file_monitor.py (15 tests)
├── test_importance_scorer.py (20 tests)
├── test_reference_resolver.py (25 tests)
└── test_token_budgeter.py (15 tests)
```

#### Testing Approach

**File System Testing:**
- Use `tmp_path` fixture with real file structures
- Create sample Python projects for realistic testing
- Test AST analysis on actual .py files

**Sample Repository Fixture:**
```python
@pytest.fixture
def sample_repo_structure(tmp_path):
    """Create a realistic Python project."""
    # Create src/
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text("""
from .utils import helper

def main():
    '''Main entry point.'''
    return helper()

class Application:
    def run(self):
        return main()
""")
    (src / "utils.py").write_text("""
def helper():
    '''Helper function.'''
    return "Hello"

def unused():
    pass
""")

    # Create tests/
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("""
from src.main import main

def test_main():
    assert main() == "Hello"
""")

    return tmp_path
```

**Key Test Categories:**
1. Repository scanning (small, medium, large repos)
2. AST analysis (functions, classes, imports)
3. Dependency graph construction
4. Context building for different operations
5. Token budgeting and prioritization
6. File monitoring and change detection
7. Performance with large codebases

#### Critical Files
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/repo_mapper.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/code_context.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/ast_analyzer.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/file_monitor.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/importance_scorer.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/reference_resolver.py`
- `/Users/dustinober/Projects/cli/vibe_coder/intelligence/token_budgeter.py`

---

### 1.3 Healing System Testing (Developer 2, Week 3)

**Coverage Gap:** 10-14% → Target: 100%
**Files:** 2 test files, ~40 test functions

#### Test Files to Create:
```
tests/test_healing/
├── test_auto_healer.py (25 tests)
└── test_validators.py (25 tests)
```

#### Testing Approach

**Subprocess Mocking:**
```python
@pytest.fixture
def mock_pytest_run_success(monkeypatch):
    """Mock successful pytest run."""
    from subprocess import CompletedProcess

    def mock_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="100% passing\n5 passed",
            stderr=""
        )

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run

@pytest.fixture
def mock_pytest_run_failure(monkeypatch):
    """Mock failed pytest run."""
    from subprocess import CompletedProcess

    def mock_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="FAILED tests/test_main.py::test_foo - AssertionError"
        )

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run
```

**Key Test Categories:**
1. Syntax validation (AST parsing)
2. Import validation
3. Test execution (pytest, unittest)
4. Type checking (mypy)
5. Code formatting (black, isort)
6. Auto-healing strategies
7. Retry logic and max attempts

#### Critical Files
- `/Users/dustinober/Projects/cli/vibe_coder/healing/auto_healer.py`
- `/Users/dustinober/Projects/cli/vibe_coder/healing/validators.py`

---

### 1.4 Utilities Testing (Developer 2, Week 3)

**Coverage Gap:** 0% → Target: 100%
**Files:** 3 test files, ~60 test functions

#### Test Files to Create:
```
tests/test_utils/
├── test_security_scanner.py (20 tests)
├── test_snippet_manager.py (20 tests)
└── test_template_engine.py (20 tests)
```

#### Critical Files
- `/Users/dustinober/Projects/cli/vibe_coder/utils/security_scanner.py`
- `/Users/dustinober/Projects/cli/vibe_coder/utils/snippet_manager.py`
- `/Users/dustinober/Projects/cli/vibe_coder/utils/template_engine.py`

---

## Phase 2: Command Layer (Weeks 4-8)

### 2.1 Main CLI Commands (Developer 3, Weeks 1-2)

**Coverage Gap:** 0% → Target: 100%
**Files:** 5 test files, ~80 test functions

#### Test Files to Create:
```
tests/test_cli/
└── test_main.py (20 tests)

tests/test_commands/
├── test_chat.py (30 tests: 25 mocked + 5 integration)
├── test_setup.py (15 tests)
├── test_config_cmd.py (10 tests)
└── test_test_cmd.py (15 tests)
```

#### Testing Approach - CLI Entry Point

**Use Typer's Testing Tools:**
```python
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    """Typer CLI test runner."""
    return CliRunner()

def test_chat_command_basic(cli_runner, monkeypatch):
    """Test basic chat command invocation."""
    # Mock the ChatCommand.run() method
    from vibe_coder import cli

    async def mock_run(self):
        self.console.print("Chat started")
        return True

    monkeypatch.setattr("vibe_coder.commands.chat.ChatCommand.run", mock_run)

    result = cli_runner.invoke(cli.app, ["chat"])

    assert result.exit_code == 0
    assert "Chat started" in result.stdout
```

#### Testing Approach - Chat Command

**Questionary Mocking:**
```python
@pytest.fixture
def mock_questionary(monkeypatch):
    """Mock questionary for interactive prompts."""
    from unittest.mock import AsyncMock, MagicMock

    responses = {}

    def set_response(key, value):
        responses[key] = value

    def mock_text(message, **kwargs):
        mock = MagicMock()
        async def ask_async():
            return responses.get(message, "default")
        mock.ask_async = ask_async
        return mock

    monkeypatch.setattr("questionary.text", mock_text)

    return set_response
```

**Integration Tests (Real AI):**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_real_ai_interaction():
    """Test chat with real AI provider."""
    # Requires OPENAI_API_KEY in environment
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    chat = ChatCommand()
    await chat.initialize(provider_name="openai-test")

    # Send a simple message
    response = await chat.send_message("Say 'test passed' and nothing else")

    assert "test" in response.lower()
    assert chat.messages  # History should be populated
```

**Key Test Categories:**
1. Chat initialization and provider selection
2. Message sending and receiving (mocked AI)
3. Slash command integration
4. Chat history management
5. Save/export conversation
6. Context injection (repository intelligence)
7. MCP tool execution
8. Streaming display
9. Error handling and recovery

#### Critical Files
- `/Users/dustinober/Projects/cli/vibe_coder/cli.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/chat.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/setup.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/config.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/test.py`

---

### 2.2 Slash Commands - Core (Developer 3, Weeks 3-5)

**Coverage Gap:** 0% → Target: 100%
**Files:** 13 test files, ~260 test functions

#### Test Files to Create:
```
tests/test_commands/test_slash_commands/
├── test_cmd_code.py (20 tests)
├── test_cmd_debug.py (15 tests)
├── test_cmd_fix.py (20 tests)
├── test_cmd_git.py (20 tests)
├── test_cmd_project.py (20 tests)
├── test_cmd_repo.py (20 tests)
├── test_cmd_system.py (25 tests)
├── test_cmd_test.py (20 tests)
├── test_cmd_model.py (10 tests)
├── test_cmd_provider.py (10 tests)
├── test_cmd_mcp.py (15 tests)
├── test_cmd_docs.py (20 tests)
└── test_slash_base.py (10 tests) - if not already tested
```

#### Testing Approach - Slash Commands

**Command Context Fixture:**
```python
@pytest.fixture
def command_context(tmp_path, mock_provider, mock_ai_client):
    """Create a realistic command context."""
    from vibe_coder.commands.slash.base import CommandContext

    # Create git repository
    repo = Repo.init(tmp_path)
    (tmp_path / "README.md").write_text("# Test")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return CommandContext(
        chat_history=[],
        current_provider=mock_provider,
        client=mock_ai_client,
        working_directory=str(tmp_path),
        git_info={
            "branch": "main",
            "commit": "abc123",
            "status": "clean",
            "remote": "origin",
        },
        repo_mapper=None,  # Optional: add mock repo mapper
        mcp_manager=None,  # Optional: add mock MCP manager
    )
```

**Example Test Structure:**
```python
class TestCodeCommand:
    """Tests for /code command."""

    @pytest.fixture
    def code_command(self):
        from vibe_coder.commands.slash.commands.code import CodeCommand
        return CodeCommand()

    async def test_generate_function(self, code_command, command_context):
        """Test generating a simple function."""
        result = await code_command.execute(
            ["Create a hello world function"],
            command_context
        )

        assert "def" in result or "function" in result
        assert result  # Should have content

    async def test_generate_with_file_spec(self, code_command, command_context, tmp_path):
        """Test code generation with file specification."""
        target_file = tmp_path / "new_module.py"

        result = await code_command.execute(
            [f"Create a calculator in {target_file}"],
            command_context
        )

        # Verify file was created (if command creates files)
        # OR verify output contains file path
        assert str(target_file) in result or target_file.exists()

    async def test_invalid_args(self, code_command, command_context):
        """Test command with invalid arguments."""
        with pytest.raises(ValueError, match="requires.*prompt"):
            await code_command.execute([], command_context)
```

**Git Operations Testing:**
```python
@pytest.fixture
def git_repository(tmp_path):
    """Create a temporary git repository."""
    repo = Repo.init(tmp_path)

    # Initial commit
    (tmp_path / "README.md").write_text("# Test Repo")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Add some changes
    (tmp_path / "file.py").write_text("print('hello')")

    return tmp_path

async def test_git_status_command(git_command, command_context, git_repository):
    """Test /git status command."""
    result = await git_command.execute(["status"], command_context)

    assert "file.py" in result  # Untracked file should appear
    assert "untracked" in result.lower() or "new file" in result.lower()
```

#### Critical Files (24 slash command modules)
- `/Users/dustinober/Projects/cli/vibe_coder/commands/slash/commands/*.py` (24 files)
- `/Users/dustinober/Projects/cli/vibe_coder/commands/slash/base.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/slash/registry.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/slash/git_ops.py`
- `/Users/dustinober/Projects/cli/vibe_coder/commands/slash/project_analyzer.py`

---

### 2.3 Slash Commands - Advanced (Developer 3, Weeks 6-8)

**Coverage Gap:** 0% → Target: 100%
**Files:** 11 test files, ~210 test functions

Similar approach to 2.2, covering remaining slash command modules.

---

## Phase 3: Integration Layer (Weeks 5-10)

### 3.1 Component Integration Tests (Developer 4, Weeks 5-7)

**Files:** 3 test files, ~30 test functions

#### Test Files to Create:
```
tests/test_integration/
├── test_repo_intelligence_integration.py (10 tests)
├── test_mcp_integration.py (10 tests)
└── test_plugin_lifecycle.py (10 tests)
```

#### Testing Approach

**Repository Intelligence Integration:**
```python
@pytest.mark.asyncio
async def test_context_injection_in_chat():
    """Test that repository context is automatically injected."""
    # Setup: Real Python project
    repo_path = create_sample_project(tmp_path)

    # Initialize components
    repo_mapper = RepositoryMapper(repo_path)
    await repo_mapper.scan_repository()

    context_provider = CodeContextProvider(repo_mapper)

    # Create chat command with intelligence
    chat = ChatCommand()
    chat.repo_mapper = repo_mapper
    chat.context_provider = context_provider

    # Mock AI client
    chat.client = mock_ai_client

    # Ask question about codebase
    response = await chat.send_message("What does the main.py file do?")

    # Verify context was injected
    # (Check that AI received context about main.py)
    assert mock_ai_client.last_request_contained("main.py")
```

**MCP Integration:**
```python
@pytest.mark.asyncio
async def test_mcp_tool_execution_in_chat():
    """Test MCP tool execution during chat."""
    # Requires MCP server running (or mocked)
    chat = ChatCommand()
    await chat.initialize_mcp()

    # Mock AI to request tool
    mock_ai_response_with_tool_call = {
        "tool_calls": [
            {
                "name": "read_file",
                "arguments": {"path": "README.md"}
            }
        ]
    }

    # Execute
    result = await chat.handle_tool_calls(mock_ai_response_with_tool_call)

    # Verify tool was executed
    assert "README" in result or result  # Tool returned something
```

---

### 3.2 End-to-End Workflow Tests (Developer 4, Weeks 8-10)

**Files:** 5 test files, ~40 test functions

#### Test Files to Create:
```
tests/test_integration/
├── test_setup_to_chat_flow.py (8 tests)
├── test_code_generation_flow.py (10 tests)
├── test_git_workflow.py (10 tests)
├── test_debugging_flow.py (8 tests)
└── test_project_analysis_flow.py (8 tests)
```

#### Testing Approach

**Complete User Journey:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_new_user_setup_to_code_generation():
    """Test complete flow: setup → chat → code generation → file creation."""

    # Step 1: Setup (interactive wizard)
    setup_cmd = SetupCommand()

    # Mock questionary responses
    with mock_questionary() as mq:
        mq.set("Provider type:", "OpenAI")
        mq.set("API Key:", os.getenv("OPENAI_API_KEY"))
        mq.set("Endpoint:", "https://api.openai.com/v1")
        mq.set("Model:", "gpt-3.5-turbo")

        await setup_cmd.run()

    # Verify configuration was saved
    config = config_manager.load_config()
    assert "openai-test" in config.providers

    # Step 2: Start chat
    chat_cmd = ChatCommand()
    await chat_cmd.initialize()

    # Step 3: Generate code
    response = await chat_cmd.send_message(
        "/code Create a fibonacci function in fib.py"
    )

    # Step 4: Verify file was created
    assert Path("fib.py").exists()
    content = Path("fib.py").read_text()
    assert "def fibonacci" in content or "def fib" in content

    # Step 5: Verify chat history
    assert len(chat_cmd.messages) > 0
```

**Git Workflow:**
```python
@pytest.mark.asyncio
async def test_git_workflow_commit_generation():
    """Test: make changes → /git status → /git commit → verify commit."""

    # Setup git repo
    repo_path = tmp_path / "project"
    repo = Repo.init(repo_path)

    # Initial commit
    (repo_path / "README.md").write_text("# Project")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Make changes
    (repo_path / "new_feature.py").write_text("""
def new_feature():
    return "New feature"
""")

    # Initialize chat in repo
    os.chdir(repo_path)
    chat = ChatCommand()
    await chat.initialize()

    # Step 1: Check status
    status_response = await chat.send_message("/git status")
    assert "new_feature.py" in status_response

    # Step 2: Generate commit message
    commit_response = await chat.send_message(
        "/git commit 'Add new feature function'"
    )

    # Step 3: Verify commit was made
    assert len(list(repo.iter_commits())) == 2
    latest_commit = next(repo.iter_commits())
    assert "new feature" in latest_commit.message.lower()
```

---

### 3.3 Performance Tests (Developer 4, Weeks 11-12)

**Files:** 2 test files, ~20 test functions

#### Test Files to Create:
```
tests/test_performance/
├── test_repository_scan_performance.py (10 tests)
└── test_context_building_performance.py (10 tests)
```

#### Testing Approach

**Large Repository Performance:**
```python
@pytest.mark.performance
def test_scan_large_repository(benchmark, large_repo_fixture):
    """Benchmark repository scanning on large codebase."""

    # large_repo_fixture creates 1000+ Python files
    repo_mapper = RepositoryMapper(large_repo_fixture)

    # Benchmark scanning
    result = benchmark(repo_mapper.scan_repository)

    # Assertions
    assert result["files_scanned"] > 1000

    # Performance targets
    assert benchmark.stats.stats.mean < 5.0  # < 5 seconds average
```

**Context Building Performance:**
```python
@pytest.mark.performance
def test_context_building_with_large_history(benchmark):
    """Test context building performance with large chat history."""

    context_provider = CodeContextProvider(repo_mapper)

    # Create large chat history (100 messages)
    large_history = [
        ApiMessage(role=MessageRole.USER, content=f"Message {i}")
        for i in range(100)
    ]

    # Benchmark context building
    def build():
        return context_provider.build_context(
            operation_type=OperationType.GENERATE,
            chat_history=large_history,
        )

    result = benchmark(build)

    # Should complete in reasonable time
    assert benchmark.stats.stats.mean < 1.0  # < 1 second
```

---

## Phase 4: Coverage Completion & Verification (Weeks 9-12)

### 4.1 Fill Remaining Gaps (Developer 5, Weeks 9-10)

**Process:**

1. **Run Coverage Report:**
   ```bash
   poetry run pytest --cov=vibe_coder --cov-report=html --cov-report=term-missing
   ```

2. **Identify Gaps:**
   - Open `htmlcov/index.html`
   - Sort by "% covered" ascending
   - Identify modules < 100%

3. **Create Targeted Tests:**
   - For each untested line, write a test that exercises it
   - Focus on:
     - Exception branches
     - Edge case conditionals
     - Cleanup code (finally blocks)
     - Error paths
     - Rare conditions

4. **Example Gap Fixing:**
   ```python
   # If coverage shows line 42 is untested:
   # vibe_coder/module.py:42

   def test_edge_case_that_triggers_line_42():
       """Test the specific condition that executes line 42."""
       # Setup to trigger that specific branch
       ...
       # Assert expected behavior
       ...
   ```

---

### 4.2 Final Verification (Developer 5, Week 12)

**Verification Checklist:**

- [ ] **Run Full Test Suite**
  ```bash
  make test
  ```

- [ ] **Run Integration Tests**
  ```bash
  pytest -m integration
  ```

- [ ] **Generate Coverage Report**
  ```bash
  make test-cov
  ```

- [ ] **Verify 100% Coverage**
  - Check coverage report shows 100% (or 99%+ with documented exceptions)
  - No module below 100%
  - No intentionally untested code without justification

- [ ] **Code Quality**
  ```bash
  make format  # Black + isort
  make lint    # Flake8 + mypy
  ```

- [ ] **Documentation**
  - Update CLAUDE.md with new test coverage stats
  - Document test organization
  - Add testing guidelines for contributors
  - Update README.md with testing instructions

- [ ] **Performance Baselines**
  - Run performance tests
  - Document baseline metrics
  - Set CI/CD performance regression thresholds

---

## Testing Infrastructure

### Central Fixture Library (`tests/conftest.py`)

This file must be created and will contain **all shared fixtures** for the entire test suite.

**Create:** `/Users/dustinober/Projects/cli/tests/conftest.py`

**Key Sections:**
1. Async fixtures (event loop, asyncio configuration)
2. File system fixtures (tmp_path extensions, sample projects)
3. Git repository fixtures
4. AI provider and client mocking
5. Command context fixtures
6. Questionary mocking
7. Subprocess mocking
8. MCP mocking
9. Repository intelligence mocking

**Example Structure:**
```python
"""Global test fixtures for Vibe Coder test suite."""

import asyncio
import os
from pathlib import Path
from typing import AsyncIterator, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from git import Repo

from vibe_coder.types.config import AIProvider
from vibe_coder.types.api import ApiMessage, ApiResponse, MessageRole, TokenUsage

# ========================================
# Async Configuration
# ========================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ========================================
# File System Fixtures
# ========================================

@pytest.fixture
def sample_python_project(tmp_path):
    """Create a sample Python project structure."""
    # ... (implementation from plan)
    pass

@pytest.fixture
def git_repository(tmp_path):
    """Create a temporary git repository."""
    # ... (implementation from plan)
    pass

# ========================================
# AI Mocking
# ========================================

@pytest.fixture
def mock_provider():
    """Create a mock AI provider."""
    return AIProvider(
        name="test-provider",
        api_key="sk-test-key-123456789",
        endpoint="https://api.test.com/v1",
        model="test-model",
        temperature=0.7,
        max_tokens=2000,
    )

@pytest.fixture
def mock_ai_client(mock_provider):
    """Create a mocked AI client."""
    client = AsyncMock()
    client.provider = mock_provider

    async def mock_send_request(messages, **kwargs):
        return ApiResponse(
            content="Mocked AI response",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            finish_reason="stop",
        )

    async def mock_stream_request(messages, **kwargs):
        for chunk in ["Mocked ", "streaming ", "response"]:
            yield chunk

    client.send_request = mock_send_request
    client.stream_request = mock_stream_request

    return client

# ========================================
# Command Context Fixtures
# ========================================

@pytest.fixture
def command_context(tmp_path, mock_provider, mock_ai_client):
    """Create a command context for testing slash commands."""
    from vibe_coder.commands.slash.base import CommandContext

    # Setup git repo
    repo = Repo.init(tmp_path)
    (tmp_path / "README.md").write_text("# Test")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return CommandContext(
        chat_history=[],
        current_provider=mock_provider,
        client=mock_ai_client,
        working_directory=str(tmp_path),
        git_info={
            "branch": "main",
            "commit": "abc123",
            "status": "clean",
            "remote": "origin",
        },
    )

# ========================================
# Questionary Mocking
# ========================================

@pytest.fixture
def mock_questionary(monkeypatch):
    """Mock questionary for interactive prompts."""
    responses = {}

    def set_response(key, value):
        responses[key] = value

    def mock_text(message, **kwargs):
        mock = MagicMock()
        async def ask_async():
            return responses.get(message, "default")
        mock.ask_async = ask_async
        return mock

    def mock_select(message, choices, **kwargs):
        mock = MagicMock()
        async def ask_async():
            return responses.get(message, choices[0])
        mock.ask_async = ask_async
        return mock

    monkeypatch.setattr("questionary.text", mock_text)
    monkeypatch.setattr("questionary.select", mock_select)

    return set_response

# ========================================
# Subprocess Mocking
# ========================================

@pytest.fixture
def mock_subprocess_success(monkeypatch):
    """Mock successful subprocess execution."""
    from subprocess import CompletedProcess

    def mock_run(*args, **kwargs):
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="Success",
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", mock_run)

# ... (more fixtures)
```

---

### Test Environment Configuration

**Create:** `/Users/dustinober/Projects/cli/.env.test`

```bash
# Test environment configuration
# Used for integration tests with real APIs

# OpenAI (required for integration tests)
OPENAI_API_KEY=sk-...

# Anthropic (required for integration tests)
ANTHROPIC_API_KEY=sk-ant-...

# Test configuration
VIBE_CODER_TEST_MODE=true
VIBE_CODER_TEST_MAX_TOKENS=10  # Keep costs low
```

**Update:** `/Users/dustinober/Projects/cli/.gitignore`

```
# Test files
.env.test
htmlcov/
.coverage
.pytest_cache/
```

---

### Test Organization Structure

```
tests/
├── __init__.py
├── conftest.py                          # ✅ CREATE - Central fixture library
│
├── test_api/                            # ✅ EXPAND
│   ├── __init__.py
│   ├── test_factory.py                 # ✅ Exists
│   ├── test_base.py                    # ❌ CREATE
│   ├── test_openai_client.py          # ❌ CREATE
│   ├── test_anthropic_client.py       # ❌ CREATE
│   └── test_generic_client.py         # ❌ CREATE
│
├── test_analytics/                      # ✅ MINIMAL GAPS
│   ├── test_pricing.py                 # ❌ CREATE (fill gaps)
│   └── test_cost_tracker.py           # ❌ CREATE (fill gaps)
│
├── test_cli/                            # ❌ CREATE NEW
│   └── test_main.py
│
├── test_commands/                       # ✅ EXPAND HEAVILY
│   ├── test_chat.py                    # ❌ CREATE
│   ├── test_setup.py                   # ❌ CREATE
│   ├── test_config_cmd.py             # ❌ CREATE
│   ├── test_test_cmd.py               # ❌ CREATE
│   ├── test_git_ops.py                 # ❌ CREATE
│   ├── test_project_analyzer.py       # ❌ CREATE
│   │
│   └── test_slash_commands/            # ❌ CREATE NEW (24 files)
│       ├── test_cmd_code.py
│       ├── test_cmd_debug.py
│       ├── test_cmd_fix.py
│       ├── test_cmd_git.py
│       └── ... (20+ more files)
│
├── test_config/                         # ✅ WELL TESTED (minor gaps)
│
├── test_healing/                        # ✅ EXPAND
│   ├── test_auto_healer.py            # ❌ CREATE
│   └── test_validators.py            # ❌ CREATE
│
├── test_intelligence/                   # ✅ EXPAND HEAVILY
│   ├── test_repo_mapper.py            # ❌ CREATE
│   ├── test_code_context.py          # ❌ CREATE
│   ├── test_file_monitor.py          # ❌ CREATE
│   ├── test_importance_scorer.py     # ❌ CREATE
│   ├── test_reference_resolver.py    # ❌ CREATE
│   └── test_token_budgeter.py        # ❌ CREATE
│
├── test_integration/                    # ❌ CREATE NEW (7 files)
│   ├── test_setup_to_chat_flow.py
│   ├── test_code_generation_flow.py
│   ├── test_git_workflow.py
│   ├── test_debugging_flow.py
│   ├── test_project_analysis_flow.py
│   ├── test_mcp_integration.py
│   └── test_plugin_lifecycle.py
│
├── test_mcp/                            # ❌ CREATE NEW
│   └── test_manager.py
│
├── test_performance/                    # ❌ CREATE NEW
│   ├── test_repository_scan_performance.py
│   └── test_context_building_performance.py
│
├── test_plugins/                        # ✅ MINIMAL GAPS
│   └── test_manager.py                 # ❌ CREATE (fill gaps)
│
└── test_utils/                          # ❌ CREATE NEW
    ├── test_security_scanner.py
    ├── test_snippet_manager.py
    └── test_template_engine.py
```

---

## Bug Fix Workflow

### When a Test Reveals a Bug

**Immediate Action Protocol:**

1. **Stop and Document**
   ```python
   @pytest.mark.xfail(reason="Bug #<issue_number>: <description>")
   def test_that_fails_due_to_bug():
       """
       This test reveals a bug in production code.

       Expected: X
       Actual: Y

       Root cause: ...
       """
       # Test code that fails
       assert expected == actual
   ```

2. **Create GitHub Issue**
   - Title: `[Bug] <Short description>`
   - Body: Include:
     - Test file and function name
     - Expected vs actual behavior
     - Steps to reproduce
     - Proposed fix (if known)

3. **Fix the Code (NOT the Test)**
   - Fix the bug in production code
   - Verify the test now passes
   - Remove `@pytest.mark.xfail`

4. **Add Regression Test**
   - Ensure the test covers the edge case
   - May add additional tests for similar scenarios

5. **Verify No Regressions**
   ```bash
   make test  # Run full suite
   make lint  # Check code quality
   ```

6. **Commit Fix**
   ```bash
   git add .
   git commit -m "fix: <description> (fixes #<issue_number>)"
   ```

**Do NOT:**
- ❌ Change tests to match buggy behavior
- ❌ Skip tests without documenting why
- ❌ Leave `@pytest.mark.xfail` without a linked issue

---

## Real API Integration Testing

### Setup Requirements

**Environment Variables:**
```bash
# Add to .env.test (not committed)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**pytest Configuration:**

**Update:** `/Users/dustinober/Projects/cli/pytest.ini`

```ini
[pytest]
markers =
    integration: marks tests that require real API calls (deselect with '-m "not integration"')
    performance: marks performance/benchmark tests
    slow: marks tests as slow (deselect with '-m "not slow"')

# Default: Run unit tests only (skip integration)
addopts = -m "not integration"

# Coverage configuration
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Makefile Commands:**

**Update:** `/Users/dustinober/Projects/cli/Makefile`

```makefile
# Add new test targets

.PHONY: test-integration
test-integration: ## Run integration tests (requires API keys)
	poetry run pytest -m integration -v

.PHONY: test-all
test-all: ## Run all tests including integration
	poetry run pytest -v

.PHONY: test-performance
test-performance: ## Run performance benchmarks
	poetry run pytest -m performance -v --benchmark-only

.PHONY: test-unit
test-unit: ## Run unit tests only (default)
	poetry run pytest -m "not integration and not performance" -v
```

### Cost Management

**Integration Test Cost Estimates:**

| Test Category | Model | Tests | Cost per Run | Monthly (30 runs) |
|---------------|-------|-------|--------------|-------------------|
| OpenAI Basic | GPT-3.5-turbo | 5 | $0.05 | $1.50 |
| OpenAI Streaming | GPT-3.5-turbo | 3 | $0.03 | $0.90 |
| Anthropic Basic | Claude-3-haiku | 5 | $0.10 | $3.00 |
| Anthropic Streaming | Claude-3-haiku | 3 | $0.06 | $1.80 |
| **TOTAL** | - | **16** | **$0.24** | **$7.20** |

**Mitigation Strategies:**
- Use cheapest models (gpt-3.5-turbo, claude-3-haiku)
- Set `max_tokens=10` for minimal responses
- Run integration tests manually, not on every commit
- Use CI/CD env variable to skip integration in PR checks
- Run integration tests on main branch merges only

---

## Makefile Updates

**Update:** `/Users/dustinober/Projects/cli/Makefile`

```makefile
.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: ## Install dependencies
	poetry install

.PHONY: test
test: ## Run unit tests (default - fast, no API calls)
	poetry run pytest -m "not integration and not performance" -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	poetry run pytest -m "not integration and not performance" --cov=vibe_coder --cov-report=term-missing --cov-report=html

.PHONY: test-integration
test-integration: ## Run integration tests (requires API keys)
	@echo "⚠️  Integration tests will use real APIs and incur costs (~$0.24 per run)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		poetry run pytest -m integration -v; \
	fi

.PHONY: test-all
test-all: ## Run all tests (unit + integration)
	poetry run pytest -v

.PHONY: test-performance
test-performance: ## Run performance benchmarks
	poetry run pytest -m performance -v

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	poetry run pytest-watch -m "not integration and not performance"

.PHONY: format
format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

.PHONY: lint
lint: ## Lint code with flake8 and mypy
	poetry run flake8 vibe_coder tests
	poetry run mypy vibe_coder

.PHONY: clean
clean: ## Clean build artifacts
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: run
run: ## Run the CLI
	poetry run vibe-coder
```

---

## Success Criteria

**The project achieves 100% test coverage when:**

✅ **Coverage Metrics:**
- `make test-cov` reports 100% overall coverage (or 99%+ with documented exceptions)
- Every module shows 100% coverage
- `htmlcov/index.html` shows no red (untested) lines

✅ **Test Quality:**
- All 1,300+ tests pass consistently
- No `@pytest.mark.skip` without justification
- No `@pytest.mark.xfail` without linked GitHub issues
- Tests follow naming conventions and best practices

✅ **Integration Testing:**
- End-to-end workflows pass (setup → chat → code generation)
- Component integration verified (repo mapper + AI client)
- MCP integration working
- Performance benchmarks established

✅ **Code Quality:**
- `make format` passes (black + isort)
- `make lint` passes (flake8 + mypy)
- No linting errors
- No type errors

✅ **Documentation:**
- CLAUDE.md updated with test coverage stats
- Testing guidelines documented
- Contributors know how to run tests
- README.md has testing section

✅ **Real API Validation:**
- Integration tests with OpenAI pass
- Integration tests with Anthropic pass
- Optional: Real MCP server integration tests

---

## Estimated Metrics

### Test File Summary

| Phase | New Files | Approx. Tests | Developer | Weeks |
|-------|-----------|---------------|-----------|-------|
| **Phase 1: Foundation** | 15 | 315 | Dev 1-2 | 1-3 |
| API Clients | 4 | 95 | Dev 1 | 1-2 |
| Intelligence | 6 | 120 | Dev 2 | 1-3 |
| Healing | 2 | 40 | Dev 2 | 3 |
| Utilities | 3 | 60 | Dev 2 | 3 |
| **Phase 2: Commands** | 30 | 550 | Dev 3 | 1-8 |
| Main CLI | 5 | 80 | Dev 3 | 1-2 |
| Slash Core | 13 | 260 | Dev 3 | 3-5 |
| Slash Advanced | 11 | 210 | Dev 3 | 6-8 |
| **Phase 3: Integration** | 10 | 100 | Dev 4 | 5-10 |
| Component Integration | 3 | 30 | Dev 4 | 5-7 |
| E2E Workflows | 5 | 50 | Dev 4 | 8-10 |
| Performance | 2 | 20 | Dev 4 | 11-12 |
| **Phase 4: Polish** | 3 | 35 | Dev 5 | 9-12 |
| MCP | 1 | 20 | Dev 5 | 9 |
| Coverage Gaps | Variable | Variable | Dev 5 | 9-11 |
| Verification | - | - | Dev 5 | 12 |
| **TOTAL** | **58 files** | **~1,000 tests** | **5 devs** | **12 weeks** |

### Current vs Target

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| Test Files | 20 | 78 | +58 |
| Test Functions | 327 | ~1,327 | +1,000 |
| Coverage | 19% | 100% | +81% |
| Tested Statements | 1,885 | 9,688 | +7,803 |
| Integration Tests | 0 | 16 | +16 |

---

## Critical Files to Create/Modify

### Must Create (Priority Order):

1. **`/Users/dustinober/Projects/cli/tests/conftest.py`** (500+ lines)
   - Central fixture library
   - All mocking utilities
   - Shared test data

2. **`/Users/dustinober/Projects/cli/.env.test`**
   - API keys for integration tests
   - Test configuration

3. **`/Users/dustinober/Projects/cli/tests/test_api/test_openai_client.py`**
   - OpenAI client unit tests
   - OpenAI integration tests
   - Foundation for AI testing

4. **`/Users/dustinober/Projects/cli/tests/test_api/test_anthropic_client.py`**
   - Anthropic client unit tests
   - Anthropic integration tests

5. **`/Users/dustinober/Projects/cli/tests/test_commands/test_chat.py`**
   - Chat command comprehensive testing
   - Most complex user-facing feature

### Must Modify:

1. **`/Users/dustinober/Projects/cli/pytest.ini`**
   - Add integration test markers
   - Configure default test behavior

2. **`/Users/dustinober/Projects/cli/Makefile`**
   - Add test-integration target
   - Add test-performance target
   - Add test-all target

3. **`/Users/dustinober/Projects/cli/.gitignore`**
   - Ignore .env.test
   - Ignore coverage artifacts

---

## Timeline & Milestones

### Week 1-2: Foundation - API Layer
- ✅ Create conftest.py
- ✅ Test OpenAI client (mocked + integration)
- ✅ Test Anthropic client (mocked + integration)
- ✅ Test Generic client
- **Milestone:** API clients at 100% coverage

### Week 3-4: Foundation - Intelligence
- ✅ Test repository mapper
- ✅ Test code context provider
- ✅ Test AST analyzer
- ✅ Test file monitor
- **Milestone:** Intelligence system at 100% coverage

### Week 5-6: CLI Commands
- ✅ Test main CLI entry point
- ✅ Test chat command
- ✅ Test setup/config/test commands
- **Milestone:** Core CLI at 100% coverage

### Week 7-8: Slash Commands
- ✅ Test core slash commands (code, debug, git, etc.)
- ✅ Test advanced slash commands
- **Milestone:** All slash commands at 100% coverage

### Week 9-10: Integration
- ✅ E2E workflow tests
- ✅ Component integration tests
- ✅ MCP integration tests
- **Milestone:** Integration layer complete

### Week 11-12: Final Push
- ✅ Fill remaining coverage gaps
- ✅ Performance benchmarks
- ✅ Final verification
- ✅ Documentation updates
- **Milestone:** 100% coverage achieved ✅

---

## This Plan Delivers

✅ **100% Test Coverage** - Every statement tested
✅ **100% Tests Passing** - All tests pass
✅ **Real API Confidence** - Integration tests with OpenAI/Anthropic
✅ **Parallel Development** - 5 developers working simultaneously
✅ **Bug Fixes First** - Immediate code fixes when tests fail
✅ **Comprehensive Integration** - E2E, component, MCP, performance
✅ **Production Ready** - High-quality, maintainable test suite

**Ready for execution. Let's achieve 100% coverage! 🚀**
