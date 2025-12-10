#!/usr/bin/env python3
"""Simple test for context compression."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper


async def test_compression():
    """Test context compression functionality."""
    print("Testing context compression...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with different content
        files = {
            "main.py": """'''Main entry point.'''

from utils import helper
from models import DataModel

def main():
    '''Main function.'''
    model = DataModel(1, "test")
    result = helper()
    print(f"{result} - {model.name}")

if __name__ == "__main__":
    main()
""",
            "utils.py": """'''Utility functions.'''

import os

def helper():
    '''Helper function.'''
    return "helper"

def format_data(data):
    '''Format data.'''
    return str(data)
""",
            "models.py": """'''Data models.'''

from dataclasses import dataclass

@dataclass
class DataModel:
    '''Data model.'''
    id: int
    name: str

    def process(self):
        '''Process model.'''
        return f"Processing {self.name}"
""",
            "legacy.py": """'''Legacy file that's not very important.'''

def old_function():
    '''Old function.'''
    pass

# Lots of boilerplate code...
class OldClass:
    '''Old class.'''

    def __init__(self):
        self.value = 0

    def method(self):
        '''Method.'''
        return self.value

def another_old():
    '''Another old function.'''
    return None

# More boilerplate...
def yet_another():
    '''Yet another function.'''
    pass

# Even more boilerplate...
class AnotherOldClass:
    '''Another old class.'''
    pass
"""
        }

        # Create all files
        for filename, content in files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)

        # Create repository mapper
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=False,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Test compression with different token budgets
        budgets = [500, 1000, 2000]

        for budget in budgets:
            print(f"\nTesting compression with {budget} token budget:")

            # Compress with importance scoring
            compressed = await repo_mapper.compress_with_importance(
                max_tokens=budget,
                target_file="main.py",
                operation="fix"
            )

            estimated_tokens = len(compressed) // 4
            print(f"  Compressed length: {len(compressed)} characters")
            print(f"  Estimated tokens: {estimated_tokens}")
            print(f"  Budget utilization: {estimated_tokens/budget*100:.1f}%")

            # Check what files are included
            included_files = []
            for filename in files.keys():
                if filename in compressed:
                    included_files.append(filename)

            print(f"  Files included: {', '.join(included_files)}")

            # Check if main.py is always included
            if "main.py" in compressed:
                print(f"  ✓ Target file (main.py) included")
            else:
                print(f"  ✗ Target file (main.py) missing!")

            # Show a small snippet
            if compressed:
                lines = compressed.split('\n')[:5]
                print(f"  Sample lines:")
                for line in lines:
                    if line.strip():
                        print(f"    {line[:60]}...")

    print("\nContext compression test completed successfully!")


async def test_importance_ranking():
    """Test importance-based file ranking."""
    print("\n" + "="*50)
    print("Testing importance-based ranking...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with different characteristics
        main_file = Path(temp_dir) / "main.py"
        main_file.write_text("""def main(): pass""")

        utils_file = Path(temp_dir) / "utils.py"
        utils_file.write_text("""def helper(): pass""")

        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("""def test_helper(): pass""")

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
        )
        await repo_mapper.scan_repository()

        # Get top files
        top_files = await repo_mapper.importance_scorer.get_top_files(limit=3)

        print("\nFiles ranked by importance:")
        for filename, score in top_files:
            factors = repo_mapper.importance_scorer.get_importance_factors(filename)
            entry_score = factors.get('entry_points', 0) if factors else 0
            print(f"  {score:.3f} - {filename} (entry points: {entry_score:.3f})")

    print("\nImportance ranking test completed!")


if __name__ == "__main__":
    asyncio.run(test_compression())
    asyncio.run(test_importance_ranking())