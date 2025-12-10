#!/usr/bin/env python3
"""Test context compression and injection."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.code_context import CodeContextProvider
from vibe_coder.analytics.token_counter import TokenCounter


async def test_context_compression():
    """Test context compression with importance scoring."""
    print("Starting context compression test...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple Python files
        files_content = {
            "main.py": """#!/usr/bin/env python3
'''Main entry point.'''

from utils import helper
from models import DataModel
from services import DataService

def main():
    '''Main function.'''
    model = DataModel()
    service = DataService(model)
    result = helper()
    print(result)

if __name__ == "__main__":
    main()
""",
            "utils.py": """'''Utility functions.'''

import os
import sys

def helper():
    '''Helper function.'''
    return "helper result"

def format_data(data):
    '''Format data for display.'''
    return str(data)

class Utility:
    '''Utility class.'''

    def __init__(self):
        self.value = 42

    def process(self):
        '''Process value.'''
        return self.value * 2
""",
            "models.py": """'''Data models.'''

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DataModel:
    '''Main data model.'''
    id: int
    name: str
    values: List[int] = None

    def __post_init__(self):
        if self.values is None:
            self.values = []

    def add_value(self, value):
        '''Add a value.'''
        self.values.append(value)

    def get_total(self):
        '''Get total of values.'''
        return sum(self.values)
""",
            "services.py": """'''Service layer.'''

from models import DataModel
from utils import format_data

class DataService:
    '''Data service class.'''

    def __init__(self, model: DataModel):
        self.model = model
        self.processed = 0

    def process_data(self):
        '''Process the data.'''
        formatted = format_data(self.model)
        self.processed += 1
        return formatted

    def get_stats(self):
        '''Get processing stats.'''
        return {
            'processed': self.processed,
            'total_values': self.model.get_total()
        }
""",
            "config.py": """'''Configuration.'''

import yaml

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'name': 'myapp'
}

# API configuration
API_CONFIG = {
    'endpoint': 'https://api.example.com',
    'timeout': 30
}
""",
            "old_file.py": """'''Old legacy file.'''

# This file hasn't been modified in a long time
def legacy_function():
    '''Legacy function.'''
    return "legacy"

# Lots of old code...
class OldClass:
    '''Old class.'''

    def old_method(self):
        '''Old method.'''
        pass

# More old code...
def another_old_function():
    '''Another old function.'''
    return None

# Even more old code...
""",
            "test_main.py": """'''Tests for main.'''

import unittest
from main import main
from models import DataModel
from services import DataService

class TestMain(unittest.TestCase):
    '''Test main functionality.'''

    def test_main(self):
        '''Test main function.'''
        # Test implementation
        pass

    def test_model_creation(self):
        '''Test model creation.'''
        model = DataModel(1, "test")
        self.assertEqual(model.id, 1)
"""
        }

        # Create all files
        for filename, content in files_content.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)

        # Create repository mapper
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Create code context provider
        context_provider = CodeContextProvider(
            repo_mapper=repo_mapper,
            model_name="gpt-4"
        )

        # Test 1: Get context for main.py
        print("\nTest 1: Getting context for main.py...")
        from vibe_coder.intelligence.types import ContextRequest, OperationType

        request = ContextRequest(
            operation=OperationType.FIX,
            target_file="main.py",
            query="Add error handling to main function",
            max_tokens=2000
        )
        context = await context_provider.get_context(request)

        print(f"Context retrieved:")
        print(f"  Files included: {context.files_included}")
        print(f"  Token estimate: {context.token_estimate}")
        print(f"  Truncated: {context.truncated}")

        # Test 2: Compressed context for fix operation
        print("\nTest 2: Context compression for fix operation...")
        compressed = await repo_mapper.compress_with_importance(
            max_tokens=1000,
            target_file="services.py",
            operation="fix"
        )

        print(f"Compressed context length: {len(compressed)} characters")
        estimated_tokens = len(compressed) // 4  # Rough estimate
        print(f"Estimated tokens: {estimated_tokens}")

        # Test 3: Different operations get different contexts
        print("\nTest 3: Operation-specific contexts...")
        operations = ["generate", "fix", "refactor", "explain", "test", "document"]

        for op in operations:
            context = await context_provider.get_context(
                query=f"{op} the services module",
                target_file="services.py",
                operation_type=op,
                max_tokens=1500
            )

            print(f"\n{op.title()} operation:")
            print(f"  Context items: {len(context.context_items)}")
            print(f"  Total tokens: {context.total_tokens}")

            # Show top files in context
            top_items = sorted(context.context_items,
                             key=lambda x: x.importance,
                             reverse=True)[:3]
            print(f"  Top files:")
            for item in top_items:
                print(f"    - {item.path}: importance={item.importance:.2f}")

        # Test 4: Context with recently modified file
        print("\nTest 4: Context with recent changes...")
        # Simulate recent file changes
        recent_changes = ["services.py", "utils.py"]

        context = await context_provider.get_context(
            query="Update the service to handle new requirements",
            target_file="services.py",
            recent_changes=recent_changes,
            max_tokens=2000
        )

        print(f"Context with recent changes:")
        print(f"  Items included: {len(context.context_items)}")
        print(f"  Total tokens: {context.total_tokens}")

        # Check if recent files are prioritized
        recent_included = [item for item in context.context_items
                          if Path(item.path).name in ["services.py", "utils.py"]]
        print(f"  Recent files in context: {len(recent_included)}")

        # Test 5: Context with many files (stress test)
        print("\nTest 5: Stress test with small token budget...")

        # Create many more files
        for i in range(10):
            extra_file = Path(temp_dir) / f"extra_{i}.py"
            extra_file.write_text(f"""'''Extra module {i}.'''

