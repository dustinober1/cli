#!/usr/bin/env python3
"""Test importance scoring algorithm."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.importance_scorer import ImportanceScorer


async def test_importance_scoring():
    """Test file importance scoring."""
    print("Starting importance scoring test...")

    # Create a temporary repository with various file types
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create main entry point
        main = Path(temp_dir) / "main.py"
        main.write_text("""#!/usr/bin/env python3
'''Main entry point.'''

def main():
    '''Main function.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

        # Create a module with many imports (high dependency)
        utils = Path(temp_dir) / "utils.py"
        utils.write_text("""'''Utilities module.'''

import os
import sys
import json
import requests
import numpy as np
import pandas as pd

def helper():
    '''Helper function.'''
    pass

class Utility:
    '''Utility class.'''
    pass
""")

        # Create a test file
        test_main = Path(temp_dir) / "test_main.py"
        test_main.write_text("""'''Tests for main module.'''

import unittest
from main import main

class TestMain(unittest.TestCase):
    '''Test main function.'''

    def test_main(self):
        '''Test main runs.'''
        main()
""")

        # Create a config file
        config = Path(temp_dir) / "config.yaml"
        config.write_text("""# Configuration
database:
  host: localhost
  port: 5432

logging:
  level: INFO
  file: app.log
""")

        # Create a recently modified file
        recent = Path(temp_dir) / "recent_file.py"
        recent.write_text("""'''Recently modified file.'''")

        # Set modification times
        now = datetime.now()

        # Main file is old (30 days ago)
        old_time = now - timedelta(days=30)
        import os
        os.utime(main, (old_time.timestamp(), old_time.timestamp()))

        # Recent file is very recent (1 hour ago)
        recent_time = now - timedelta(hours=1)
        os.utime(recent, (recent_time.timestamp(), recent_time.timestamp()))

        # Create repository mapper
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=False,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Create importance scorer
        scorer = ImportanceScorer(repo_mapper)

        # Test 1: Score individual files
        print("\nTest 1: Scoring individual files...")
        files_to_score = [
            ("main.py", "Entry point"),
            ("utils.py", "Utility with imports"),
            ("test_main.py", "Test file"),
            ("config.yaml", "Configuration file"),
            ("recent_file.py", "Recently modified")
        ]

        for filename, description in files_to_score:
            # Skip non-Python files for now since they're not in modules
            if filename not in repo_mapper._repo_map.modules:
                continue

            score = await scorer.score_file(filename)
            print(f"\n{filename} ({description}):")
            print(f"  Score: {score:.3f}")

            # Get factor breakdown
            factors = scorer.get_importance_factors(filename)
            if factors:
                print(f"  Factors:")
                for factor, value in factors.items():
                    print(f"    - {factor}: {value:.3f}")

        # Test 2: Ranking files
        print("\nTest 2: Ranking all files...")
        all_files = list(repo_mapper._repo_map.modules.keys())
        ranked = await scorer.rank_files(all_files)

        print("\nFiles ranked by importance:")
        for filename, score in ranked:
            print(f"  {score:.3f} - {filename}")

        # Test 3: Context-aware scoring
        print("\nTest 3: Context-aware scoring...")

        # Score with target file context
        if "utils.py" in repo_mapper._repo_map.modules:
            context = {
                "target_file": "utils.py",
                "operation": "fix"
            }

            score_with_context = await scorer.score_file("utils.py", context)
            score_without_context = await scorer.score_file("utils.py")

            print(f"\nutils.py score without context: {score_without_context:.3f}")
            print(f"utils.py score with fix context: {score_with_context:.3f}")

            if score_with_context > score_without_context:
                print("✓ Context boosted the score for target file")

        # Test 4: Top files
        print("\nTest 4: Getting top files...")
        top_files = await scorer.get_top_files(limit=3)
        print("\nTop 3 most important files:")
        for filename, score in top_files:
            print(f"  {score:.3f} - {filename}")

        # Test 5: Different operations
        print("\nTest 5: Operation-specific scoring...")
        operations = ["fix", "refactor", "test", "document"]

        if "utils.py" in repo_mapper._repo_map.modules:
            base_file = "utils.py"

            for op in operations:
                context = {"operation": op, "target_file": base_file}
                score = await scorer.score_file(base_file, context)
                print(f"  {op.title()}: {score:.3f}")

    print("\nImportance scoring test completed successfully!")


async def test_entry_point_scoring():
    """Test scoring of entry points."""
    print("\n" + "="*50)
    print("Testing entry point scoring...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create various entry point patterns
        files = {
            "main.py": "def main(): pass",
            "app.py": "if __name__ == '__main__': pass",
            "cli.py": "def cli(): pass",
            "index.py": "def start(): pass",
            "__main__.py": "def run(): pass",
            "regular.py": "def function(): pass"
        }

        for filename, content in files.items():
            full_content = f"'''{filename}'''\n\n{content}\n"
            Path(temp_dir / filename).write_text(full_content)

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
        )
        await repo_mapper.scan_repository()

        scorer = ImportanceScorer(repo_mapper)

        print("\nEntry point scores:")
        for filename in files.keys():
            score = await scorer.score_file(filename)
            factors = scorer.get_importance_factors(filename)
            entry_score = factors.get('entry_points', 0) if factors else 0
            print(f"  {filename}: {score:.3f} (entry points: {entry_score:.3f})")

    print("\nEntry point scoring test completed!")


if __name__ == "__main__":
    asyncio.run(test_importance_scoring())
    asyncio.run(test_entry_point_scoring())