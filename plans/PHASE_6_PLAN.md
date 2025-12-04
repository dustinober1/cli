# Phase 6: Utilities & Advanced Features Implementation Plan

**Status:** 📋 Planning Phase
**Start Date:** January 2025
**Estimated Duration:** 4-5 weeks
**Complexity Level:** High - Advanced patterns and system integration

---

## 🎯 Phase Overview

Phase 6 transforms Vibe Coder into a production-grade development assistant by adding intelligent repository mapping, auto-healing capabilities, comprehensive cost tracking, and an extensible plugin system. This phase focuses on power-user features that differentiate Vibe Coder from basic AI chat interfaces.

**Core Focus Areas:**
1. **AST-Based Repository Intelligence** - Deep codebase understanding
2. **Auto-Healing Engine** - Automatic code validation and fixing
3. **Cost & Token Tracking** - Budget awareness and analytics
4. **Plugin Architecture** - Community extensibility
5. **Performance Optimization** - Speed and memory efficiency

---

## 📊 Success Metrics

### Functional Metrics
- **AST Coverage:** Support for Python, JavaScript/TypeScript, and Go
- **Auto-Healing:** 95%+ success rate for common errors
- **Token Counting:** Within 5% accuracy of actual token usage
- **Plugin System:** Support for custom commands and integrations
- **Performance:** Code generation responses in <3 seconds

### Quality Metrics
- **Test Coverage:** 90%+ for all new code
- **Code Quality:** Zero linting errors, full type safety
- **Documentation:** Complete API docs and plugin guide
- **Backwards Compatibility:** All Phase 5 features remain unchanged

---

## 🏗️ Architecture Design

### 1. Repository Mapping System (AST + Dependency Analysis)

#### Core Components

```python
# vibe_coder/intelligence/repo_mapper.py
from pathlib import Path
from typing import Dict, List, Set, Optional
import ast
from dataclasses import dataclass

@dataclass
class FunctionSignature:
    """Function metadata extracted via AST."""
    name: str
    module_path: str
    file_path: str
    line_start: int
    line_end: int
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int  # Cyclomatic complexity

@dataclass
class FileNode:
    """File-level metadata."""
    path: str
    language: str
    lines_of_code: int
    functions: List[FunctionSignature]
    classes: List['ClassSignature']
    imports: List[str]
    dependencies: Set[str]
    type_hints_coverage: float  # Percentage with type hints

@dataclass
class RepositoryMap:
    """Complete codebase structure."""
    root_path: str
    total_files: int
    total_lines: int
    languages: Dict[str, int]  # Language -> file count
    modules: Dict[str, FileNode]
    dependency_graph: Dict[str, Set[str]]
    entry_points: List[str]
    test_files: List[str]
    generated_at: str

class PythonASTAnalyzer:
    """Analyze Python files using AST."""

    async def analyze_file(self, file_path: str) -> FileNode:
        """Extract metadata from Python file."""
        # Parse AST and extract:
        # - Function signatures
        # - Class definitions
        # - Type hints
        # - Imports
        # - Docstrings
        # - Complexity metrics

    def extract_functions(self, tree: ast.Module) -> List[FunctionSignature]:
        """Walk AST and extract function metadata."""

    def extract_classes(self, tree: ast.Module) -> List[ClassSignature]:
        """Walk AST and extract class metadata."""

    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""

class JavaScriptASTAnalyzer:
    """Analyze JavaScript/TypeScript using tree-sitter."""

    async def analyze_file(self, file_path: str) -> FileNode:
        """Extract metadata from JS/TS file."""
        # Use tree-sitter for parsing
        # Extract:
        # - Function declarations
        # - Class definitions
        # - Type annotations (TypeScript)
        # - Module exports
        # - Dependencies

class RepositoryMapper:
    """High-level repository analysis orchestrator."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.python_analyzer = PythonASTAnalyzer()
        self.js_analyzer = JavaScriptASTAnalyzer()
        self.cache: Dict[str, FileNode] = {}

    async def scan_repository(self) -> RepositoryMap:
        """Complete repository scan with caching."""
        # 1. Identify all files
        # 2. Detect languages
        # 3. Parse each file in parallel
        # 4. Build dependency graph
        # 5. Return compressed representation

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Create import/dependency relationships."""
        # Analyze imports to find:
        # - Internal module dependencies
        # - External library usage
        # - Circular dependencies

    def compress_representation(self, repo_map: RepositoryMap) -> str:
        """Create AI-friendly compressed representation."""
        # Output format similar to:
        # ```
        # PROJECT: vibe-coder
        # STRUCTURE:
        # - src/
        #   - api/
        #     - base.py (206 lines, 5 functions)
        #       - send_request(messages) -> ApiResponse
        #       - validate_connection() -> bool
        #       - stream_request(messages) -> AsyncIterator
        #     - openai_client.py (244 lines, 1 class)
        #       - class OpenAIClient(BaseApiClient)
        #
        # DEPENDENCIES:
        # - Internal: api/base -> types/api
        # - External: openai, httpx, anthropic
        #
        # ENTRY_POINTS:
        # - cli.py: ChatCommand, SetupCommand, ConfigCommand
        # ```

    async def update_on_file_change(self, file_path: str):
        """Incrementally update cache on file changes."""

    def get_context_for_file(self, file_path: str, context_size: int = 8000) -> str:
        """Get relevant context for code generation."""
        # Returns related files and functions
        # within token budget

