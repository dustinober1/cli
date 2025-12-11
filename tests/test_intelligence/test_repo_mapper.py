"""
Tests for repository mapping and analysis functionality.

This module tests the RepositoryMapper class which provides high-level
repository scanning, dependency graph building, and caching capabilities.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.types import FileNode, FunctionSignature, RepositoryMap


class TestRepositoryMapperInitialization:
    """Test RepositoryMapper initialization and configuration."""

    def test_init_with_default_parameters(self, tmp_path):
        """Test mapper initialization with default parameters."""
        mapper = RepositoryMapper(str(tmp_path))

        assert mapper.root_path == tmp_path.resolve()
        assert mapper.cache_dir == tmp_path / ".vibe_cache"
        assert mapper.ignore_patterns == RepositoryMapper.DEFAULT_IGNORE_PATTERNS
        assert mapper.enable_monitoring is False
        assert mapper.enable_importance_scoring is True
        assert mapper.enable_reference_resolution is True

    def test_init_with_custom_parameters(self, tmp_path):
        """Test mapper initialization with custom parameters."""
        cache_dir = tmp_path / "custom_cache"
        ignore_patterns = ["*.log", "temp/*"]

        mapper = RepositoryMapper(
            root_path=str(tmp_path),
            cache_dir=str(cache_dir),
            ignore_patterns=ignore_patterns,
            enable_monitoring=True,
            enable_importance_scoring=False,
            enable_reference_resolution=False,
        )

        assert mapper.cache_dir == cache_dir
        assert mapper.ignore_patterns == ignore_patterns
        assert mapper.enable_monitoring is True
        assert mapper.enable_importance_scoring is False
        assert mapper.enable_reference_resolution is False

    def test_language_extensions_mapping(self):
        """Test that language extensions are properly mapped."""
        mapper = RepositoryMapper("/tmp")

        assert mapper.LANGUAGE_EXTENSIONS[".py"] == "python"
        assert mapper.LANGUAGE_EXTENSIONS[".js"] == "javascript"
        assert mapper.LANGUAGE_EXTENSIONS[".ts"] == "typescript"
        assert mapper.LANGUAGE_EXTENSIONS[".go"] == "go"
        assert mapper.LANGUAGE_EXTENSIONS[".rs"] == "rust"
        assert mapper.LANGUAGE_EXTENSIONS[".java"] == "java"

    def test_default_ignore_patterns(self):
        """Test default ignore patterns include common directories."""
        mapper = RepositoryMapper("/tmp")

        assert "__pycache__" in mapper.ignore_patterns
        assert "*.pyc" in mapper.ignore_patterns
        assert ".git" in mapper.ignore_patterns
        assert "node_modules" in mapper.ignore_patterns
        assert "venv" in mapper.ignore_patterns
        assert ".venv" in mapper.ignore_patterns


class TestFileDiscovery:
    """Test file discovery functionality."""

    def test_discover_python_files(self, tmp_path):
        """Test discovering Python files in a repository."""
        # Create test file structure
        (tmp_path / "main.py").touch()
        (tmp_path / "utils.py").touch()
        (tmp_path / "submodule").mkdir()
        (tmp_path / "submodule" / "__init__.py").touch()
        (tmp_path / "submodule" / "helper.py").touch()

        # Create files that should be ignored
        (tmp_path / "test.pyc").touch()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.py").touch()

        mapper = RepositoryMapper(str(tmp_path))
        files = mapper._discover_files()

        # Should find Python files but not ignored ones
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "helper.py" in file_names
        assert "__init__.py" in file_names
        assert "test.pyc" not in file_names
        assert "cache.py" not in file_names

    def test_discover_mixed_language_files(self, tmp_path):
        """Test discovering files in multiple languages."""
        # Create files in different languages
        (tmp_path / "app.py").touch()
        (tmp_path / "script.js").touch()
        (tmp_path / "component.tsx").touch()
        (tmp_path / "main.go").touch()
        (tmp_path / "lib.rs").touch()

        # Create unknown file type
        (tmp_path / "data.txt").touch()

        mapper = RepositoryMapper(str(tmp_path))
        files = mapper._discover_files()

        file_names = [f.name for f in files]
        assert "app.py" in file_names
        assert "script.js" in file_names
        assert "component.tsx" in file_names
        assert "main.go" in file_names
        assert "lib.rs" in file_names
        assert "data.txt" not in file_names  # Not in LANGUAGE_EXTENSIONS

    def test_discover_files_with_custom_ignore_patterns(self, tmp_path):
        """Test file discovery with custom ignore patterns."""
        # Create file structure
        (tmp_path / "main.py").touch()
        (tmp_path / "temp.py").touch()
        (tmp_path / "backup.py").touch()
        (tmp_path / "logs").mkdir()
        (tmp_path / "logs" / "app.py").touch()

        mapper = RepositoryMapper(str(tmp_path), ignore_patterns=["temp*", "backup*", "logs/*"])
        files = mapper._discover_files()

        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "temp.py" not in file_names
        assert "backup.py" not in file_names


class TestFileAnalysis:
    """Test file analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_python_file(self, tmp_path):
        """Test analyzing a Python file with AST."""
        # Create a Python file with various constructs
        python_content = '''
"""Module docstring."""

import os
import sys
from typing import Optional

def simple_function(param1: str, param2: int = 10) -> bool:
    """A simple function with type hints."""
    return param1 and param2 > 0

async def async_function() -> None:
    """An async function."""
    await asyncio.sleep(1)

class TestClass:
    """A test class."""

    def __init__(self, value: int):
        self.value = value

    def method(self) -> int:
        """Instance method."""
        return self.value

    @staticmethod
    def static_method() -> str:
        """Static method."""
        return "static"
'''
        py_file = tmp_path / "test_module.py"
        py_file.write_text(python_content)

        mapper = RepositoryMapper(str(tmp_path))
        node = await mapper._analyze_python_file(py_file)

        assert node is not None
        assert node.language == "python"
        assert node.lines_of_code > 0
        assert node.has_docstring is True
        assert len(node.functions) >= 2  # simple_function and async_function
        assert len(node.classes) >= 1  # TestClass
        assert "os" in node.imports
        assert "sys" in node.imports
        assert "typing" in node.imports

    @pytest.mark.asyncio
    async def test_create_basic_file_node(self, tmp_path):
        """Test creating a basic file node for non-Python files."""
        # Create a JavaScript file
        js_content = '''
// JavaScript file
function greet(name) {
    return `Hello, ${name}!`;
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
'''
        js_file = tmp_path / "script.js"
        js_file.write_text(js_content)

        mapper = RepositoryMapper(str(tmp_path))
        node = await mapper._create_basic_file_node(js_file, "javascript")

        assert node.language == "javascript"
        assert node.lines_of_code == len(js_content.splitlines())
        assert len(node.functions) == 0  # Non-Python files don't have AST analysis
        assert len(node.classes) == 0

    @pytest.mark.asyncio
    async def test_analyze_files_in_parallel(self, tmp_path):
        """Test analyzing multiple files in parallel."""
        # Create multiple Python files
        for i in range(5):
            (tmp_path / f"module_{i}.py").write_text(f"# Module {i}\n\ndef func_{i}():\n    pass\n")

        # Create a JavaScript file
        (tmp_path / "script.js").write_text("// JavaScript\nconsole.log('hello');")

        mapper = RepositoryMapper(str(tmp_path))
        files = mapper._discover_files()
        file_nodes = await mapper._analyze_files(files)

        assert len(file_nodes) == 6  # 5 Python + 1 JavaScript
        for node in file_nodes.values():
            if node.language == "python":
                assert len(node.functions) >= 1
            elif node.language == "javascript":
                assert node.lines_of_code > 0


