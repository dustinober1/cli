#!/usr/bin/env python3
"""Simple test for importance scoring algorithm."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.importance_scorer import ImportanceScorer


async def test_importance_scoring():
    """Test file importance scoring."""
    print("Starting importance scoring test...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a main file
        main_file = Path(temp_dir) / "main.py"
        main_file.write_text("""#!/usr/bin/env python3
'''Main entry point.'''

def main():
    '''Main function.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

        # Create a utils file
        utils_file = Path(temp_dir) / "utils.py"
        utils_file.write_text("""'''Utilities module.'''

import os
import sys

def helper():
    '''Helper function.'''
    pass
""")

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

        # Test 1: Score main file (should have high entry point score)
        print("\nTest 1: Scoring entry point...")
        if "main.py" in repo_mapper._repo_map.modules:
            score = await scorer.score_file("main.py")
            factors = scorer.get_importance_factors("main.py")
            print(f"main.py score: {score:.3f}")
            if factors:
                print(f"  Entry points: {factors.get('entry_points', 0):.3f}")
                print(f"  Recency: {factors.get('recency', 0):.3f}")
                print(f"  Dependencies: {factors.get('dependencies', 0):.3f}")

        # Test 2: Score utils file
        print("\nTest 2: Scoring utility file...")
        if "utils.py" in repo_mapper._repo_map.modules:
            score = await scorer.score_file("utils.py")
            factors = scorer.get_importance_factors("utils.py")
            print(f"utils.py score: {score:.3f}")
            if factors:
                print(f"  Entry points: {factors.get('entry_points', 0):.3f}")
                print(f"  Change frequency: {factors.get('change_frequency', 0):.3f}")

        # Test 3: Context-aware scoring
        print("\nTest 3: Context-aware scoring...")
        if "utils.py" in repo_mapper._repo_map.modules:
            context = {"target_file": "utils.py", "operation": "fix"}
            score_with_context = await scorer.score_file("utils.py", context)
            score_without_context = await scorer.score_file("utils.py")
            print(f"utils.py score without context: {score_without_context:.3f}")
            print(f"utils.py score with fix context: {score_with_context:.3f}")

        # Test 4: Ranking files
        print("\nTest 4: Ranking files...")
        all_files = list(repo_mapper._repo_map.modules.keys())
        ranked = await scorer.rank_files(all_files)
        print("\nFiles ranked by importance:")
        for filename, score in ranked:
            print(f"  {score:.3f} - {filename}")

        # Test 5: Update weights
        print("\nTest 5: Testing weight updates...")
        original_weights = scorer.WEIGHTS.copy()
        print(f"Original weights: {original_weights}")

        # Update weights to emphasize entry points
        new_weights = {
            "recency": 0.10,
            "dependencies": 0.20,
            "entry_points": 0.40,  # Increased
            "test_coverage": 0.10,
            "change_frequency": 0.10,
            "graph_centrality": 0.10,
        }
        scorer.update_weights(new_weights)
        print(f"Updated weights (more emphasis on entry points)")

        # Re-score main file
        if "main.py" in repo_mapper._repo_map.modules:
            new_score = await scorer.score_file("main.py")
            print(f"main.py new score: {new_score:.3f}")

        # Restore original weights
        scorer.update_weights(original_weights)

    print("\nImportance scoring test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_importance_scoring())