class CodeContextProvider:
    """Provide relevant code context for AI operations."""

    async def get_context(
        self,
        operation: str,  # "generate", "fix", "refactor"
        target_file: str,
        token_budget: int = 8000
    ) -> str:
        """Get minimal sufficient context for operation."""
        # 1. Identify target file's dependencies
        # 2. Load related implementations
        # 3. Include relevant patterns
        # 4. Stay within token budget
        # 5. Prioritize by relevance
```

#### Features

- **Multi-Language Support:**
  - Python (AST-based)
  - JavaScript/TypeScript (tree-sitter)
  - Go (tree-sitter)
  - Extensible for more languages

- **Intelligent Context:**
  - Dependency analysis
  - Entry point detection
  - Test file identification
  - Unused code detection

- **Performance:**
  - Async file processing
  - Smart caching
  - Incremental updates
  - Compressed representations

---

### 2. Auto-Healing Engine

#### Core Components

```python
# vibe_coder/healing/auto_healer.py
from typing import Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass

class ValidationStrategy(Enum):
    """Types of validation to run."""
    SYNTAX = "syntax"       # Check for syntax errors
    TYPE_CHECK = "typecheck"  # Run mypy/tsc
    LINT = "lint"           # Run linting
    TESTS = "tests"         # Run test suite
    BUILD = "build"         # Try to build/compile
    CUSTOM = "custom"       # User-defined validator

@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    strategy: ValidationStrategy
    execution_time: float

@dataclass
class HealingAttempt:
    """Record of healing attempt."""
    attempt_number: int
    original_code: str
    fixed_code: str
    validation_result: ValidationResult
    ai_prompt: str
    timestamp: str

class CodeValidator:
    """Run various validations on code."""

    async def validate_syntax(self, code: str, language: str) -> ValidationResult:
        """Check if code has syntax errors."""
        # Use language-specific parsers

    async def validate_types(self, file_path: str) -> ValidationResult:
        """Run type checker (mypy for Python, tsc for TypeScript)."""

    async def validate_linting(self, file_path: str) -> ValidationResult:
        """Run linter and report issues."""

    async def validate_tests(self, file_path: str) -> ValidationResult:
        """Run tests for this file/module."""

    async def validate_build(self, project_root: str) -> ValidationResult:
        """Attempt to build project."""

    async def validate_custom(self, script: str, code: str) -> ValidationResult:
        """Run user-defined validation script."""

