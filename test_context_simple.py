#!/usr/bin/env python3
"""Simple test for context compression."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.code_context import CodeContextProvider, ContextRequest, OperationType
from vibe_coder.analytics.token_counter import TokenCounter


async def test_context_compression():
    """Test context compression functionality."""
    print("Starting context compression test...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a few test files
        main_file = Path(temp_dir) / "main.py"
        main_file.write_text("""'''Main entry point.'''

from utils import helper

def main():
    '''Main function.'''
    result = helper()
    print(result)

if __name__ == "__main__":
    main()
""")

        utils_file = Path(temp_dir) / "utils.py"
        utils_file.write_text("""'''Utility functions.'''

import os

def helper():
    '''Helper function.'''
    return "helper result"

def format_data(data):
    '''Format data.'''
    return str(data)
""")

        models_file = Path(temp_dir) / "models.py"
        models_file.write_text("""'''Data models.'''

from dataclasses import dataclass

@dataclass
class Model:
    '''Data model.'''
    id: int
    name: str

    def process(self):
        '''Process model.'''
        return f"Processing {self.name}"
""")

        # Create repository mapper
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Create context provider
        context_provider = CodeContextProvider(
            repo_mapper=repo_mapper,
            model_name="gpt-4"
        )

        # Test 1: Get context for fix operation
        print("\nTest 1: Context for fix operation...")
        request = ContextRequest(
            operation=OperationType.FIX,
            target_file="main.py",
            query="Fix error in main function",
            max_tokens=1000
        )
        context = await context_provider.get_context(request)

        print(f"Context for fix operation:")
        print(f"  Files included: {len(context.files_included)}")
        print(f"  Files: {', '.join(context.files_included)}")
        print(f"  Token estimate: {context.token_estimate}")
        print(f"  Truncated: {context.truncated}")

        # Test 2: Get context for explain operation
        print("\nTest 2: Context for explain operation...")
        request = ContextRequest(
            operation=OperationType.EXPLAIN,
            target_file="models.py",
            query="Explain the Model class",
            max_tokens=1000
        )
        context = await context_provider.get_context(request)

        print(f"Context for explain operation:")
        print(f"  Files included: {len(context.files_included)}")
        print(f"  Functions included: {context.functions_included}")
        print(f"  Classes included: {context.classes_included}")
        print(f"  Token estimate: {context.token_estimate}")

        # Test 3: Compression with importance scoring
        print("\nTest 3: Compression with importance scoring...")
        compressed = await repo_mapper.compress_with_importance(
            max_tokens=500,  # Small budget
            target_file="main.py",
            operation="fix"
        )

        print(f"Compressed representation:")
        print(f"  Length: {len(compressed)} characters")
        print(f"  Estimated tokens: {len(compressed) // 4}")

        # Show a snippet
        if len(compressed) > 200:
            print(f"  Snippet:\n{compressed[:200]}...")
        else:
            print(f"  Full content:\n{compressed}")

    print("\nContext compression test completed successfully!")


async def test_token_budget_integration():
    """Test token budgeting integration."""
    print("\n" + "="*50)
    print("Testing token budget integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with varying importance
        important_file = Path(temp_dir) / "important.py"
        important_file.write_text("""'''Important module.'''

class ImportantClass:
    '''Critical business logic.'''

    def critical_method(self):
        '''Critical method.'''
        return "critical"
""")

        less_file = Path(temp_dir) / "less_important.py"
        less_file.write_text("""'''Less important module.'''

def helper():
    '''Simple helper.'''
    return "helper"

# Lots of boilerplate...
class Boilerplate:
    '''Boilerplate class.'''
    pass

def more_boilerplate():
    '''More boilerplate.'''
    return None
""")

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
        )
        await repo_mapper.scan_repository()

        # Test compression with different budgets
        budgets = [200, 500, 1000, 2000]

        for budget in budgets:
            print(f"\nTesting with {budget} token budget:")
            compressed = await repo_mapper.compress_with_importance(
                max_tokens=budget,
                target_file="important.py",
                operation="fix"
            )

            estimated_tokens = len(compressed) // 4
            utilization = (estimated_tokens / budget) * 100
            print(f"  Estimated tokens: {estimated_tokens}")
            print(f"  Budget utilization: {utilization:.1f}%")

            # Check if important file is included
            if "ImportantClass" in compressed:
                print(f"  ✓ Important file included")
            else:
                print(f"  ✗ Important file missing")

    print("\nToken budget integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_context_compression())
    asyncio.run(test_token_budget_integration())