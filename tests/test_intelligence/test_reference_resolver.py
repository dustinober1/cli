"""
Tests for reference resolution functionality.

This module tests the ReferenceResolver class which provides cross-file
symbol tracking and reference resolution.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.intelligence.reference_resolver import ReferenceResolver
from vibe_coder.intelligence.types import (
    ClassSignature,
    Definition,
    FileNode,
    FunctionSignature,
    SymbolReference,
)


class TestReferenceResolverInitialization:
    """Test ReferenceResolver initialization."""

    def test_init(self, tmp_path):
        """Test resolver initialization."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        resolver = ReferenceResolver(mock_mapper)

        assert resolver.repo_mapper == mock_mapper
        assert resolver._symbol_index == {}
        assert resolver._reference_index == {}
        assert resolver._import_map == {}
        assert resolver._dirty_files == set()


class TestDefinitionIndexing:
    """Test symbol definition indexing."""

    @pytest.mark.asyncio
    async def test_index_function_definitions(self, tmp_path):
        """Test indexing function definitions."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        resolver = ReferenceResolver(mock_mapper)

        # Create file node with functions
        func1 = FunctionSignature(
            name="test_function",
            module_path="test",
            file_path="test.py",
            line_start=10,
            line_end=20,
            docstring="Test function",
        )
        func2 = FunctionSignature(
            name="another_function",
            module_path="test",
            file_path="test.py",
            line_start=30,
            line_end=40,
        )

        node = FileNode(path="test.py", language="python", functions=[func1, func2], classes=[])

        await resolver._index_definitions("test.py", node)

        # Check functions were indexed
        assert "test_function" in resolver._symbol_index
        assert "another_function" in resolver._symbol_index

        # Check definition details
        test_def = resolver._symbol_index["test_function"][0]
        assert test_def.symbol == "test_function"
        assert test_def.file_path == "test.py"
        assert test_def.line_number == 10
        assert test_def.type == "function"
        assert test_def.docstring == "Test function"

    @pytest.mark.asyncio
    async def test_index_class_definitions(self, tmp_path):
        """Test indexing class definitions."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        resolver = ReferenceResolver(mock_mapper)

        # Create file node with class
        cls = ClassSignature(
            name="TestClass",
            module_path="test",
            file_path="test.py",
            line_start=5,
            line_end=25,
            docstring="Test class",
        )

        node = FileNode(path="test.py", language="python", functions=[], classes=[cls])

        await resolver._index_definitions("test.py", node)

        # Check class was indexed
        assert "TestClass" in resolver._symbol_index

        # Check definition details
        class_def = resolver._symbol_index["TestClass"][0]
        assert class_def.symbol == "TestClass"
        assert class_def.file_path == "test.py"
        assert class_def.line_number == 5
        assert class_def.type == "class"
        assert class_def.docstring == "Test class"

    @pytest.mark.asyncio
    async def test_index_method_definitions(self, tmp_path):
        """Test indexing method definitions."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        resolver = ReferenceResolver(mock_mapper)

        # Create file node with class and methods
        method1 = FunctionSignature(
            name="method1",
            module_path="test",
            file_path="test.py",
            line_start=15,
            line_end=20,
            is_method=True,
        )
        method2 = FunctionSignature(
            name="method2",
            module_path="test",
            file_path="test.py",
            line_start=25,
            line_end=30,
            is_method=True,
        )

        cls = ClassSignature(
            name="TestClass",
            module_path="test",
            file_path="test.py",
            line_start=5,
            line_end=35,
            methods=[method1, method2],
        )

        node = FileNode(path="test.py", language="python", functions=[], classes=[cls])

        await resolver._index_definitions("test.py", node)

        # Check methods were indexed with qualified names
        assert "TestClass.method1" in resolver._symbol_index
        assert "TestClass.method2" in resolver._symbol_index

        # Check method definition details
        method_def = resolver._symbol_index["TestClass.method1"][0]
        assert method_def.symbol == "TestClass.method1"
        assert method_def.file_path == "test.py"
        assert method_def.line_number == 15
        assert method_def.type == "method"

    @pytest.mark.asyncio
    async def test_index_multiple_definitions_same_symbol(self, tmp_path):
        """Test indexing multiple definitions of the same symbol."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        resolver = ReferenceResolver(mock_mapper)

        # Create two files with functions of the same name
        func1 = FunctionSignature(
            name="helper", module_path="utils1", file_path="utils1.py", line_start=1, line_end=10
        )
        func2 = FunctionSignature(
            name="helper", module_path="utils2", file_path="utils2.py", line_start=1, line_end=10
        )

        node1 = FileNode(path="utils1.py", language="python", functions=[func1], classes=[])
        node2 = FileNode(path="utils2.py", language="python", functions=[func2], classes=[])

        await resolver._index_definitions("utils1.py", node1)
        await resolver._index_definitions("utils2.py", node2)

        # Check both definitions were indexed
        assert "helper" in resolver._symbol_index
        assert len(resolver._symbol_index["helper"]) == 2

        # Check both files are represented
        file_paths = [defn.file_path for defn in resolver._symbol_index["helper"]]
        assert "utils1.py" in file_paths
        assert "utils2.py" in file_paths