class TestDependencyGraph:
    """Test dependency graph construction."""

    def test_build_dependency_graph(self, tmp_path):
        """Test building import dependency graph."""
        # Create mock file nodes with imports
        file_nodes = {
            "main.py": FileNode(
                path="main.py",
                language="python",
                imports=["utils", "os", "sys"],
                dependencies=set()
            ),
            "utils.py": FileNode(
                path="utils.py",
                language="python",
                imports=["helpers"],
                dependencies=set()
            ),
            "helpers.py": FileNode(
                path="helpers.py",
                language="python",
                imports=[],
                dependencies=set()
            ),
            "external.py": FileNode(
                path="external.py",
                language="python",
                imports=["external_lib"],  # Not in repository
                dependencies=set()
            ),
        }

        mapper = RepositoryMapper(str(tmp_path))
        graph = mapper._build_dependency_graph(file_nodes)

        # Check dependencies
        assert graph["main.py"] == {"utils.py"}
        assert graph["utils.py"] == {"helpers.py"}
        assert "helpers.py" not in graph  # No internal dependencies
        assert "external.py" not in graph  # Only external dependencies

    def test_find_import_file_module(self, tmp_path):
        """Test finding import file for module import."""
        file_nodes = {
            "package/module.py": FileNode(path="package/module.py", language="python"),
            "package/__init__.py": FileNode(path="package/__init__.py", language="python"),
        }

        mapper = RepositoryMapper(str(tmp_path))

        # Test module import
        result = mapper._find_import_file("package.module", file_nodes)
        assert result == "package/module.py"

        # Test package import
        result = mapper._find_import_file("package", file_nodes)
        assert result == "package/__init__.py"

    def test_find_import_file_not_found(self, tmp_path):
        """Test handling when import file is not found."""
        file_nodes = {
            "existing.py": FileNode(path="existing.py", language="python"),
        }

        mapper = RepositoryMapper(str(tmp_path))
        result = mapper._find_import_file("nonexistent.module", file_nodes)
        assert result is None


