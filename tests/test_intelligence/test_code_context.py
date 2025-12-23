"""
Tests for code context provider functionality.

This module tests the CodeContextProvider class which provides intelligent
context extraction for AI-powered code operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.intelligence.code_context import (
    CodeContextProvider,
    ContextRequest,
    ContextResult,
    OperationType,
)
from vibe_coder.intelligence.types import ClassSignature, ContextItem, FileNode, FunctionSignature


class TestContextRequest:
    """Test ContextRequest dataclass."""

    def test_context_request_creation(self):
        """Test creating a context request."""
        request = ContextRequest(
            operation=OperationType.GENERATE,
            target_file="test.py",
            target_function="test_func",
            token_budget=4000,
            include_tests=True,
        )

        assert request.operation == OperationType.GENERATE
        assert request.target_file == "test.py"
        assert request.target_function == "test_func"
        assert request.token_budget == 4000
        assert request.include_tests is True
        assert request.include_docstrings is True  # Default value

    def test_context_request_defaults(self):
        """Test context request with default values."""
        request = ContextRequest(operation=OperationType.FIX)

        assert request.operation == OperationType.FIX
        assert request.target_file is None
        assert request.target_function is None
        assert request.target_class is None
        assert request.related_files is None
        assert request.token_budget == 8000  # Default value
        assert request.include_tests is False
        assert request.include_docstrings is True

    def test_operation_type_values(self):
        """Test operation type enum values."""
        assert OperationType.GENERATE.value == "generate"
        assert OperationType.FIX.value == "fix"
        assert OperationType.REFACTOR.value == "refactor"
        assert OperationType.EXPLAIN.value == "explain"
        assert OperationType.TEST.value == "test"
        assert OperationType.DOCUMENT.value == "document"


class TestCodeContextProviderInitialization:
    """Test CodeContextProvider initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Test provider initialization with default parameters."""
        mock_mapper = MagicMock()

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)

        assert provider.repo_mapper == mock_mapper
        assert provider.model_name == "gpt-4"  # Default
        assert provider.CHARS_PER_TOKEN == 4

    def test_init_with_custom_model(self, tmp_path):
        """Test provider initialization with custom model."""
        mock_mapper = MagicMock()

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper, model_name="gpt-3.5-turbo")

        assert provider.model_name == "gpt-3.5-turbo"


class TestGenerationContext:
    """Test context extraction for code generation."""

    @pytest.mark.asyncio
    async def test_get_generation_context_no_target(self, tmp_path):
        """Test generation context without target file."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")

            request = ContextRequest(operation=OperationType.GENERATE)
            result = await provider.get_context(request)

        assert isinstance(result, ContextResult)
        assert "# Project Overview" in result.context
        assert result.token_estimate > 0
        assert result.files_included == []
        assert result.functions_included == []
        assert result.classes_included == []

    @pytest.mark.asyncio
    async def test_get_generation_context_with_target(self, tmp_path):
        """Test generation context with target file."""
        # Create a test file
        test_file = tmp_path / "target.py"
        test_file.write_text(
            """
def existing_function():
    '''Existing function docstring.'''
    pass
"""
        )

        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None
        mock_mapper._repo_map = {
            "target.py": FileNode(
                path="target.py",
                language="python",
                lines_of_code=5,
                functions=[
                    FunctionSignature(
                        name="existing_function",
                        module_path="target",
                        file_path="target.py",
                        line_start=2,
                        line_end=4,
                        docstring="Existing function docstring.",
                    )
                ],
                classes=[],
            )
        }

        # Mock the file context method
        async def mock_get_file_context(file_path, include_docstrings=True):
            if file_path == "target.py":
                return (
                    "# File: target.py\ndef existing_function():\n"
                    "    '''Existing function docstring.'''\n    pass"
                )
            return None

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_context = mock_get_file_context

            request = ContextRequest(
                operation=OperationType.GENERATE, target_file="target.py", token_budget=4000
            )
            result = await provider.get_context(request)

        assert "# Project Overview" in result.context
        assert "# File: target.py" in result.context
        assert "existing_function" in result.context
        assert "target.py" in result.files_included
        assert result.token_estimate > 0

    @pytest.mark.asyncio
    async def test_get_generation_context_with_related_files(self, tmp_path):
        """Test generation context with related files."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock context items
        context_items = [
            ContextItem(
                path="utils.py",
                content="# Utils module\n def helper(): pass",
                importance=0.8,
                token_count=20,
                type="file",
                metadata={"functions": 1, "classes": 0},
            ),
            ContextItem(
                path="models.py",
                content="# Models module\n class Model: pass",
                importance=0.6,
                token_count=20,
                type="file",
                metadata={"functions": 0, "classes": 1},
            ),
        ]
        mock_mapper.get_context_items.return_value = context_items

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")

            request = ContextRequest(
                operation=OperationType.GENERATE,
                related_files=["utils.py", "models.py"],
                token_budget=8000,
            )
            result = await provider._get_generation_context(request)

        assert "utils.py" in result.context
        assert "models.py" in result.context
        assert len(result.files_included) == 2


class TestFixContext:
    """Test context extraction for code fixing."""

    @pytest.mark.asyncio
    async def test_get_fix_context(self, tmp_path):
        """Test fix context extraction."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock file with error
        mock_mapper._repo_map = {
            "buggy.py": FileNode(
                path="buggy.py",
                language="python",
                lines_of_code=10,
                functions=[
                    FunctionSignature(
                        name="buggy_function",
                        module_path="buggy",
                        file_path="buggy.py",
                        line_start=1,
                        line_end=10,
                    )
                ],
                classes=[],
            )
        }

        async def mock_get_file_content(file_path):
            return (
                "def buggy_function():\n    undefined_variable = x\n    return undefined_variable"
            )

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.FIX,
                target_file="buggy.py",
                target_function="buggy_function",
            )
            result = await provider.get_context(request)

        assert "buggy_function" in result.context
        assert "buggy.py" in result.files_included

    @pytest.mark.asyncio
    async def test_get_fix_context_with_dependencies(self, tmp_path):
        """Test fix context includes file dependencies."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None
        mock_mapper._repo_map = {
            "main.py": FileNode(
                path="main.py",
                language="python",
                lines_of_code=5,
                imports=["utils"],
                dependencies={"utils.py"},
            ),
            "utils.py": FileNode(
                path="utils.py",
                language="python",
                lines_of_code=10,
                functions=[
                    FunctionSignature(
                        name="helper",
                        module_path="utils",
                        file_path="utils.py",
                        line_start=1,
                        line_end=10,
                    )
                ],
                classes=[],
            ),
        }

        async def mock_get_file_content(file_path):
            if file_path == "main.py":
                return "import utils\n\ndef main():\n    utils.helper()"
            elif file_path == "utils.py":
                return "def helper():\n    return 'help'"
            return None

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(operation=OperationType.FIX, target_file="main.py")
            result = await provider.get_context(request)

        assert "main.py" in result.context
        assert "utils.py" in result.context
        assert len(result.files_included) >= 1


class TestRefactorContext:
    """Test context extraction for code refactoring."""

    @pytest.mark.asyncio
    async def test_get_refactor_context_function(self, tmp_path):
        """Test refactor context for a specific function."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock file with function to refactor
        func_signature = FunctionSignature(
            name="legacy_function",
            module_path="legacy",
            file_path="legacy.py",
            line_start=1,
            line_end=20,
            parameters=["param1", "param2"],
            complexity=10,
            docstring="Legacy function that needs refactoring.",
        )

        mock_mapper._repo_map = {
            "legacy.py": FileNode(
                path="legacy.py",
                language="python",
                lines_of_code=30,
                functions=[func_signature],
                classes=[],
            )
        }

        async def mock_get_file_content(file_path, start_line=None, end_line=None):
            return """
def legacy_function(param1, param2):
    '''Legacy function that needs refactoring.'''
    # Complex logic that should be simplified
    result = []
    for i in range(len(param1)):
        for j in range(len(param2)):
            if param1[i] == param2[j]:
                result.append(param1[i])
    return result
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.REFACTOR,
                target_file="legacy.py",
                target_function="legacy_function",
            )
            result = await provider.get_context(request)

        assert "legacy_function" in result.context
        assert "legacy.py" in result.files_included
        assert "legacy_function" in result.functions_included

    @pytest.mark.asyncio
    async def test_get_refactor_context_class(self, tmp_path):
        """Test refactor context for a specific class."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock file with class to refactor
        class_signature = ClassSignature(
            name="LegacyClass",
            module_path="legacy",
            file_path="legacy.py",
            line_start=1,
            line_end=50,
            methods=[
                FunctionSignature(
                    name="old_method",
                    module_path="legacy",
                    file_path="legacy.py",
                    line_start=10,
                    line_end=30,
                    is_method=True,
                )
            ],
            attributes=["_old_attr1", "_old_attr2"],
        )

        mock_mapper._repo_map = {
            "legacy.py": FileNode(
                path="legacy.py",
                language="python",
                lines_of_code=60,
                functions=[],
                classes=[class_signature],
            )
        }

        async def mock_get_file_content(file_path):
            return """
class LegacyClass:
    '''Legacy class that needs refactoring.'''

    def __init__(self):
        self._old_attr1 = None
        self._old_attr2 = []

    def old_method(self):
        # Old implementation
        pass
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.REFACTOR,
                target_file="legacy.py",
                target_class="LegacyClass",
            )
            result = await provider.get_context(request)

        assert "LegacyClass" in result.context
        assert "legacy.py" in result.files_included
        assert "LegacyClass" in result.classes_included


class TestExplainContext:
    """Test context extraction for code explanation."""

    @pytest.mark.asyncio
    async def test_get_explain_context(self, tmp_path):
        """Test explain context extraction."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock complex code to explain
        mock_mapper._repo_map = {
            "complex.py": FileNode(
                path="complex.py",
                language="python",
                lines_of_code=50,
                functions=[
                    FunctionSignature(
                        name="complex_algorithm",
                        module_path="complex",
                        file_path="complex.py",
                        line_start=1,
                        line_end=40,
                        docstring="Complex algorithm implementation.",
                    )
                ],
                imports=["numpy", "scipy"],
            )
        }

        async def mock_get_file_content(file_path):
            return """
import numpy as np
from scipy import stats

def complex_algorithm(data):
    '''Complex algorithm implementation.'''
    # Complex mathematical operations
    normalized = (data - np.mean(data)) / np.std(data)
    transformed = stats.boxcox(normalized)[0]

    # More complex logic
    result = np.fft.fft(transformed)
    return np.abs(result)
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(operation=OperationType.EXPLAIN, target_file="complex.py")
            result = await provider.get_context(request)

        assert "complex_algorithm" in result.context
        assert "numpy" in result.context
        assert "scipy" in result.context
        assert "complex.py" in result.files_included


class TestDocumentContext:
    """Test context extraction for documentation generation."""

    @pytest.mark.asyncio
    async def test_get_document_context_with_docstrings(self, tmp_path):
        """Test document context with docstrings included."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        func_with_docstring = FunctionSignature(
            name="documented_function",
            module_path="docs",
            file_path="docs.py",
            line_start=1,
            line_end=20,
            docstring=(
                "This function does something important.\n\n"
                "    Args:\n        param: The parameter\n    "
                "Returns:\n        The result"
            ),
        )

        mock_mapper._repo_map = {
            "docs.py": FileNode(
                path="docs.py",
                language="python",
                lines_of_code=30,
                functions=[func_with_docstring],
                classes=[],
            )
        }

        async def mock_get_file_content(file_path):
            return """
def documented_function(param):
    '''This function does something important.

    Args:
        param: The parameter
    Returns:
        The result
    '''
    # Implementation
    return param * 2
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.DOCUMENT, target_file="docs.py", include_docstrings=True
            )
            result = await provider.get_context(request)

        assert "documented_function" in result.context
        assert "This function does something important" in result.context
        assert "param" in result.context

    @pytest.mark.asyncio
    async def test_get_document_context_without_docstrings(self, tmp_path):
        """Test document context without docstrings."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        func_without_docstring = FunctionSignature(
            name="undocumented_function",
            module_path="docs",
            file_path="docs.py",
            line_start=1,
            line_end=10,
            docstring=None,
        )

        mock_mapper._repo_map = {
            "docs.py": FileNode(
                path="docs.py",
                language="python",
                lines_of_code=15,
                functions=[func_without_docstring],
                classes=[],
            )
        }

        async def mock_get_file_content(file_path):
            return """
def undocumented_function(param):
    # No docstring
    return param * 2
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.DOCUMENT, target_file="docs.py", include_docstrings=False
            )
            result = await provider.get_context(request)

        assert "undocumented_function" in result.context
        # Should still include the function even without docstring
        assert "docs.py" in result.files_included


class TestTestContext:
    """Test context extraction for test generation."""

    @pytest.mark.asyncio
    async def test_get_test_context_for_function(self, tmp_path):
        """Test test context for a specific function."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock function to test
        func_to_test = FunctionSignature(
            name="calculate_sum",
            module_path="math",
            file_path="math.py",
            line_start=1,
            line_end=15,
            parameters=["numbers"],
            return_type="int",
            docstring="Calculate sum of numbers in a list.",
        )

        mock_mapper._repo_map = {
            "math.py": FileNode(
                path="math.py",
                language="python",
                lines_of_code=20,
                functions=[func_to_test],
                classes=[],
                imports=["typing"],
            ),
            "tests/test_math.py": FileNode(
                path="tests/test_math.py",
                language="python",
                lines_of_code=5,
                functions=[],
                classes=[],
            ),
        }

        async def mock_get_file_content(file_path):
            if file_path == "math.py":
                return """
from typing import List

def calculate_sum(numbers: List[int]) -> int:
    '''Calculate sum of numbers in a list.'''
    return sum(numbers)
"""
            elif file_path == "tests/test_math.py":
                return "# Existing test file"
            return None

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.TEST,
                target_file="math.py",
                target_function="calculate_sum",
                include_tests=True,
            )
            result = await provider.get_context(request)

        assert "calculate_sum" in result.context
        assert "typing" in result.context  # Import dependency
        assert "tests/test_math.py" in result.files_included

    @pytest.mark.asyncio
    async def test_get_test_context_for_class(self, tmp_path):
        """Test test context for a class."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock class to test
        class_to_test = ClassSignature(
            name="Calculator",
            module_path="calc",
            file_path="calc.py",
            line_start=1,
            line_end=40,
            methods=[
                FunctionSignature(
                    name="add",
                    module_path="calc",
                    file_path="calc.py",
                    line_start=10,
                    line_end=15,
                    parameters=["a", "b"],
                    return_type="int",
                    is_method=True,
                ),
                FunctionSignature(
                    name="multiply",
                    module_path="calc",
                    file_path="calc.py",
                    line_start=20,
                    line_end=25,
                    parameters=["a", "b"],
                    return_type="int",
                    is_method=True,
                ),
            ],
        )

        mock_mapper._repo_map = {
            "calc.py": FileNode(
                path="calc.py",
                language="python",
                lines_of_code=50,
                functions=[],
                classes=[class_to_test],
            )
        }

        async def mock_get_file_content(file_path):
            return """