class AutoHealer:
    """Automatically fix code issues."""

    def __init__(
        self,
        api_client,
        validator: CodeValidator,
        max_attempts: int = 3,
        timeout: int = 60
    ):
        self.api_client = api_client
        self.validator = validator
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.healing_history: List[HealingAttempt] = []

    async def heal_code(
        self,
        code: str,
        language: str,
        context: str = "",
        validation_strategies: List[ValidationStrategy] = None
    ) -> Tuple[str, bool, List[HealingAttempt]]:
        """
        Attempt to fix broken code.

        Returns:
            - healed_code: The fixed code
            - success: Whether healing succeeded
            - history: All healing attempts for debugging
        """
        if validation_strategies is None:
            validation_strategies = [ValidationStrategy.SYNTAX]

        attempts: List[HealingAttempt] = []
        current_code = code

        for attempt_num in range(1, self.max_attempts + 1):
            # Validate current code
            validation_results = []
            for strategy in validation_strategies:
                result = await self._run_validation(strategy, current_code)
                validation_results.append(result)

            # Check if all validations passed
            if all(r.is_valid for r in validation_results):
                return current_code, True, attempts

            # Collect errors
            all_errors = []
            for result in validation_results:
                all_errors.extend(result.errors)

            # Ask AI to fix
            fixed_code = await self._ask_ai_to_fix(
                current_code,
                language,
                all_errors,
                context,
                attempt_num
            )

            # Record attempt
            attempt = HealingAttempt(
                attempt_number=attempt_num,
                original_code=current_code,
                fixed_code=fixed_code,
                validation_result=validation_results[0],
                ai_prompt=f"Fix errors: {all_errors}",
                timestamp=datetime.now().isoformat()
            )
            attempts.append(attempt)

            current_code = fixed_code

        # Max attempts exceeded
        return current_code, False, attempts

    async def _run_validation(
        self,
        strategy: ValidationStrategy,
        code: str
    ) -> ValidationResult:
        """Run specific validation strategy."""
        if strategy == ValidationStrategy.SYNTAX:
            return await self.validator.validate_syntax(code, "python")
        elif strategy == ValidationStrategy.TYPE_CHECK:
            return await self.validator.validate_types("temp_file.py")
        # ... other strategies

    async def _ask_ai_to_fix(
        self,
        code: str,
        language: str,
        errors: List[str],
        context: str,
        attempt_num: int
    ) -> str:
        """Use AI to fix code."""
        error_description = "\n".join(f"- {e}" for e in errors)

        prompt = f"""Fix the following {language} code.

ERRORS TO FIX:
{error_description}

ORIGINAL CODE:
```{language}
{code}
```

{f'CONTEXT:{context}' if context else ''}

{'PREVIOUS ATTEMPTS FAILED - Be creative with the fix.' if attempt_num > 1 else ''}

Return ONLY the fixed code, no explanations."""

        response = await self.api_client.send_request([
            {"role": "system", "content": f"You are an expert {language} developer fixing code errors."},
            {"role": "user", "content": prompt}
        ])

        return self._extract_code_from_response(response.content)

class HealingConfig:
    """Configuration for auto-healing."""

    max_attempts: int = 3
    strategies: List[ValidationStrategy] = [
        ValidationStrategy.SYNTAX,
        ValidationStrategy.TYPE_CHECK
    ]
    require_user_confirmation: bool = True
    save_before_healing: bool = True
    timeout_seconds: int = 60
```

#### Features

- **Multi-Strategy Validation:**
  - Syntax checking
  - Type checking (mypy, tsc)
  - Linting (flake8, eslint)
  - Unit tests
  - Build compilation

- **Intelligent Retry Logic:**
  - Progressive fixing attempts
  - Context awareness
  - Error analysis
  - Attempt history tracking

- **Safety:**
  - Backup before changes
  - User confirmation required
  - Audit trail of changes
  - Rollback capability

---

### 3. Cost Tracking & Token Counting

#### Core Components

```python
# vibe_coder/analytics/cost_tracker.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json

class ModelTier(Enum):
    """Pricing tier for models."""
    CHEAP = "cheap"      # gpt-3.5, local models
    STANDARD = "standard"  # gpt-4, claude-3-sonnet
    EXPENSIVE = "expensive"  # gpt-4-turbo, claude-3-opus

@dataclass
class TokenPricing:
    """Token pricing for a model."""
    model_name: str
    input_price_per_1k: float  # Price per 1000 tokens
    output_price_per_1k: float
    tier: ModelTier

@dataclass
class RequestMetrics:
    """Metrics for a single API request."""
    timestamp: datetime
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    operation: str  # "chat", "code_generation", etc.
    completion_time: float  # seconds