def function_{i}():
    '''Function {i}.'''
    return {i}

class Class{i}:
    '''Class {i}.'''

    def method_{i}(self):
        '''Method {i}.'''
        return self.function_{i}()
""")

        # Re-scan repository
        await repo_mapper.scan_repository()

        # Get context with very small budget
        context = await context_provider.get_context(
            query="Summarize the codebase",
            max_tokens=500  # Very small budget
        )

        print(f"Small budget context:")
        print(f"  Total files in repo: {len(repo_mapper._repo_map.modules)}")
        print(f"  Files in context: {len(context.context_items)}")
        print(f"  Budget utilization: {context.total_tokens}/500")

        # Show most important files included
        if context.context_items:
            most_important = max(context.context_items, key=lambda x: x.importance)
            print(f"  Most important file: {most_important.path} (importance={most_important.importance:.2f})")

    print("\nContext compression test completed successfully!")


async def test_context_injection():
    """Test context injection into chat messages."""
    print("\n" + "="*50)
    print("Testing context injection...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple project
        Path(temp_dir / "app.py").write_text("""'''Application entry point.'''

from calculator import Calculator

def main():
    '''Main function.'''
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
""")

        Path(temp_dir / "calculator.py").write_text("""'''Calculator module.'''

class Calculator:
    '''Simple calculator.'''

    def __init__(self):
        self.history = []

    def add(self, a, b):
        '''Add two numbers.'''
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        '''Subtract two numbers.'''
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a, b):
        '''Multiply two numbers.'''
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a, b):
        '''Divide two numbers.'''
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def get_history(self):
        '''Get calculation history.'''
        return self.history
""")

        Path(temp_dir / "test_calculator.py").write_text("""'''Tests for calculator.'''

import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    '''Test calculator functionality.'''

    def setUp(self):
        '''Set up test.'''
        self.calc = Calculator()

    def test_add(self):
        '''Test addition.'''
        self.assertEqual(self.calc.add(2, 3), 5)

    def test_divide_by_zero(self):
        '''Test division by zero.'''
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)
""")

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()

        context_provider = CodeContextProvider(
            repo_mapper=repo_mapper,
            token_counter=TokenCounter(),
            model_name="gpt-4"
        )

        # Test context extraction for different queries
        test_queries = [
            ("Add a power method to Calculator", "calculator.py"),
            ("Test the multiply function", "test_calculator.py"),
            ("Improve error handling", "app.py"),
            ("Document the Calculator class", "calculator.py")
        ]

        print("\nContext extraction for various queries:")
        for query, expected_file in test_queries:
            print(f"\nQuery: {query}")
            print(f"Expected target: {expected_file}")

            context = await context_provider.get_context(
                query=query,
                target_file=expected_file,
                max_tokens=1000
            )

            print(f"  Files in context: {len(context.context_items)}")
            print(f"  Total tokens: {context.total_tokens}")

            # Check if expected file is in context
            target_included = any(
                item.path == expected_file
                for item in context.context_items
            )
            print(f"  Target file included: {target_included}")

    print("\nContext injection test completed!")


if __name__ == "__main__":
    asyncio.run(test_context_compression())
    asyncio.run(test_context_injection())