class TestImportResolution:
    """Test import resolution functionality."""

    @pytest.mark.asyncio
    async def test_resolve_import_path_module(self, tmp_path):
        """Test resolving import path to module file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "package/module.py": MagicMock(),
            "other/file.py": MagicMock(),
        }

        resolver = ReferenceResolver(mock_mapper)

        resolved = await resolver._resolve_import_path("package.module", "")
        assert resolved == "package/module.py"

    @pytest.mark.asyncio
    async def test_resolve_import_path_package(self, tmp_path):
        """Test resolving import path to package."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "package/__init__.py": MagicMock(),
            "other/file.py": MagicMock(),
        }

        resolver = ReferenceResolver(mock_mapper)

        resolved = await resolver._resolve_import_path("package", "")
        assert resolved == "package/__init__.py"

    @pytest.mark.asyncio
    async def test_resolve_import_path_relative(self, tmp_path):
        """Test resolving relative import path."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "sibling.py": MagicMock(),
            "parent/child.py": MagicMock(),
            "parent/__init__.py": MagicMock(),
        }

        resolver = ReferenceResolver(mock_mapper)

        # Test relative import from subdirectory
        resolved = await resolver._resolve_import_path("..sibling", "sub/dir")
        assert resolved == "sibling.py"

        # Test relative import to parent package
        resolved = await resolver._resolve_import_path("..", "sub/dir")
        assert resolved == "parent/__init__.py"

    @pytest.mark.asyncio
    async def test_resolve_import_path_not_found(self, tmp_path):
        """Test resolving import path that doesn't exist."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {}

        resolver = ReferenceResolver(mock_mapper)

        resolved = await resolver._resolve_import_path("nonexistent.module", "")
        assert resolved is None

    @pytest.mark.asyncio
    async def test_resolve_imports(self, tmp_path):
        """Test building import map from repository."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils.helper", "models"]),
            "utils/helper.py": MagicMock(imports=[]),
            "models/__init__.py": MagicMock(imports=[]),
        }

        resolver = ReferenceResolver(mock_mapper)

        with patch.object(resolver, "_resolve_import_path") as mock_resolve:
            mock_resolve.side_effect = lambda imp, dir: {
                "utils.helper": "utils/helper.py",
                "models": "models/__init__.py",
            }.get(imp)

            await resolver._resolve_imports()

            assert resolver._import_map["utils.helper"] == "utils/helper.py"
            assert resolver._import_map["models"] == "models/__init__.py"


class TestReferenceIndexing:
    """Test symbol reference indexing."""

    @pytest.mark.asyncio
    async def test_index_references_with_imports(self, tmp_path):
        """Test indexing references from imports."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils", "models"]),
            "utils.py": MagicMock(),
            "models.py": MagicMock(),
        }

        resolver = ReferenceResolver(mock_mapper)
        resolver._import_map = {
            "utils": "utils.py",
            "models": "models.py",
        }

        # Mock the indexed modules to have symbols
        utils_node = MagicMock()
        utils_node.functions = [MagicMock(name="helper")]
        utils_node.classes = [MagicMock(name="HelperClass")]
        mock_mapper._repo_map.modules["utils.py"] = utils_node

        await resolver._index_references("main.py", mock_mapper._repo_map.modules["main.py"])

        # Check references were created
        assert "main.py" in resolver._reference_index
        references = resolver._reference_index["main.py"]
        assert len(references) >= 3  # utils, helper, HelperClass

        # Check reference details
        ref_names = [ref.name for ref in references]
        assert "utils" in ref_names
        assert "helper" in ref_names
        assert "HelperClass" in ref_names

    @pytest.mark.asyncio
    async def test_index_references_no_imports(self, tmp_path):
        """Test indexing references when no imports."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "standalone.py": MagicMock(imports=[]),
        }

        resolver = ReferenceResolver(mock_mapper)

        await resolver._index_references(
            "standalone.py", mock_mapper._repo_map.modules["standalone.py"]
        )

        # Should still create entry for the file
        assert "standalone.py" in resolver._reference_index
        # But no references
        assert len(resolver._reference_index["standalone.py"]) == 0


class TestBuildIndexes:
    """Test building complete symbol and reference indexes."""

    @pytest.mark.asyncio
    async def test_build_indexes_complete(self, tmp_path):
        """Test building complete indexes for repository."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils"]),
            "utils.py": MagicMock(imports=[]),
        }

        # Add functions and classes to nodes
        main_func = FunctionSignature(
            name="main", module_path="main", file_path="main.py", line_start=1, line_end=10
        )
        utils_func = FunctionSignature(
            name="helper", module_path="utils", file_path="utils.py", line_start=1, line_end=10
        )

        mock_mapper._repo_map.modules["main.py"].functions = [main_func]
        mock_mapper._repo_map.modules["main.py"].classes = []
        mock_mapper._repo_map.modules["utils.py"].functions = [utils_func]
        mock_mapper._repo_map.modules["utils.py"].classes = []

        resolver = ReferenceResolver(mock_mapper)

        with (
            patch.object(resolver, "_resolve_import_path") as mock_resolve,
            patch.object(resolver, "_index_references") as mock_index_refs,
        ):
            mock_resolve.return_value = "utils.py"

            await resolver.build_indexes()

            # Check definitions were indexed
            assert "main" in resolver._symbol_index
            assert "helper" in resolver._symbol_index

            # Check import map was built
            assert "utils" in resolver._import_map
            assert resolver._import_map["utils"] == "utils.py"

            # Check references were indexed
            mock_index_refs.assert_called()

    @pytest.mark.asyncio
    async def test_build_indexes_no_repo_map(self, tmp_path):
        """Test building indexes when no repository map exists."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None
        mock_mapper.scan_repository = AsyncMock()

        resolver = ReferenceResolver(mock_mapper)

        await resolver.build_indexes()

        # Should have scanned repository
        mock_mapper.scan_repository.assert_called_once()


class TestFindReferences:
    """Test finding symbol references."""

    @pytest.mark.asyncio
    async def test_find_references_all_files(self, tmp_path):
        """Test finding references across all files."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup reference index
        ref1 = SymbolReference(
            name="helper",
            file_path="main.py",
            line_number=5,
            column=10,
            reference_type="usage",
            context="helper()",
            symbol_type="function",
        )
        ref2 = SymbolReference(
            name="helper",
            file_path="other.py",
            line_number=3,
            column=5,
            reference_type="usage",
            context="helper()",
            symbol_type="function",
        )
        ref3 = SymbolReference(
            name="other_func",
            file_path="main.py",
            line_number=10,
            column=1,
            reference_type="usage",
            context="other_func()",
            symbol_type="function",
        )

        resolver._reference_index = {
            "main.py": [ref1, ref3],
            "other.py": [ref2],
        }

        references = await resolver.find_references("helper")

        assert len(references) == 2
        assert ref1 in references
        assert ref2 in references
        assert ref3 not in references

    @pytest.mark.asyncio
    async def test_find_references_specific_file(self, tmp_path):
        """Test finding references in a specific file."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup reference index
        ref1 = SymbolReference(
            name="target",
            file_path="main.py",
            line_number=5,
            column=10,
            reference_type="usage",
            context="target()",
            symbol_type="function",
        )
        ref2 = SymbolReference(
            name="target",
            file_path="other.py",
            line_number=3,
            column=5,
            reference_type="usage",
            context="target()",
            symbol_type="function",
        )

        resolver._reference_index = {
            "main.py": [ref1],
            "other.py": [ref2],
        }

        references = await resolver.find_references("target", file_path="main.py")

        assert len(references) == 1
        assert references[0] == ref1

    @pytest.mark.asyncio
    async def test_find_references_qualified_names(self, tmp_path):
        """Test finding references with qualified names."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup reference index
        ref1 = SymbolReference(
            name="Class.method",
            file_path="main.py",
            line_number=5,
            column=10,
            reference_type="usage",
            context="Class.method()",
            symbol_type="method",
        )

        resolver._reference_index = {
            "main.py": [ref1],
        }

        # Should find by full qualified name
        references = await resolver.find_references("Class.method")
        assert len(references) == 1

        # Should also find by method name part
        references = await resolver.find_references("method")
        assert len(references) == 1


