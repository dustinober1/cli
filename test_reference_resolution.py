#!/usr/bin/env python3
"""Test reference resolution functionality."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.reference_resolver import ReferenceResolver


async def test_reference_resolution():
    """Test reference resolution and symbol tracking."""
    print("Starting reference resolution test...")

    # Create a temporary repository with multiple Python files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file A with exports
        file_a = Path(temp_dir) / "module_a.py"
        file_a.write_text("""
'''Module A with exports.'''

def helper_function():
    '''A helper function.'''
    return "helper"

class ExportedClass:
    '''A class to be exported.'''

    def method_one(self):
        '''Method one.'''
        pass

    def method_two(self, arg):
        '''Method two with arguments.'''
        return arg * 2

CONSTANT_A = 42
""")

        # Create file B that imports from A
        file_b = Path(temp_dir) / "module_b.py"
        file_b.write_text("""
'''Module B that uses Module A.'''

from module_a import helper_function, ExportedClass

import module_a

def local_function():
    '''Local function.'''
    result = helper_function()
    obj = ExportedClass()
    return obj.method_one()

class LocalClass:
    '''Local class.'''

    def __init__(self):
        self.value = module_a.CONSTANT_A

    def use_exported(self):
        '''Use exported class.'''
        ec = ExportedClass()
        return ec.method_two(5)
""")

        # Create file C with relative imports
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()

        file_c = subdir / "module_c.py"
        file_c.write_text("""
'''Module C with relative imports.'''

from ..module_a import CONSTANT_A
from ..module_b import LocalClass

def combined_function():
    '''Use both modules.'''
    local = LocalClass()
    return local.value + CONSTANT_A
""")

        # Create __init__.py files
        (Path(temp_dir) / "__init__.py").write_text("")
        (subdir / "__init__.py").write_text("")

        # Create repository mapper and scan
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=False,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Create reference resolver
        resolver = ReferenceResolver(repo_mapper)

        # Test 1: Build indexes
        print("\nTest 1: Building symbol indexes...")
        await resolver.build_indexes()
        stats = resolver.get_symbol_statistics()
        print(f"Indexed symbols: {stats['total_symbols']}")
        print(f"Total definitions: {stats['total_definitions']}")
        print(f"Total references: {stats['total_references']}")

        # Test 2: Find definitions
        print("\nTest 2: Finding symbol definitions...")

        # Find helper_function definition
        definition = await resolver.find_definition("helper_function")
        if definition:
            print(f"Found 'helper_function' at {definition.file_path}:{definition.line_number}")
        else:
            print("Could not find 'helper_function' definition")

        # Find ExportedClass definition
        definition = await resolver.find_definition("ExportedClass")
        if definition:
            print(f"Found 'ExportedClass' at {definition.file_path}:{definition.line_number}")

        # Find method definition (qualified name)
        definition = await resolver.find_definition("ExportedClass.method_two")
        if definition:
            print(f"Found 'ExportedClass.method_two' at {definition.file_path}:{definition.line_number}")

        # Test 3: Find references
        print("\nTest 3: Finding symbol references...")

        # Find all references to helper_function
        references = await resolver.find_references("helper_function")
        print(f"Found {len(references)} references to 'helper_function'")
        for ref in references[:3]:  # Show first 3
            print(f"  - {ref.file_path}:{ref.line_number} ({ref.reference_type})")

        # Find all references to ExportedClass
        references = await resolver.find_references("ExportedClass")
        print(f"Found {len(references)} references to 'ExportedClass'")

        # Test 4: Get dependencies
        print("\nTest 4: Analyzing file dependencies...")

        # Get dependencies for module_b
        deps = await resolver.get_dependencies("module_b.py")
        print(f"Dependencies of module_b.py:")
        for dep in deps:
            print(f"  - {dep}")

        # Get dependents of module_a
        dependents = await resolver.get_dependents("module_a.py")
        print(f"Files that depend on module_a.py:")
        for dependent in dependents:
            print(f"  - {dependent}")

        # Test 5: Get dependencies with indirect
        print("\nTest 5: Analyzing indirect dependencies...")

        indirect_deps = await resolver.get_dependencies("module_c.py", include_indirect=True)
        print(f"All dependencies of module_c.py (including indirect):")
        for dep in indirect_deps:
            print(f"  - {dep}")

        # Test 6: Symbol statistics
        print("\nTest 6: Most referenced symbols...")
        stats = resolver.get_symbol_statistics()
        print("Top referenced symbols:")
        for symbol, count in stats['most_referenced_symbols'][:5]:
            print(f"  - {symbol}: {count} references")

    print("\nReference resolution test completed successfully!")


async def test_cross_file_references():
    """Test cross-file reference resolution."""
    print("\n" + "="*50)
    print("Testing cross-file reference resolution...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a more complex structure
        utils = Path(temp_dir) / "utils.py"
        utils.write_text("""
'''Utility functions.'''

def format_data(data):
    '''Format data for display.'''
    return str(data)

class DataProcessor:
    '''Process data.'''

    def process(self, data):
        '''Process the data.'''
        return format_data(data)
""")

        main = Path(temp_dir) / "main.py"
        main.write_text("""
'''Main module.'''

from utils import DataProcessor, format_data

def main():
    '''Main function.'''
    processor = DataProcessor()
    result = processor.process("test")
    print(result)
""")

        tests = Path(temp_dir) / "tests.py"
        tests.write_text("""
'''Test module.'''

from utils import format_data
from main import main

def test_format_data():
    '''Test format_data function.'''
    assert format_data(42) == "42"
""")

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=False,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()

        resolver = ReferenceResolver(repo_mapper)
        await resolver.build_indexes()

        # Check that format_data is referenced in multiple files
        references = await resolver.find_references("format_data")
        print(f"\n'format_data' references found in {len(references)} locations:")
        for ref in references:
            rel_path = Path(ref.file_path).name
            print(f"  - {rel_path}:{ref.line_number}")

        # Check that DataProcessor is used correctly
        references = await resolver.find_references("DataProcessor")
        print(f"\n'DataProcessor' references found in {len(references)} locations:")

        # Verify dependency chain
        deps = await resolver.get_dependencies("main.py")
        print(f"\n'main.py' dependencies:")
        for dep in deps:
            print(f"  - {Path(dep).name}")

        print("\nCross-file reference resolution test completed!")


if __name__ == "__main__":
    asyncio.run(test_reference_resolution())
    asyncio.run(test_cross_file_references())