class TokenCounter:
    """Estimate token usage before API calls."""

    # Model-specific token limits and estimation factors
    TOKEN_ESTIMATION_FACTORS = {
        "gpt-3.5-turbo": {"chars_per_token": 4.0, "overhead": 1.1},
        "gpt-4": {"chars_per_token": 4.0, "overhead": 1.1},
        "claude-3-sonnet": {"chars_per_token": 3.5, "overhead": 1.15},
        "claude-3-opus": {"chars_per_token": 3.5, "overhead": 1.15},
    }

    async def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count for text.

        Uses:
        1. tiktoken library for OpenAI models (exact)
        2. Anthropic token counter for Claude (exact)
        3. Estimation formula for unknown models
        """
        if "gpt" in model.lower():
            return self._count_openai_tokens(text, model)
        elif "claude" in model.lower():
            return self._count_anthropic_tokens(text, model)
        else:
            return self._estimate_tokens(text, model)

    def _count_openai_tokens(self, text: str, model: str) -> int:
        """Use tiktoken for exact OpenAI token count."""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            return self._estimate_tokens(text, model)

    def _count_anthropic_tokens(self, text: str, model: str) -> int:
        """Use Anthropic SDK for token counting."""
        try:
            from anthropic import Anthropic
            client = Anthropic()
            response = client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}]
            )
            return response.input_tokens
        except:
            return self._estimate_tokens(text, model)

    def _estimate_tokens(self, text: str, model: str) -> int:
        """Estimate tokens using formula."""
        factors = self.TOKEN_ESTIMATION_FACTORS.get(
            model,
            {"chars_per_token": 4.0, "overhead": 1.1}
        )
        base_tokens = len(text) / factors["chars_per_token"]
        return int(base_tokens * factors["overhead"])

    async def estimate_request_cost(
        self,
        prompt: str,
        model: str,
        estimated_output_tokens: int = 500
    ) -> Tuple[int, int, float]:
        """
        Estimate cost before making request.

        Returns:
            - input_tokens: Estimated input tokens
            - output_tokens: Estimated output tokens
            - cost_usd: Estimated cost in USD
        """
        input_tokens = await self.count_tokens(prompt, model)

        pricing = PRICING_DB.get(model)
        if not pricing:
            return input_tokens, estimated_output_tokens, 0.0

        input_cost = (input_tokens / 1000) * pricing.input_price_per_1k
        output_cost = (estimated_output_tokens / 1000) * pricing.output_price_per_1k

        return input_tokens, estimated_output_tokens, input_cost + output_cost

class CostTracker:
    """Track API usage and costs."""

    def __init__(self, storage_path: str = "~/.vibe/analytics.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.metrics: List[RequestMetrics] = []
        self.budget_limit: Optional[float] = None
        self.load_history()

    def set_budget(self, amount_usd: float, period: str = "monthly"):
        """Set spending budget."""
        self.budget_limit = amount_usd
        self.budget_period = period

    def record_request(self, metrics: RequestMetrics):
        """Record API request metrics."""
        self.metrics.append(metrics)
        self.save_history()

        # Check budget
        if self.budget_limit:
            current_spent = self.get_current_period_cost()
            if current_spent > self.budget_limit:
                logger.warning(
                    f"Budget exceeded! "
                    f"Spent ${current_spent:.2f} of ${self.budget_limit:.2f}"
                )

    def get_current_period_cost(self) -> float:
        """Get spending for current period."""
        now = datetime.now()
        period_start = self._get_period_start(now)

        return sum(
            m.total_cost for m in self.metrics
            if m.timestamp >= period_start
        )

    def get_statistics(self) -> Dict:
        """Get comprehensive usage statistics."""
        return {
            "total_requests": len(self.metrics),
            "total_cost": sum(m.total_cost for m in self.metrics),
            "total_tokens": sum(m.total_tokens for m in self.metrics),
            "by_model": self._stats_by_model(),
            "by_provider": self._stats_by_provider(),
            "by_operation": self._stats_by_operation(),
            "daily_average": self._daily_average(),
            "projected_monthly": self._project_monthly(),
            "most_expensive_request": self._most_expensive(),
        }

    def save_history(self):
        """Persist metrics to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "metrics": [asdict(m) for m in self.metrics],
            "budget_limit": self.budget_limit,
            "saved_at": datetime.now().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_history(self):
        """Load metrics from disk."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                data = json.load(f)
                self.metrics = [
                    RequestMetrics(**m) for m in data.get("metrics", [])
                ]
                self.budget_limit = data.get("budget_limit")

class CostDisplay:
    """Format cost information for display."""

    @staticmethod
    def format_cost(amount_usd: float) -> str:
        """Format cost as string."""
        return f"${amount_usd:.4f}"

    @staticmethod
    def get_cost_emoji(cost: float) -> str:
        """Return emoji based on cost level."""
        if cost < 0.01:
            return "🟢"  # Cheap
        elif cost < 0.10:
            return "🟡"  # Moderate
        else:
            return "🔴"  # Expensive

    @staticmethod
    def render_budget_gauge(spent: float, limit: float) -> str:
        """Render visual budget gauge."""
        percent = (spent / limit) * 100
        filled = int(percent / 5)  # 20 chars wide
        empty = 20 - filled

        color = "green" if percent < 80 else "yellow" if percent < 95 else "red"

        return f"[{color}]{'█' * filled}{'░' * empty}[/{color}] {percent:.0f}%"
```

#### Pricing Database

```python
# vibe_coder/analytics/pricing.py
PRICING_DB = {
    # OpenAI models
    "gpt-3.5-turbo": TokenPricing(
        model_name="gpt-3.5-turbo",
        input_price_per_1k=0.0005,
        output_price_per_1k=0.0015,
        tier=ModelTier.CHEAP
    ),
    "gpt-4": TokenPricing(
        model_name="gpt-4",
        input_price_per_1k=0.03,
        output_price_per_1k=0.06,
        tier=ModelTier.EXPENSIVE
    ),
    # Anthropic models
    "claude-3-sonnet": TokenPricing(
        model_name="claude-3-sonnet",
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD
    ),
    "claude-3-opus": TokenPricing(
        model_name="claude-3-opus",
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        tier=ModelTier.EXPENSIVE
    ),
    # Local/free models
    "ollama-local": TokenPricing(
        model_name="ollama-local",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.CHEAP
    ),
}
```

---

### 4. Plugin Architecture

#### Core Components

```python
# vibe_coder/plugins/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import importlib.util
from pathlib import Path

@dataclass
class PluginMetadata:
    """Plugin information."""
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    dependencies: List[str] = None
    permissions: List[str] = None  # "file_access", "network", etc.
    tags: List[str] = None

class BasePlugin(ABC):
    """Base class for all plugins."""

    metadata: PluginMetadata

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality."""

    def on_load(self):
        """Called when plugin is loaded."""

    def on_unload(self):
        """Called when plugin is unloaded."""

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate plugin integrity. Returns (is_valid, errors)."""

class CommandPlugin(BasePlugin):
    """Plugin that adds slash commands."""

    commands: Dict[str, callable]

    async def execute(self, command: str, args: List[str]) -> str:
        """Execute named command."""
        if command not in self.commands:
            raise ValueError(f"Unknown command: {command}")
        return await self.commands[command](*args)

class AnalysisPlugin(BasePlugin):
    """Plugin that analyzes code."""

    @abstractmethod
    async def analyze(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and return findings."""