class TestFindDefinition:
    """Test finding symbol definitions."""

    @pytest.mark.asyncio
    async def test_find_definition_single(self, tmp_path):
        """Test finding a symbol with single definition."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup symbol index
        definition = Definition(
            symbol="target_func",
            file_path="utils.py",
            line_number=10,
            column=4,
            type="function",
            signature="target_func()",
            docstring="Target function",
        )

        resolver._symbol_index = {
            "target_func": [definition],
        }

        found = await resolver.find_definition("target_func")

        assert found == definition

    @pytest.mark.asyncio
    async def test_find_definition_multiple_same_file(self, tmp_path):
        """Test finding symbol when multiple definitions exist, prefer same file."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup symbol index with multiple definitions
        def1 = Definition(
            symbol="helper", file_path="main.py", line_number=5, column=4, type="function"
        )
        def2 = Definition(
            symbol="helper", file_path="utils.py", line_number=10, column=4, type="function"
        )

        resolver._symbol_index = {
            "helper": [def1, def2],
        }

        # Search from main.py should find main.py definition
        found = await resolver.find_definition("helper", from_file="main.py")
        assert found == def1

    @pytest.mark.asyncio
    async def test_find_definition_multiple_imported(self, tmp_path):
        """Test finding symbol when multiple definitions exist, prefer imported."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils"]),
        }

        resolver = ReferenceResolver(mock_mapper)

        # Setup symbol index with multiple definitions
        def1 = Definition(
            symbol="helper", file_path="other.py", line_number=5, column=4, type="function"
        )
        def2 = Definition(
            symbol="helper", file_path="utils.py", line_number=10, column=4, type="function"
        )

        resolver._symbol_index = {
            "helper": [def1, def2],
        }
        resolver._import_map = {
            "utils": "utils.py",
        }

        # Search from main.py should find utils.py definition (imported)
        found = await resolver.find_definition("helper", from_file="main.py")
        assert found == def2

    @pytest.mark.asyncio
    async def test_find_definition_method(self, tmp_path):
        """Test finding method definition using qualified name."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup symbol index with class and method
        class_def = Definition(
            symbol="MyClass", file_path="class.py", line_number=5, column=4, type="class"
        )
        method_def = Definition(
            symbol="MyClass.method", file_path="class.py", line_number=15, column=8, type="method"
        )

        resolver._symbol_index = {
            "MyClass": [class_def],
            "MyClass.method": [method_def],
        }

        found = await resolver.find_definition("MyClass.method")
        assert found == method_def

    @pytest.mark.asyncio
    async def test_find_definition_not_found(self, tmp_path):
        """Test finding definition that doesn't exist."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        resolver._symbol_index = {}

        found = await resolver.find_definition("nonexistent")
        assert found is None


class TestDependencies:
    """Test dependency analysis functionality."""

    @pytest.mark.asyncio
    async def test_get_dependencies_direct(self, tmp_path):
        """Test getting direct dependencies."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils", "models"]),
        }

        resolver = ReferenceResolver(mock_mapper)
        resolver._import_map = {
            "utils": "utils.py",
            "models": "models.py",
        }

        deps = await resolver.get_dependencies("main.py")

        assert len(deps) == 2
        assert "utils.py" in deps
        assert "models.py" in deps

    @pytest.mark.asyncio
    async def test_get_dependencies_with_indirect(self, tmp_path):
        """Test getting dependencies including indirect ones."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils"]),
            "utils.py": MagicMock(imports=["base"]),
        }

        resolver = ReferenceResolver(mock_mapper)
        resolver._import_map = {
            "utils": "utils.py",
            "base": "base.py",
        }

        # Mock get_dependencies for indirect calls
        async def mock_get_deps(file_path, include_indirect=False):
            if file_path == "utils.py" and include_indirect:
                return ["base.py"]
            return []

        resolver.get_dependencies = mock_get_deps

        deps = await resolver.get_dependencies("main.py", include_indirect=True)

        assert len(deps) == 2
        assert "utils.py" in deps
        assert "base.py" in deps

    @pytest.mark.asyncio
    async def test_get_dependencies_file_not_found(self, tmp_path):
        """Test getting dependencies for non-existent file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {}

        resolver = ReferenceResolver(mock_mapper)

        deps = await resolver.get_dependencies("nonexistent.py")
        assert deps == []

    @pytest.mark.asyncio
    async def test_get_dependents(self, tmp_path):
        """Test getting files that depend on a given file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils"]),
            "other.py": MagicMock(imports=["utils"]),
            "utils.py": MagicMock(imports=[]),
            "standalone.py": MagicMock(imports=[]),
        }

        resolver = ReferenceResolver(mock_mapper)
        resolver._import_map = {
            "utils": "utils.py",
        }

        dependents = await resolver.get_dependents("utils.py")

        assert len(dependents) == 2
        assert "main.py" in dependents
        assert "other.py" in dependents
        assert "standalone.py" not in dependents

    @pytest.mark.asyncio
    async def test_get_dependents_no_repo_map(self, tmp_path):
        """Test getting dependents when no repository map."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        resolver = ReferenceResolver(mock_mapper)

        dependents = await resolver.get_dependents("any.py")
        assert dependents == []