class TestRepositoryScanning:
    """Test complete repository scanning functionality."""

    @pytest.mark.asyncio
    async def test_scan_small_repository(self, tmp_path):
        """Test scanning a small repository."""
        # Create a simple project structure
        (tmp_path / "main.py").write_text("""
import utils

def main():
    utils.helper()

if __name__ == "__main__":
    main()
""")
        (tmp_path / "utils.py").write_text("""
def helper():
    return "help"
""")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("""
def test_main():
    assert True
""")

        mapper = RepositoryMapper(str(tmp_path))
        repo_map = await mapper.scan_repository(use_cache=False)

        assert repo_map.total_files == 3
        assert repo_map.total_lines > 0
        assert "python" in repo_map.languages
        assert repo_map.languages["python"] == 3
        assert len(repo_map.entry_points) >= 1  # main.py has __main__ block
        assert len(repo_map.test_files) >= 1  # test_main.py

    @pytest.mark.asyncio
    async def test_scan_with_caching(self, tmp_path):
        """Test repository scanning with caching."""
        # Create a simple file
        (tmp_path / "test.py").write_text("# Test file")

        mapper = RepositoryMapper(str(tmp_path))

        # First scan - should analyze files
        repo_map1 = await mapper.scan_repository(use_cache=False)
        assert repo_map1.total_files == 1

        # Second scan - should use cache
        repo_map2 = await mapper.scan_repository(use_cache=True)
        assert repo_map2.total_files == 1
        assert repo_map1.generated_at == repo_map2.generated_at

    @pytest.mark.asyncio
    async def test_scan_medium_repository(self, tmp_path):
        """Test scanning a medium-sized repository."""
        # Create a more complex structure
        directories = ["src", "src/utils", "src/models", "tests", "tests/unit", "tests/integration"]
        for dir_path in directories:
            (tmp_path / dir_path).mkdir(parents=True)

        # Create multiple files
        files_content = {
            "src/main.py": "from utils import helper\nfrom models import User\n\ndef main():\n    pass",
            "src/utils/helper.py": "def helper():\n    return 'help'",
            "src/utils/formatter.py": "def format(data):\n    return str(data)",
            "src/models/user.py": "class User:\n    def __init__(self, name):\n        self.name = name",
            "src/models/base.py": "class BaseModel:\n    pass",
            "tests/unit/test_helper.py": "def test_helper():\n    assert helper() == 'help'",
            "tests/integration/test_models.py": "def test_user():\n    u = User('test')\n    assert u.name == 'test'",
        }

        for file_path, content in files_content.items():
            (tmp_path / file_path).write_text(content)

        mapper = RepositoryMapper(str(tmp_path))
        repo_map = await mapper.scan_repository(use_cache=False)

        assert repo_map.total_files == 7
        assert repo_map.languages["python"] == 7
        assert len(repo_map.entry_points) >= 1
        assert len(repo_map.test_files) >= 2
        assert len(repo_map.dependency_graph) >= 2  # Some files have dependencies

    def test_find_entry_points(self, tmp_path):
        """Test identifying entry points in the codebase."""
        file_nodes = {
            "cli.py": FileNode(
                path="cli.py",
                language="python",
                functions=[FunctionSignature(
                    name="main",
                    module_path="cli",
                    file_path="cli.py",
                    line_start=10,
                    line_end=20
                )]
            ),
            "main.py": FileNode(
                path="main.py",
                language="python",
                functions=[FunctionSignature(
                    name="main",
                    module_path="main",
                    file_path="main.py",
                    line_start=5,
                    line_end=15
                )]
            ),
            "utils.py": FileNode(
                path="utils.py",
                language="python",
                functions=[FunctionSignature(
                    name="helper",
                    module_path="utils",
                    file_path="utils.py",
                    line_start=1,
                    line_end=5
                )]
            ),
        }

        mapper = RepositoryMapper(str(tmp_path))
        entry_points = mapper._find_entry_points(file_nodes)

        assert "cli.py" in entry_points
        assert "main.py" in entry_points
        assert "utils.py" not in entry_points

    def test_find_test_files(self, tmp_path):
        """Test identifying test files."""
        files = [
            tmp_path / "test_main.py",
            tmp_path / "test_utils.py",
            tmp_path / "helper_test.py",
            tmp_path / "tests" / "test_integration.py",
            tmp_path / "test" / "unit_test.py",
            tmp_path / "main.py",  # Not a test file
            tmp_path / "utils.py",  # Not a test file
        ]

        # Create all files
        for file_path in files:
            if file_path.parent != tmp_path:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()

        mapper = RepositoryMapper(str(tmp_path))
        test_files = mapper._find_test_files(files)

        assert "test_main.py" in test_files
        assert "test_utils.py" in test_files
        assert "helper_test.py" in test_files
        assert "tests/test_integration.py" in test_files
        assert "test/unit_test.py" in test_files
        assert "main.py" not in test_files
        assert "utils.py" not in test_files

    def test_count_languages(self, tmp_path):
        """Test counting files by language."""
        file_nodes = {
            "app.py": FileNode(path="app.py", language="python"),
            "utils.py": FileNode(path="utils.py", language="python"),
            "script.js": FileNode(path="script.js", language="javascript"),
            "component.tsx": FileNode(path="component.tsx", language="typescript"),
            "main.go": FileNode(path="main.go", language="go"),
            "lib.rs": FileNode(path="lib.rs", language="rust"),
        }

        mapper = RepositoryMapper(str(tmp_path))
        counts = mapper._count_languages(file_nodes)

        assert counts["python"] == 2
        assert counts["javascript"] == 1
        assert counts["typescript"] == 1
        assert counts["go"] == 1
        assert counts["rust"] == 1


