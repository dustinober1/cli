"""Tests for intelligence types."""

from vibe_coder.intelligence.types import ClassSignature, FileNode, FunctionSignature, RepositoryMap


class TestFunctionSignature:
    """Tests for FunctionSignature dataclass."""

    def test_create_function_signature(self):
        """Test creating a function signature."""
        func = FunctionSignature(
            name="test_func",
            module_path="test.module",
            file_path="/path/to/file.py",
            line_start=10,
            line_end=20,
            parameters=["arg1", "arg2: int"],
            return_type="str",
            docstring="Test function",
            complexity=3,
            is_async=True,
            is_method=False,
            decorators=["staticmethod"],
        )

        assert func.name == "test_func"
        assert func.module_path == "test.module"
        assert func.line_start == 10
        assert func.line_end == 20
        assert len(func.parameters) == 2
        assert func.return_type == "str"
        assert func.is_async is True
        assert func.complexity == 3

    def test_function_signature_defaults(self):
        """Test FunctionSignature with default values."""
        func = FunctionSignature(
            name="simple",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=5,
        )

        assert func.parameters == []
        assert func.return_type is None
        assert func.docstring is None
        assert func.complexity == 1
        assert func.is_async is False
        assert func.is_method is False
        assert func.decorators == []

    def test_function_signature_to_dict(self):
        """Test serialization to dictionary."""
        func = FunctionSignature(
            name="test",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=5,
            parameters=["x"],
            return_type="int",
        )

        data = func.to_dict()
        assert data["name"] == "test"
        assert data["parameters"] == ["x"]
        assert data["return_type"] == "int"

    def test_function_signature_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "loaded",
            "module_path": "mod",
            "file_path": "/path.py",
            "line_start": 1,
            "line_end": 10,
            "parameters": ["a", "b"],
            "return_type": "bool",
            "complexity": 5,
        }

        func = FunctionSignature.from_dict(data)
        assert func.name == "loaded"
        assert func.complexity == 5
        assert len(func.parameters) == 2

    def test_function_signature_str(self):
        """Test string representation."""
        func = FunctionSignature(
            name="my_func",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=5,
            parameters=["x: int", "y: str"],
            return_type="bool",
        )

        result = str(func)
        assert "my_func" in result
        assert "x: int" in result
        assert "-> bool" in result

    def test_async_function_str(self):
        """Test string representation of async function."""
        func = FunctionSignature(
            name="async_func",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=5,
            is_async=True,
        )

        result = str(func)
        assert "async " in result


class TestClassSignature:
    """Tests for ClassSignature dataclass."""

    def test_create_class_signature(self):
        """Test creating a class signature."""
        method = FunctionSignature(
            name="method",
            module_path="mod",
            file_path="/path.py",
            line_start=5,
            line_end=10,
            is_method=True,
        )

        cls = ClassSignature(
            name="TestClass",
            module_path="test.module",
            file_path="/path/to/file.py",
            line_start=1,
            line_end=50,
            bases=["BaseClass"],
            methods=[method],
            attributes=["attr1: str", "attr2"],
            docstring="A test class",
            decorators=["dataclass"],
            is_dataclass=True,
        )

        assert cls.name == "TestClass"
        assert len(cls.bases) == 1
        assert len(cls.methods) == 1
        assert len(cls.attributes) == 2
        assert cls.is_dataclass is True

    def test_class_signature_to_dict(self):
        """Test serialization to dictionary."""
        cls = ClassSignature(
            name="MyClass",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=20,
            bases=["Parent"],
        )

        data = cls.to_dict()
        assert data["name"] == "MyClass"
        assert data["bases"] == ["Parent"]

    def test_class_signature_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "LoadedClass",
            "module_path": "mod",
            "file_path": "/path.py",
            "line_start": 1,
            "line_end": 30,
            "bases": ["A", "B"],
            "methods": [],
            "attributes": ["x"],
        }

        cls = ClassSignature.from_dict(data)
        assert cls.name == "LoadedClass"
        assert len(cls.bases) == 2

    def test_class_signature_str(self):
        """Test string representation."""
        cls = ClassSignature(
            name="MyClass",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=20,
            bases=["Parent", "Mixin"],
        )

        result = str(cls)
        assert "class MyClass" in result
        assert "Parent" in result


class TestFileNode:
    """Tests for FileNode dataclass."""

    def test_create_file_node(self):
        """Test creating a file node."""
        func = FunctionSignature(
            name="func",
            module_path="mod",
            file_path="/path.py",
            line_start=1,
            line_end=5,
        )

        node = FileNode(
            path="/path/to/file.py",
            language="python",
            lines_of_code=100,
            functions=[func],
            classes=[],
            imports=["os", "sys"],
            dependencies={"os", "requests"},
            type_hints_coverage=75.5,
            has_docstring=True,
        )

        assert node.path == "/path/to/file.py"
        assert node.language == "python"
        assert node.lines_of_code == 100
        assert len(node.functions) == 1
        assert len(node.imports) == 2
        assert "requests" in node.dependencies

    def test_file_node_to_dict(self):
        """Test serialization to dictionary."""
        node = FileNode(
            path="/path.py",
            language="python",
            lines_of_code=50,
            dependencies={"numpy"},
        )

        data = node.to_dict()
        assert data["path"] == "/path.py"
        assert data["language"] == "python"
        assert "numpy" in data["dependencies"]

    def test_file_node_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "path": "/loaded.py",
            "language": "python",
            "lines_of_code": 200,
            "functions": [],
            "classes": [],
            "imports": ["json"],
            "dependencies": ["requests"],
            "type_hints_coverage": 80.0,
        }

        node = FileNode.from_dict(data)
        assert node.path == "/loaded.py"
        assert node.lines_of_code == 200
        assert "requests" in node.dependencies


class TestRepositoryMap:
    """Tests for RepositoryMap dataclass."""

    def test_create_repository_map(self):
        """Test creating a repository map."""
        node = FileNode(
            path="/path.py",
            language="python",
            lines_of_code=100,
        )

        repo = RepositoryMap(
            root_path="/project",
            total_files=10,
            total_lines=1000,
            languages={"python": 8, "javascript": 2},
            modules={"/path.py": node},
            dependency_graph={"/path.py": {"/other.py"}},
            entry_points=["/main.py"],
            test_files=["/test_main.py"],
        )

        assert repo.root_path == "/project"
        assert repo.total_files == 10
        assert repo.total_lines == 1000
        assert repo.languages["python"] == 8
        assert len(repo.modules) == 1

    def test_repository_map_to_dict(self):
        """Test serialization to dictionary."""
        repo = RepositoryMap(
            root_path="/project",
            total_files=5,
            total_lines=500,
        )

        data = repo.to_dict()
        assert data["root_path"] == "/project"
        assert "generated_at" in data

    def test_repository_map_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "root_path": "/loaded",
            "total_files": 20,
            "total_lines": 2000,
            "languages": {"python": 15, "go": 5},
            "modules": {},
            "dependency_graph": {},
            "entry_points": [],
            "test_files": [],
            "generated_at": "2024-01-01T00:00:00",
        }

        repo = RepositoryMap.from_dict(data)
        assert repo.root_path == "/loaded"
        assert repo.total_files == 20
        assert repo.languages["go"] == 5

    def test_repository_map_summary(self):
        """Test get_summary method."""
        repo = RepositoryMap(
            root_path="/my-project",
            total_files=15,
            total_lines=1500,
            languages={"python": 10, "javascript": 5},
            entry_points=["/main.py"],
        )

        summary = repo.get_summary()
        assert "my-project" in summary
        assert "15" in summary
        assert "python" in summary.lower()
