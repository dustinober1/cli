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
        base_file = "utils.py"

        for op in operations:
            context = {"operation": op, "target_file": base_file}
            score = await scorer.score_file(base_file, context)
            print(f"  {op.title()}: {score:.3f}")

    print("\nImportance scoring test completed successfully!")


async def test_importance_factors():
    """Test importance scoring factors in detail."""
    print("\n" + "="*50)
    print("Testing importance scoring factors...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dependency chain
        Path(temp_dir / "base.py").write_text("""'''Base module.'''

def base_func():
    '''Base function.'''
    return "base"

class Base:
    '''Base class.'''
    pass
""")

        Path(temp_dir / "intermediate.py").write_text("""'''Intermediate module.'''

from base import Base, base_func

class Intermediate(Base):
    '''Intermediate class extending Base.'''

    def process(self):
        '''Process using base function.'''
        return base_func()
""")

        Path(temp_dir / "top_level.py").write_text("""'''Top level module.'''

from intermediate import Intermediate

def main():
    '''Main function.'''
    obj = Intermediate()
    return obj.process()

if __name__ == "__main__":
    main()
""")

        Path(temp_dir / "standalone.py").write_text("""'''Standalone module.'''

def standalone_func():
    '''Not used anywhere.'''
    return "standalone"
""")

        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,
            enable_importance_scoring=True,
            enable_reference_resolution=True,
        )
        await repo_mapper.scan_repository()

        scorer = ImportanceScorer(repo_mapper)

        # Build dependency graph
        if repo_mapper._repo_map:
            repo_mapper._repo_map.dependency_graph = {
                "intermediate.py": {"base.py"},
                "top_level.py": {"intermediate.py"},
                "standalone.py": set()
            }

        # Analyze scores
        files = ["base.py", "intermediate.py", "top_level.py", "standalone.py"]

        print("\nDependency chain analysis:")
        for filename in files:
            score = await scorer.score_file(filename)
            factors = scorer.get_importance_factors(filename)

            print(f"\n{filename}:")
            print(f"  Total score: {score:.3f}")

            if factors:
                print(f"  Dependency score: {factors.get('dependencies', 0):.3f}")
                print(f"  Graph centrality: {factors.get('graph_centrality', 0):.3f}")

        # Get statistics
        dependents = {
            "base.py": await scorer.get_dependents("base.py"),
            "intermediate.py": await scorer.get_dependents("intermediate.py"),
            "top_level.py": await scorer.get_dependents("top_level.py"),
            "standalone.py": await scorer.get_dependents("standalone.py")
        }

        print("\nDependency relationships:")
        for file, deps in dependents.items():
            print(f"  {file} is depended on by: {len(deps)} files")

    print("\nImportance factors test completed!")


if __name__ == "__main__":
    asyncio.run(test_importance_scoring())
    asyncio.run(test_importance_factors())