class Calculator:
    '''Simple calculator class.'''

    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return a * b
"""

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Project Overview")
            provider._get_file_content = mock_get_file_content

            request = ContextRequest(
                operation=OperationType.TEST, target_file="calc.py", target_class="Calculator"
            )
            result = await provider.get_context(request)

        assert "Calculator" in result.context
        assert "add" in result.context
        assert "multiply" in result.context
        assert "Calculator" in result.classes_included


class TestContextWithBudgeting:
    """Test context extraction with dynamic token budgeting."""

    @pytest.mark.asyncio
    async def test_get_context_with_budgeting(self, tmp_path):
        """Test context extraction with token budgeting."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock context items
        context_items = [
            ContextItem(
                path="high_importance.py",
                content="# High importance file",
                importance=0.9,
                token_count=100,
                type="file",
                metadata={"functions": 2, "classes": 1},
            ),
            ContextItem(
                path="medium_importance.py",
                content="# Medium importance file",
                importance=0.6,
                token_count=200,
                type="file",
                metadata={"functions": 1, "classes": 0},
            ),
            ContextItem(
                path="low_importance.py",
                content="# Low importance file",
                importance=0.3,
                token_count=300,
                type="file",
                metadata={"functions": 0, "classes": 0},
            ),
        ]
        mock_mapper.get_context_items.return_value = context_items

        # Mock token budgeter
        mock_budget = MagicMock()
        mock_budget.total = 1000
        mock_budget.available = 500
        mock_budget.allocations = {"repository_overview": 100}

        mock_budgeter = AsyncMock()
        mock_budgeter.calculate_budget.return_value = mock_budget
        mock_budgeter.compress_context.return_value = context_items[:2]  # Filtered items
        mock_budgeter.estimate_tokens.return_value = 50

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter", return_value=mock_budgeter),
        ):
            provider = CodeContextProvider(mock_mapper)

            request = ContextRequest(
                operation=OperationType.GENERATE,
                target_file="high_importance.py",
                token_budget=8000,
            )
            result = await provider.get_context_with_budgeting(
                request, conversation_history_length=100
            )

        assert isinstance(result, ContextResult)
        assert len(result.files_included) == 2  # Filtered items
        assert "high_importance.py" in result.files_included
        assert "medium_importance.py" in result.files_included
        assert result.token_estimate > 0
        assert result.truncated is True  # Items were filtered out

    @pytest.mark.asyncio
    async def test_context_budgeting_small_budget(self, tmp_path):
        """Test context extraction with very small token budget."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock context items
        context_items = [
            ContextItem(
                path="large_file.py",
                content="#" * 1000,  # Large content
                importance=0.8,
                token_count=1000,
                type="file",
                metadata={},
            ),
        ]
        mock_mapper.get_context_items.return_value = context_items

        # Mock small budget
        mock_budget = MagicMock()
        mock_budget.total = 100
        mock_budget.available = 50
        mock_budget.allocations = {}

        mock_budgeter = AsyncMock()
        mock_budgeter.calculate_budget.return_value = mock_budget
        mock_budgeter.compress_context.return_value = []  # No items fit
        mock_budgeter.estimate_tokens.return_value = 50

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter", return_value=mock_budgeter),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Small overview")

            request = ContextRequest(operation=OperationType.EXPLAIN, token_budget=100)
            result = await provider.get_context_with_budgeting(request)

        assert len(result.files_included) == 0  # No files fit budget
        assert result.token_estimate >= 50  # At least overview


class TestGenericContext:
    """Test generic context extraction fallback."""

    @pytest.mark.asyncio
    async def test_get_generic_context(self, tmp_path):
        """Test generic context extraction for unknown operations."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            provider._get_project_overview = MagicMock(return_value="# Generic Project Overview")

            # Create request with unknown operation type (direct enum value)
            request = ContextRequest(operation=OperationType("unknown"))
            result = await provider.get_context(request)

        assert isinstance(result, ContextResult)
        assert "# Generic Project Overview" in result.context
        assert result.files_included == []
        assert result.functions_included == []
        assert result.classes_included == []