class TestSymbolStatistics:
    """Test symbol statistics functionality."""

    def test_get_symbol_statistics(self, tmp_path):
        """Test getting comprehensive symbol statistics."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        # Setup symbol index
        resolver._symbol_index = {
            "func1": [Definition("func1", "file1.py", 1, 0, "function")],
            "func2": [Definition("func2", "file2.py", 1, 0, "function")],
            "class1": [Definition("class1", "file1.py", 10, 0, "class")],
            "helper": [
                Definition("helper", "file1.py", 20, 0, "function"),
                Definition("helper", "file2.py", 30, 0, "function"),
            ],
        }

        # Setup reference index
        resolver._reference_index = {
            "file1.py": [
                SymbolReference("func1", "file1.py", 5, 10, "usage", "func1()", "function"),
                SymbolReference("helper", "file1.py", 15, 10, "usage", "helper()", "function"),
                SymbolReference("helper", "file1.py", 25, 10, "usage", "helper()", "function"),
            ],
            "file2.py": [
                SymbolReference("func2", "file2.py", 5, 10, "usage", "func2()", "function"),
                SymbolReference("helper", "file2.py", 10, 10, "usage", "helper()", "function"),
                SymbolReference("class1", "file2.py", 20, 10, "usage", "Class1()", "class"),
            ],
        }

        stats = resolver.get_symbol_statistics()

        assert stats["total_symbols"] == 4  # func1, func2, class1, helper
        assert stats["total_definitions"] == 5  # helper has 2 definitions
        assert stats["total_references"] == 6

        # Check most referenced
        most_ref = stats["most_referenced_symbols"]
        # helper should be most referenced (3 times)
        assert most_ref[0] == ("helper", 3)

    def test_get_symbol_statistics_empty(self, tmp_path):
        """Test getting statistics when no symbols indexed."""
        mock_mapper = MagicMock()
        resolver = ReferenceResolver(mock_mapper)

        resolver._symbol_index = {}
        resolver._reference_index = {}

        stats = resolver.get_symbol_statistics()

        assert stats["total_symbols"] == 0
        assert stats["total_definitions"] == 0
        assert stats["total_references"] == 0
        assert stats["most_referenced_symbols"] == []


class TestIntegration:
    """Integration tests for reference resolution."""

    @pytest.mark.asyncio
    async def test_end_to_end_resolution(self, tmp_path):
        """Test end-to-end reference resolution workflow."""
        # Create mock repository
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(imports=["utils"]),
            "utils.py": MagicMock(imports=[]),
        }

        # Add functions to modules
        main_func = FunctionSignature(
            name="main", module_path="main", file_path="main.py", line_start=1, line_end=10
        )
        utils_func = FunctionSignature(
            name="helper", module_path="utils", file_path="utils.py", line_start=1, line_end=10
        )

        mock_mapper._repo_map.modules["main.py"].functions = [main_func]
        mock_mapper._repo_map.modules["main.py"].classes = []
        mock_mapper._repo_map.modules["utils.py"].functions = [utils_func]
        mock_mapper._repo_map.modules["utils.py"].classes = []

        # Create resolver and build indexes
        resolver = ReferenceResolver(mock_mapper)

        with patch.object(resolver, "_resolve_import_path") as mock_resolve:
            mock_resolve.return_value = "utils.py"

            await resolver.build_indexes()

        # Test finding definition
        def_found = await resolver.find_definition("helper")
        assert def_found is not None
        assert def_found.symbol == "helper"
        assert def_found.file_path == "utils.py"

        # Test finding references
        refs = await resolver.find_references("helper")
        assert len(refs) >= 1

        # Test dependencies
        deps = await resolver.get_dependencies("main.py")
        assert "utils.py" in deps

        # Test dependents
        dependents = await resolver.get_dependents("utils.py")
        assert "main.py" in dependents
