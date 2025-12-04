"""Tests for the AST analyzer."""

import tempfile
from pathlib import Path

import pytest

from vibe_coder.intelligence.ast_analyzer import PythonASTAnalyzer, calculate_complexity


class TestPythonASTAnalyzer:
    """Tests for PythonASTAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PythonASTAnalyzer()

    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing."""
        code = '''"""Sample module docstring."""

import os
from typing import List, Optional

def simple_function(x: int, y: str) -> bool:
    """A simple function."""
    return True

async def async_function(data: List[str]) -> None:
    """An async function."""
    pass

class MyClass:
    """A sample class."""

    attr: str
    count: int = 0

    def __init__(self, name: str):
        """Initialize."""
        self.name = name

    async def process(self, items: List[int]) -> Optional[str]:
        """Process items."""
        if items:
            for item in items:
                if item > 0:
                    return str(item)
        return None

@dataclass
class DataClass:
    """A dataclass."""
    field1: str
    field2: int
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    @pytest.mark.asyncio
    async def test_analyze_file_basic(self, analyzer, sample_python_file):
        """Test basic file analysis."""
        result = await analyzer.analyze_file(sample_python_file)

        assert result is not None
        assert result.language == "python"
        assert result.lines_of_code > 0
        assert result.has_docstring is True

        # Clean up
        Path(sample_python_file).unlink()

    @pytest.mark.asyncio
    async def test_extract_functions(self, analyzer, sample_python_file):
        """Test function extraction."""
        result = await analyzer.analyze_file(sample_python_file)

        assert result is not None
        func_names = [f.name for f in result.functions]
        assert "simple_function" in func_names
        assert "async_function" in func_names

        # Check async function
        async_func = next(f for f in result.functions if f.name == "async_function")
        assert async_func.is_async is True

        # Check parameters
        simple_func = next(f for f in result.functions if f.name == "simple_function")
        assert len(simple_func.parameters) == 2
        assert simple_func.return_type == "bool"

        Path(sample_python_file).unlink()

    @pytest.mark.asyncio
    async def test_extract_classes(self, analyzer, sample_python_file):
        """Test class extraction."""
        result = await analyzer.analyze_file(sample_python_file)

        assert result is not None
        class_names = [c.name for c in result.classes]
        assert "MyClass" in class_names
        assert "DataClass" in class_names

        # Check MyClass
        my_class = next(c for c in result.classes if c.name == "MyClass")
        assert my_class.docstring is not None
        assert len(my_class.methods) >= 2
        assert len(my_class.attributes) >= 2

        # Check DataClass
        data_class = next(c for c in result.classes if c.name == "DataClass")
        assert data_class.is_dataclass is True

        Path(sample_python_file).unlink()

    @pytest.mark.asyncio
    async def test_extract_imports(self, analyzer, sample_python_file):
        """Test import extraction."""
        result = await analyzer.analyze_file(sample_python_file)

        assert result is not None
        assert "os" in result.imports
        assert any("typing" in imp for imp in result.imports)

        Path(sample_python_file).unlink()

    @pytest.mark.asyncio
    async def test_type_hints_coverage(self, analyzer, sample_python_file):
        """Test type hints coverage calculation."""
        result = await analyzer.analyze_file(sample_python_file)

        assert result is not None
        assert result.type_hints_coverage > 0

        Path(sample_python_file).unlink()

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer):
        """Test analyzing a nonexistent file."""
        result = await analyzer.analyze_file("/nonexistent/path.py")
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_syntax_error(self, analyzer):
        """Test analyzing a file with syntax errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(:\n  pass")
            path = f.name

        result = await analyzer.analyze_file(path)
        assert result is None

        Path(path).unlink()

    @pytest.mark.asyncio
    async def test_caching(self, analyzer, sample_python_file):
        """Test file caching."""
        # First analysis
        result1 = await analyzer.analyze_file(sample_python_file)

        # Second analysis should use cache
        result2 = await analyzer.analyze_file(sample_python_file)

        assert result1 is not None
        assert result2 is not None
        assert result1.lines_of_code == result2.lines_of_code

        # Check cache stats
        stats = analyzer.get_cache_stats()
        assert stats["cached_files"] > 0

        Path(sample_python_file).unlink()

    def test_clear_cache(self, analyzer):
        """Test cache clearing."""
        analyzer._cache["test"] = (0, None)
        analyzer.clear_cache()
        assert len(analyzer._cache) == 0


class TestComplexityCalculation:
    """Tests for complexity calculation."""

    def test_simple_function_complexity(self):
        """Test complexity of simple function."""
        import ast

        code = "def func(): pass"
        tree = ast.parse(code)
        func = tree.body[0]

        complexity = calculate_complexity(func)
        assert complexity == 1

    def test_if_statement_complexity(self):
        """Test complexity with if statement."""
        import ast

        code = """
def func(x):
    if x > 0:
        return True
    return False
"""
        tree = ast.parse(code)
        func = tree.body[0]

        complexity = calculate_complexity(func)
        assert complexity == 2  # 1 base + 1 if

    def test_loop_complexity(self):
        """Test complexity with loops."""
        import ast

        code = """
def func(items):
    for item in items:
        while item > 0:
            item -= 1
"""
        tree = ast.parse(code)
        func = tree.body[0]

        complexity = calculate_complexity(func)
        assert complexity >= 3  # 1 base + 1 for + 1 while

    def test_boolean_complexity(self):
        """Test complexity with boolean operators."""
        import ast

        code = """
def func(a, b, c):
    if a and b or c:
        pass
"""
        tree = ast.parse(code)
        func = tree.body[0]

        complexity = calculate_complexity(func)
        assert complexity >= 3  # 1 base + 1 if + 2 bool ops

    def test_exception_complexity(self):
        """Test complexity with exception handling."""
        import ast

        code = """
def func():
    try:
        pass
    except ValueError:
        pass
    except KeyError:
        pass
"""
        tree = ast.parse(code)
        func = tree.body[0]

        complexity = calculate_complexity(func)
        assert complexity >= 3  # 1 base + 2 except handlers