class TestCompressedRepresentation:
    """Test compressed repository representation for AI context."""

    @pytest.mark.asyncio
    async def test_compress_representation_small_repo(self, tmp_path):
        """Test compressing a small repository representation."""
        # Create a simple repository
        (tmp_path / "main.py").write_text("""
def main():
    print("Hello, World!")
""")
        (tmp_path / "utils.py").write_text("""
def helper():
    return "help"
""")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        compressed = mapper.compress_representation(max_tokens=1000)

        assert "PROJECT:" in compressed
        assert "FILES:" in compressed
        assert "LINES:" in compressed
        assert "STRUCTURE:" in compressed
        assert "main.py" in compressed
        assert "utils.py" in compressed

    @pytest.mark.asyncio
    async def test_compress_representation_with_token_limit(self, tmp_path):
        """Test compression respects token limits."""
        # Create many files to exceed token limit
        for i in range(20):
            (tmp_path / f"module_{i}.py").write_text(f"""
# Module {i}
def function_{i}():
    return {i}

class Class{i}:
    def method(self):
        return {i}
""")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        # Very small token limit
        compressed = mapper.compress_representation(max_tokens=100)

        # Should be truncated
        assert "(truncated)" in compressed
        assert len(compressed) < 100 * 4  # Approximate token limit

    @pytest.mark.asyncio
    async def test_get_context_for_file(self, tmp_path):
        """Test getting context for a specific file."""
        # Create files with dependencies
        (tmp_path / "main.py").write_text("""
import utils
from models import User

def main():
    user = User("test")
    utils.helper(user)
""")
        (tmp_path / "utils.py").write_text("""
def helper(user):
    return user
""")
        (tmp_path / "models.py").write_text("""
class User:
    def __init__(self, name):
        self.name = name
""")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        context = mapper.get_context_for_file(str(tmp_path / "main.py"))

        assert "CONTEXT FOR:" in context
        assert "main.py" in context
        assert "IMPORTS:" in context
        assert "utils" in context
        assert "models" in context
        assert "FUNCTIONS:" in context
        assert "main" in context