class TestContextResult:
    """Test ContextResult dataclass."""

    def test_context_result_creation(self):
        """Test creating a context result."""
        result = ContextResult(
            context="# Sample context",
            files_included=["file1.py", "file2.py"],
            functions_included=["func1", "func2"],
            classes_included=["Class1"],
            token_estimate=1000,
            truncated=False,
        )

        assert result.context == "# Sample context"
        assert len(result.files_included) == 2
        assert "file1.py" in result.files_included
        assert "file2.py" in result.files_included
        assert len(result.functions_included) == 2
        assert len(result.classes_included) == 1
        assert result.token_estimate == 1000
        assert result.truncated is False

    def test_context_result_defaults(self):
        """Test context result with default values."""
        result = ContextResult(
            context="# Minimal context",
            files_included=[],
            functions_included=[],
            classes_included=[],
            token_estimate=100,
        )

        assert result.truncated is False  # Default value


class TestHelperMethods:
    """Test helper methods for context extraction."""

    @pytest.mark.asyncio
    async def test_get_project_overview(self, tmp_path):
        """Test getting project overview."""
        mock_mapper = AsyncMock()
        mock_mapper.scan_repository.return_value = None

        # Mock repository map
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.root_path = "test_project"
        mock_mapper._repo_map.total_files = 10
        mock_mapper._repo_map.total_lines = 1000
        mock_mapper._repo_map.languages = {"python": 8, "javascript": 2}

        with (
            patch("vibe_coder.intelligence.code_context.TokenCounter"),
            patch("vibe_coder.intelligence.code_context.TokenBudgeter"),
        ):
            provider = CodeContextProvider(mock_mapper)
            overview = provider._get_project_overview()

        assert "test_project" in overview
        assert "10 files" in overview
        assert "1000 lines" in overview
        assert "python" in overview
        assert "javascript" in overview
