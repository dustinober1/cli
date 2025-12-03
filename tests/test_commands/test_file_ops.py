"""Tests for file operations utilities."""

import pytest
import tempfile
import shutil
from pathlib import Path

from vibe_coder.commands.slash.file_ops import FileOperations


class TestFileOperations:
    """Test the FileOperations class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def file_ops(self, temp_dir):
        """Create FileOperations instance with temp directory."""
        return FileOperations(temp_dir)

    def test_get_absolute_path(self, file_ops, temp_dir):
        """Test getting absolute path from relative path."""
        # Relative path
        result = file_ops.get_absolute_path("test.txt")
        assert str(result) == str(Path(temp_dir) / "test.txt")

        # Absolute path
        abs_path = "/absolute/path/test.txt"
        result = file_ops.get_absolute_path(abs_path)
        assert str(result) == str(Path(abs_path))

    async def test_read_write_file(self, file_ops):
        """Test reading and writing files."""
        content = "Test content for file operations"
        filename = "test_file.txt"

        # Write file
        success = await file_ops.write_file(filename, content)
        assert success is True

        # Check file exists
        file_path = file_ops.get_absolute_path(filename)
        assert file_path.exists()

        # Read file
        read_content = await file_ops.read_file(filename)
        assert read_content == content

    async def test_write_file_with_backup(self, file_ops):
        """Test writing file with backup creation."""
        filename = "backup_test.txt"
        initial_content = "Initial content"
        updated_content = "Updated content"

        # Write initial file
        await file_ops.write_file(filename, initial_content, backup=True)

        # Write updated file (should create backup)
        await file_ops.write_file(filename, updated_content, backup=True)

        # Check backup was created
        backup_dir = file_ops.backup_dir
        backup_files = list(backup_dir.glob(f"{filename}_*"))
        assert len(backup_files) > 0

        # Check current content is updated
        current_content = await file_ops.read_file(filename)
        assert current_content == updated_content

    async def test_read_nonexistent_file(self, file_ops):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            await file_ops.read_file("nonexistent.txt")

    async def test_write_file_create_dirs(self, file_ops):
        """Test writing file with directory creation."""
        filename = "subdir/nested/file.txt"
        content = "Test content in nested directory"

        success = await file_ops.write_file(filename, content, create_dirs=True)
        assert success is True

        # Check file and directory were created
        file_path = file_ops.get_absolute_path(filename)
        assert file_path.exists()
        assert file_path.parent.exists()

    async def test_analyze_file_text(self, file_ops):
        """Test analyzing a text file."""
        content = """def hello_world():
    print("Hello, World!")
    return "Hello"