class TestCaching:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_save_and_load_cache(self, tmp_path):
        """Test saving and loading repository map from cache."""
        # Create a test repository
        (tmp_path / "test.py").write_text("# Test")

        mapper = RepositoryMapper(str(tmp_path))
        repo_map = await mapper.scan_repository(use_cache=False)

        # Save to cache
        mapper._save_cache(repo_map)
        cache_file = mapper.cache_dir / "repo_map.json"
        assert cache_file.exists()

        # Load from cache
        loaded_map = mapper._load_cache()
        assert loaded_map is not None
        assert loaded_map.root_path == repo_map.root_path
        assert loaded_map.total_files == repo_map.total_files
        assert loaded_map.total_lines == repo_map.total_lines

    def test_load_cache_not_found(self, tmp_path):
        """Test loading cache when no cache file exists."""
        mapper = RepositoryMapper(str(tmp_path))
        loaded_map = mapper._load_cache()
        assert loaded_map is None

    def test_load_cache_corrupted(self, tmp_path):
        """Test loading corrupted cache file."""
        cache_dir = tmp_path / ".vibe_cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "repo_map.json"
        cache_file.write_text("invalid json content")

        mapper = RepositoryMapper(str(tmp_path), cache_dir=str(cache_dir))
        loaded_map = mapper._load_cache()
        assert loaded_map is None

    @pytest.mark.asyncio
    async def test_clear_cache(self, tmp_path):
        """Test clearing all caches."""
        # Create repository and scan
        (tmp_path / "test.py").write_text("# Test")
        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        # Verify cache exists
        cache_file = mapper.cache_dir / "repo_map.json"
        assert cache_file.exists()

        # Clear cache
        mapper.clear_cache()

        # Verify cache is gone
        assert not cache_file.exists()
        assert mapper._repo_map is None
        assert len(mapper._file_cache) == 0


class TestIncrementalUpdates:
    """Test incremental updates on file changes."""

    @pytest.mark.asyncio
    async def test_update_on_file_change_modify(self, tmp_path):
        """Test updating cache when file is modified."""
        # Create initial file
        test_file = tmp_path / "test.py"
        test_file.write_text("def original():\n    pass")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        original_map = mapper._repo_map
        assert len(original_map.modules["test.py"].functions) == 1

        # Modify file
        test_file.write_text("def modified():\n    pass\ndef new_function():\n    pass")
        await mapper.update_on_file_change(str(test_file))

        # Check update
        updated_map = mapper._repo_map
        assert len(updated_map.modules["test.py"].functions) == 2
        assert updated_map.generated_at > original_map.generated_at

    @pytest.mark.asyncio
    async def test_update_on_file_change_delete(self, tmp_path):
        """Test updating cache when file is deleted."""
        # Create initial file
        test_file = tmp_path / "test.py"
        test_file.write_text("def test():\n    pass")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        assert "test.py" in mapper._repo_map.modules

        # Delete file
        test_file.unlink()
        await mapper.update_on_file_change(str(test_file))

        # Check update
        assert "test.py" not in mapper._repo_map.modules

    @pytest.mark.asyncio
    async def test_update_on_file_change_nonexistent(self, tmp_path):
        """Test updating when file doesn't exist."""
        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        # Try to update non-existent file
        await mapper.update_on_file_change(str(tmp_path / "nonexistent.py"))

        # Should not raise error
        assert mapper._repo_map is not None