class FormatterPlugin(BasePlugin):
    """Plugin that formats code."""

    @abstractmethod
    async def format(self, code: str, language: str, config: Dict) -> str:
        """Format code according to rules."""

class IntegrationPlugin(BasePlugin):
    """Plugin that integrates external services."""

    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate with external service."""

    @abstractmethod
    async def call(self, action: str, params: Dict) -> Any:
        """Call external service."""

class PluginManager:
    """Manage plugin lifecycle."""

    def __init__(self, plugins_dir: str = "~/.vibe/plugins"):
        self.plugins_dir = Path(plugins_dir).expanduser()
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> List[PluginMetadata]:
        """Find all available plugins."""
        plugins = []
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                metadata = self._load_plugin_metadata(plugin_dir)
                if metadata:
                    plugins.append(metadata)
        return plugins

    def load_plugin(self, plugin_name: str) -> BasePlugin:
        """Load and initialize a plugin."""
        plugin_dir = self.plugins_dir / plugin_name

        # Load metadata
        metadata = self._load_plugin_metadata(plugin_dir)

        # Load module
        plugin_module = self._import_plugin_module(plugin_dir)

        # Instantiate plugin
        plugin = plugin_module.Plugin()
        plugin.metadata = metadata

        # Validate
        is_valid, errors = plugin.validate()
        if not is_valid:
            raise PluginError(f"Plugin validation failed: {errors}")

        # Initialize
        plugin.on_load()

        self.plugins[plugin_name] = plugin
        return plugin

    def unload_plugin(self, plugin_name: str):
        """Unload a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_unload()
            del self.plugins[plugin_name]

    def _load_plugin_metadata(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """Load plugin.json metadata."""
        metadata_file = plugin_dir / "plugin.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file) as f:
            data = json.load(f)
            return PluginMetadata(**data)

    def _import_plugin_module(self, plugin_dir: Path):
        """Import plugin module."""
        init_file = plugin_dir / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            "plugin", init_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

# Example plugin structure
# ~/.vibe/plugins/my-analysis/
#   plugin.json
#   __init__.py
#   requirements.txt

# plugin.json
{
  "name": "my-analysis",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Custom code analysis plugin",
  "entry_point": "MyAnalysisPlugin",
  "tags": ["analysis", "custom"],
  "permissions": ["file_access"]
}

# __init__.py
from vibe_coder.plugins.base import AnalysisPlugin

class MyAnalysisPlugin(AnalysisPlugin):
    async def analyze(self, code: str, language: str) -> Dict[str, Any]:
        # Custom analysis logic
        return {"findings": [...]}
```

---

## 📁 New File Structure

```
vibe_coder/
├── intelligence/                    # NEW: Repository intelligence
│   ├── __init__.py
│   ├── repo_mapper.py              # Repository mapping and analysis
│   ├── ast_analyzer.py             # AST-based code analysis
│   ├── code_context.py             # Context provider for AI
│   └── dependency_graph.py         # Dependency analysis
├── healing/                         # NEW: Auto-healing system
│   ├── __init__.py
│   ├── auto_healer.py              # Main healing engine
│   ├── validators.py               # Code validators
│   ├── strategies.py               # Validation strategies
│   └── formatters.py               # Code formatters
├── analytics/                       # NEW: Cost tracking
│   ├── __init__.py
│   ├── cost_tracker.py             # Cost and token tracking
│   ├── token_counter.py            # Token estimation
│   ├── pricing.py                  # Pricing database
│   └── reports.py                  # Analytics reports
├── plugins/                         # NEW: Plugin system
│   ├── __init__.py
│   ├── base.py                     # Base plugin classes
│   ├── manager.py                  # Plugin management
│   ├── registry.py                 # Plugin registry
│   └── examples/                   # Example plugins
│       ├── analysis_plugin/
│       ├── formatter_plugin/
│       └── integration_plugin/
├── utils/                           # ENHANCED: Additional utilities
│   ├── __init__.py
│   ├── performance.py              # Performance optimization
│   ├── caching.py                  # Caching system
│   ├── profiling.py                # Code profiling
│   └── monitoring.py               # System monitoring
├── commands/                        # ENHANCED: Add new commands
│   ├── __init__.py
│   ├── heal.py                     # /heal command
│   ├── analyze.py                  # /analyze command
│   ├── tokens.py                   # /tokens command
│   ├── cost.py                     # /cost command
│   └── plugins.py                  # /plugins command
└── tests/
    ├── test_intelligence/          # Repository mapping tests
    ├── test_healing/               # Auto-healing tests
    ├── test_analytics/             # Cost tracking tests
    └── test_plugins/               # Plugin system tests
```

---

## 🚀 Implementation Phases

### Phase 6.1: Repository Intelligence (Week 1)

**Goal:** Implement AST-based repository analysis

**Tasks:**

1. **PythonASTAnalyzer Implementation**
   - AST parsing and traversal
   - Function/class extraction
   - Import analysis
   - Type hint coverage detection
   - Complexity metrics

2. **JavaScriptASTAnalyzer Implementation**
   - tree-sitter integration
   - JS/TS parsing
   - Export detection
   - TypeScript type extraction

3. **RepositoryMapper Implementation**
   - File discovery and filtering
   - Parallel analysis
   - Dependency graph building
   - Caching system

4. **CodeContextProvider Implementation**
   - Relevant context extraction
   - Token budget management
   - Pattern detection

**Tests:**
- 40+ unit tests for AST analyzers
- Integration tests for mapper
- Performance tests for large codebases

**Deliverables:**
- Working repository mapping for Python/JS codebases
- Compressed representations suitable for AI
- Context provider with token budgets

---

### Phase 6.2: Auto-Healing Engine (Week 2)

**Goal:** Implement automatic code fixing

**Tasks:**

1. **CodeValidator Implementation**
   - Syntax validation
   - Type checking (mypy, tsc)
   - Linting (flake8, eslint)
   - Test running
   - Build validation

2. **AutoHealer Implementation**
   - Healing loop logic
   - Error analysis
   - AI-powered fixing
   - Attempt tracking

3. **HealingStrategies**
   - Progressive fixing
   - Context-aware prompts
   - Safety checks

4. **Integration**
   - Backup before healing
   - User confirmations
   - Rollback capability

**Tests:**
- 35+ unit tests for validators
- 20+ integration tests for healer
- Real error fixing scenarios

**Deliverables:**
- Working auto-healing for Python code
- Support for multiple validation strategies
- Safe, reversible changes

---

### Phase 6.3: Cost Tracking System (Week 2-3)

**Goal:** Comprehensive cost and token tracking

**Tasks:**

1. **TokenCounter Implementation**
   - tiktoken integration (OpenAI)
   - Anthropic token counter
   - Estimation formulas
   - Per-model accuracy

2. **CostTracker Implementation**
   - Request recording
   - History persistence
   - Budget management
   - Analytics generation

3. **PricingDatabase**
   - OpenAI pricing
   - Anthropic pricing
   - Local model support
   - Regular updates

4. **CostDisplay**
   - Formatted output
   - Visual gauges
   - Alerts and warnings

**Tests:**
- 25+ unit tests for token counting
- Accuracy tests against real models
- Budget tracking tests

**Deliverables:**
- Accurate token counting
- Cost tracking with history
- Budget alerts and reports

---

### Phase 6.4: Plugin Architecture (Week 3-4)

**Goal:** Extensible plugin system

**Tasks:**

1. **BasePlugin Classes**
   - Abstract interfaces
   - Lifecycle hooks
   - Validation framework

2. **PluginManager**
   - Discovery system
   - Loading/unloading
   - Dependency resolution

3. **Example Plugins**
   - Analysis plugin (custom linting)
   - Formatter plugin (code style)
   - Integration plugin (external service)

4. **Security**
   - Permission system
   - Sandboxing
   - Malware detection

5. **Documentation**
   - Plugin development guide
   - API reference
   - Example plugins

**Tests:**
- 30+ unit tests for plugin system
- Integration tests for loading/running
- Security tests for permissions

**Deliverables:**
- Working plugin system
- 3+ example plugins
- Plugin development guide

---

### Phase 6.5: Performance & Polish (Week 4-5)

**Goal:** Optimize and finalize

**Tasks:**

1. **Performance Optimization**
   - Caching system for repository maps
   - Async optimization
   - Memory profiling
   - Response time benchmarks

2. **Monitoring & Profiling**
   - Performance metrics
   - Usage analytics
   - Resource monitoring

3. **Integration Testing**
   - End-to-end workflows
   - Multi-component testing
   - Real-world scenarios

4. **Documentation**
   - Complete API docs
   - Plugin development guide
   - Cost tracking guide
   - Examples and tutorials

5. **Release Preparation**
   - Final testing
   - Bug fixes
   - Version bumps

**Deliverables:**
- Optimized Phase 6 implementation
- Complete documentation
- Ready for v1.1.0 release

---

## 🧪 Testing Strategy

### Unit Tests (Target: 90%+ coverage)

```python
# tests/test_intelligence/
- test_python_ast_analyzer.py (45 tests)
- test_javascript_analyzer.py (40 tests)
- test_repo_mapper.py (35 tests)
- test_code_context.py (25 tests)

# tests/test_healing/
- test_code_validator.py (40 tests)
- test_auto_healer.py (35 tests)
- test_healing_strategies.py (30 tests)

# tests/test_analytics/
- test_token_counter.py (35 tests)
- test_cost_tracker.py (30 tests)
- test_pricing.py (20 tests)

# tests/test_plugins/
- test_plugin_manager.py (40 tests)
- test_plugin_loading.py (30 tests)
- test_plugin_security.py (25 tests)

Total: 400+ unit tests
```

### Integration Tests

- Repository analysis workflows
- Multi-file healing scenarios
- Cost tracking across operations
- Plugin loading and execution

### Performance Tests

- Large codebase analysis (>100k files)
- Token counting accuracy
- Healing loop performance
- Plugin execution performance

---

## 🔗 Dependencies & External Tools

### New Python Dependencies

```toml
[tool.poetry.dependencies]
# Repository analysis
tree-sitter = "^0.20.0"
tree-sitter-python = "^0.20.0"
tree-sitter-javascript = "^0.20.0"

# Token counting
tiktoken = "^0.5.0"  # OpenAI token counter

# Code analysis
astor = "^0.8.1"
astroid = "^3.0.0"
radon = "^6.0.0"  # Complexity metrics

# Performance monitoring
memory-profiler = "^0.61.0"
line-profiler = "^4.0.0"

# Type checking
mypy-extensions = "^1.0.0"

[tool.poetry.group.dev.dependencies]
# Testing plugins
pytest-plugin-cases = "^3.1.0"
```

### External Tools

- `mypy` - Python type checking
- `tsc` - TypeScript compiler
- `flake8` - Python linting
- `eslint` - JavaScript linting
- `pytest` - Test running
- `git` - Version control operations

---

## 🎯 Success Criteria

### Functional Criteria
- [ ] Repository mapping works for 50+ file codebases
- [ ] Auto-healing fixes 90%+ of common errors
- [ ] Token counting within 5% of actual usage
- [ ] Plugin system loads and executes plugins
- [ ] Cost tracking persists and generates reports

### Quality Criteria
- [ ] 90%+ test coverage for new code
- [ ] Zero critical bugs in Phase 6
- [ ] All code formatted, linted, type-checked
- [ ] Complete API documentation
- [ ] Performance benchmarks met

### User Experience Criteria
- [ ] New commands integrate seamlessly
- [ ] Cost/token information easily accessible
- [ ] Plugin development is straightforward
- [ ] Error messages are helpful
- [ ] Performance is responsive

---

## 📊 Estimated Effort

### Development Time
- **Week 1:** Repository Intelligence (40 hours)
- **Week 2:** Auto-Healing Engine (40 hours)
- **Week 2-3:** Cost Tracking (30 hours)
- **Week 3-4:** Plugin System (40 hours)
- **Week 4-5:** Performance & Polish (35 hours)
- **Total:** ~185 hours (~5 weeks)

### Team Allocation (if applicable)
- **Developer 1:** Repository Intelligence + Auto-Healing
- **Developer 2:** Cost Tracking + Analytics
- **Developer 3:** Plugin System + Tests
- **Lead:** Integration, Documentation, Release

---

## 🚨 Risk Assessment & Mitigation

### Technical Risks

1. **AST Parsing Complexity**
   - Risk: Difficulty handling all Python/JS constructs
   - Mitigation: Focus on common patterns, graceful degradation

2. **Auto-Healing Unreliability**
   - Risk: Fixed code doesn't work
   - Mitigation: Multiple validation strategies, user confirmation

3. **Token Counting Accuracy**
   - Risk: Cost estimates incorrect
   - Mitigation: Use official SDKs, test against real usage

### Performance Risks

1. **Large Repository Scanning**
   - Risk: Slow analysis on huge codebases
   - Mitigation: Caching, incremental updates, async processing

2. **Plugin Loading Overhead**
   - Risk: Slow startup time
   - Mitigation: Lazy loading, plugin isolation

### Security Risks

1. **Malicious Plugins**
   - Risk: Plugins executing untrusted code
   - Mitigation: Permission system, sandboxing, code review

2. **Code Modification Safety**
   - Risk: Auto-healing breaks code
   - Mitigation: Backups, confirmations, version control

---

## 📚 Documentation Plan

### User Documentation
- **Cost Tracking Guide** - Understanding token usage and costs
- **Auto-Healing Guide** - How to use auto-healing features
- **Plugin Guide** - Finding and using plugins
- **Repository Mapping** - Understanding code analysis

### Developer Documentation
- **Plugin Development Guide** - Creating custom plugins
- **API Reference** - All Phase 6 APIs
- **Architecture Guide** - System design overview
- **Extension Points** - How to extend Phase 6

---

## 🎉 Phase 6 Completion Criteria

The phase will be considered complete when:

1. **All Systems Implemented**
   - Repository intelligence working
   - Auto-healing functional
   - Cost tracking accurate
   - Plugin system operational

2. **High Quality Standards**
   - 90%+ test coverage
   - Zero critical bugs
   - Full type safety
   - Comprehensive documentation

3. **Production Ready**
   - Performance benchmarks met
   - Security validated
   - Error handling robust
   - User experience polished

4. **Release Preparation**
   - All tests passing
   - Documentation complete
   - Version bumped to v1.1.0
   - Changelog updated

---

## 🔮 Vision for Phase 6+

### Immediate Next Steps (v1.1.0)
- **Auto-Healing:** Production-ready code fixing
- **Cost Management:** Budget tracking and alerts
- **Repository Intelligence:** Smart context for AI
- **Plugin Ecosystem:** Community extensions

### Future Enhancements (v1.2.0+)
- **MCP Integration:** Model Context Protocol support
- **Vector Search:** Semantic code search with RAG
- **Multi-Language:** Support for more programming languages
- **IDE Integration:** VS Code, JetBrains plugins
- **Web Interface:** Browser-based alternative to CLI

---

**Phase 6 will elevate Vibe Coder from a chat interface to a sophisticated development assistant with deep codebase intelligence, automatic error fixing, and cost awareness.**

---

**Document Version:** 1.0
**Last Updated:** December 2024
**Status:** Planning Complete - Ready for Implementation