hello_world()
"""
        filename = "test.py"
        await file_ops.write_file(filename, content)

        analysis = file_ops.analyze_file(filename)

        assert analysis["name"] == filename
        assert analysis["size"] == len(content)
        assert analysis["file_type"] == "python"
        assert analysis["line_count"] == 4
        assert analysis["is_file"] is True
        assert analysis["encoding"] == "utf-8"
        assert "hash" in analysis

        # Python-specific analysis
        assert analysis["functions"] == 1

    async def test_analyze_file_binary(self, file_ops):
        """Test analyzing a binary file."""
        filename = "test.bin"
        binary_content = b'\x00\x01\x02\x03\x04\x05'

        # Write binary content directly
        file_path = file_ops.get_absolute_path(filename)
        with open(file_path, 'wb') as f:
            f.write(binary_content)

        analysis = file_ops.analyze_file(filename)

        assert analysis["name"] == filename
        assert analysis["size"] == len(binary_content)
        assert analysis["is_file"] is True
        assert analysis["encoding"] == "binary"

    def test_analyze_nonexistent_file(self, file_ops):
        """Test analyzing non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            file_ops.analyze_file("nonexistent.txt")

    def test_detect_file_type(self, file_ops):
        """Test file type detection."""
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.jsx", "jsx"),
            ("test.tsx", "tsx"),
            ("test.java", "java"),
            ("test.cpp", "cpp"),
            ("test.c", "c"),
            ("test.html", "html"),
            ("test.css", "css"),
            ("test.json", "json"),
            ("test.md", "markdown"),
            ("test.yaml", "yaml"),
            ("test.yml", "yaml"),
            ("unknown.xyz", "unknown"),
        ]

        for filename, expected_type in test_cases:
            path = Path(filename)
            detected_type = file_ops._detect_file_type(path)
            assert detected_type == expected_type, f"Failed for {filename}"

    def test_is_text_file(self, file_ops):
        """Test text file detection."""
        text_files = [
            "test.py", "test.js", "test.ts", "test.html", "test.css",
            "test.json", "test.md", "test.yaml", "test.txt", "test.csv"
        ]

        binary_files = [
            "test.png", "test.jpg", "test.mp3", "test.mp4", "test.zip"
        ]

        for filename in text_files:
            path = Path(filename)
            assert file_ops._is_text_file(path), f"Should be text: {filename}"

        for filename in binary_files:
            path = Path(filename)
            assert not file_ops._is_text_file(path), f"Should not be text: {filename}"

    def test_list_files_basic(self, file_ops, temp_dir):
        """Test basic file listing."""
        # Create test files
        test_files = ["test1.txt", "test2.py", "subdir/test3.js"]
        for filename in test_files:
            file_path = Path(temp_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("test content")

        # List all files
        files = file_ops.list_files()
        files_set = set(files)
        assert "test1.txt" in files_set
        assert "test2.py" in files_set

        # List with pattern
        py_files = file_ops.list_files(pattern="*.py")
        assert py_files == ["test2.py"]

    def test_list_files_recursive(self, file_ops, temp_dir):
        """Test recursive file listing."""
        # Create nested structure
        nested_files = ["test.txt", "subdir/test.py", "subdir/nested/test.js"]
        for filename in nested_files:
            file_path = Path(temp_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("test content")

        # Non-recursive
        files = file_ops.list_files(recursive=False)
        assert "test.txt" in files
        assert "subdir/test.py" not in files

        # Recursive
        files = file_ops.list_files(recursive=True)
        files_set = set(files)
        assert "test.txt" in files_set
        assert "subdir/test.py" in files_set
        assert "subdir/nested/test.js" in files_set

    def test_get_file_tree(self, file_ops, temp_dir):
        """Test generating file tree."""
        # Create test structure
        structure = {
            "root.txt": "root file",
            "subdir/": {
                "nested.txt": "nested file",
                "deep/": {
                    "deepest.txt": "deepest file"
                }
            }
        }

        def create_structure(base_path, structure):
            for name, content in structure.items():
                path = base_path / name
                if name.endswith("/"):
                    path.mkdir(parents=True, exist_ok=True)
                    create_structure(path, content)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)

        create_structure(Path(temp_dir), structure)

        # Get file tree with max depth 2
        tree = file_ops.get_file_tree(max_depth=2)

        assert tree["name"] == Path(temp_dir).name
        assert tree["type"] == "directory"

        # Find files in tree
        def find_files(node, files_found):
            if node["type"] == "file":
                files_found.append(node["name"])
            elif "children" in node:
                for child in node["children"]:
                    find_files(child, files_found)

        files_found = []
        find_files(tree, files_found)

        assert "root.txt" in files_found
        assert "nested.txt" in files_found

    def test_analyze_code_file_python(self, file_ops):
        """Test Python code analysis."""
        code = '''
import os
import sys
from typing import Optional

class TestClass:
    """A test class."""

    def __init__(self):
        self.value = 42

    def get_value(self) -> int:
        """Get the value."""
        return self.value

    @staticmethod
    def static_method():
        """A static method."""
        pass

def main():
    """Main function."""
    test = TestClass()
    # This is a comment
    print(test.get_value())

if __name__ == "__main__":
    main()
'''

        lines = code.splitlines()
        analysis = file_ops._analyze_python_code(code, lines)

        assert analysis["classes"] == 1
        assert analysis["functions"] >= 2  # main and static_method
        assert analysis["imports"] >= 2   # os and sys
        assert analysis["comments"] >= 1
        assert analysis["docstrings"] >= 2

    def test_analyze_code_file_javascript(self, file_ops):
        """Test JavaScript code analysis."""
        code = '''
import React from 'react';
import { useState } from 'hooks';

export class TestClass {
    constructor() {
        this.value = 42;
    }

    getValue() {
        return this.value;
    }
}

const testFunction = () => {
    console.log("test");
    return "result";
};

export default testFunction;
'''

        lines = code.splitlines()
        analysis = file_ops._analyze_javascript_code(code, lines)

        assert analysis["classes"] >= 1
        assert analysis["functions"] >= 1
        assert analysis["imports"] >= 2
        assert analysis["exports"] >= 1
        assert analysis["comments"] >= 0  # No comments in this code