class TestStatisticsAndMonitoring:
    """Test statistics and monitoring functionality."""

    @pytest.mark.asyncio
    async def test_get_stats(self, tmp_path):
        """Test getting repository statistics."""
        # Create a repository
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        (tmp_path / "script.js").write_text("console.log('hello');")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        stats = mapper.get_stats()

        assert stats["status"] != "not_scanned"
        assert stats["root_path"] == str(tmp_path.resolve())
        assert stats["total_files"] == 3
        assert stats["total_lines"] > 0
        assert "python" in stats["languages"]
        assert "javascript" in stats["languages"]
        assert stats["languages"]["python"] == 2
        assert stats["languages"]["javascript"] == 1

    def test_get_stats_not_scanned(self, tmp_path):
        """Test getting stats before repository is scanned."""
        mapper = RepositoryMapper(str(tmp_path))
        stats = mapper.get_stats()

        assert stats["status"] == "not_scanned"

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, tmp_path):
        """Test starting and stopping file monitoring."""
        mapper = RepositoryMapper(str(tmp_path), enable_monitoring=True)

        # Mock file watcher
        with patch('vibe_coder.intelligence.repo_mapper.FileWatcher') as mock_watcher:
            mock_instance = MagicMock()
            mock_watcher.return_value = mock_instance

            # Start monitoring
            mapper.start_monitoring()
            mock_instance.start_monitoring.assert_called_once()

            # Stop monitoring
            mapper.stop_monitoring()
            mock_instance.stop_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_monitoring_disabled(self, tmp_path):
        """Test that monitoring doesn't start when disabled."""
        mapper = RepositoryMapper(str(tmp_path), enable_monitoring=False)

        # Should not create file watcher
        mapper.start_monitoring()
        assert mapper.file_watcher is None


class TestImportanceBasedCompression:
    """Test importance-based repository compression."""

    @pytest.mark.asyncio
    async def test_compress_with_importance_disabled(self, tmp_path):
        """Test compression when importance scoring is disabled."""
        mapper = RepositoryMapper(str(tmp_path), enable_importance_scoring=False)

        # Create test files
        (tmp_path / "main.py").write_text("def main(): pass")
        await mapper.scan_repository(use_cache=False)

        compressed = await mapper.compress_with_importance(max_tokens=1000)

        # Should use original compression method
        assert "PROJECT:" in compressed
        assert "STRUCTURE:" in compressed

    @pytest.mark.asyncio
    async def test_get_context_items(self, tmp_path):
        """Test getting context items for AI operations."""
        # Create test repository
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        # Get context items
        items = await mapper.get_context_items(max_items=10)

        assert len(items) == 2
        for item in items:
            assert item.path in ["main.py", "utils.py"]
            assert item.importance > 0
            assert item.token_count > 0
            assert item.type == "file"
            assert "language" in item.metadata
            assert "lines_of_code" in item.metadata

    @pytest.mark.asyncio
    async def test_get_context_items_with_target(self, tmp_path):
        """Test getting context items with target file."""
        # Create test repository
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        (tmp_path / "target.py").write_text("def target_func(): pass")

        mapper = RepositoryMapper(str(tmp_path))
        await mapper.scan_repository(use_cache=False)

        # Get context items with target
        items = await mapper.get_context_items(
            target_file="target.py",
            operation="fix",
            max_items=10
        )

        assert len(items) == 3
        target_item = next(item for item in items if item.path == "target.py")
        assert target_item is not None