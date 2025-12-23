"""
File importance scoring for repository intelligence.

This module provides algorithms to score files based on various factors
like recency, dependencies, entry points, and graph centrality.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from vibe_coder.intelligence.types import FileImportance

if TYPE_CHECKING:
    from vibe_coder.intelligence.repo_mapper import RepositoryMapper


class ImportanceScorer:
    """Scores files and symbols based on relevance and importance."""

    # Scoring weights (should sum to 1.0)
    WEIGHTS = {
        "recency": 0.20,  # Recently modified files
        "dependencies": 0.25,  # Files with more dependents
        "entry_points": 0.20,  # Main files, CLI entry points
        "test_coverage": 0.10,  # Well-tested files
        "change_frequency": 0.15,  # Frequently changed files
        "graph_centrality": 0.10,  # Files in dependency chains
    }

    # Time windows for scoring
    RECENT_TIMEDELTA = timedelta(days=7)  # Files modified in last week
    FREQUENT_TIMEDELTA = timedelta(days=30)  # For change frequency analysis

    def __init__(self, repo_mapper: "RepositoryMapper"):
        self.repo_mapper = repo_mapper
        self._importance_cache: Dict[str, FileImportance] = {}
        self._git_history: Dict[str, List[datetime]] = {}

    async def score_file(self, file_path: str, context: Optional[Dict] = None) -> float:
        """
        Calculate importance score for a file.

        Args:
            file_path: Path to the file relative to repository root.
            context: Additional context (target file, operation type, etc.)

        Returns:
            Importance score between 0.0 and 1.0.
        """
        # Check cache first
        if file_path in self._importance_cache:
            cached = self._importance_cache[file_path]
            # Check if cache is still valid (5 minutes)
            if datetime.now() - cached.last_calculated < timedelta(minutes=5):
                return cached.score

        # Get file node
        if not self.repo_mapper._repo_map or file_path not in self.repo_mapper._repo_map.modules:
            return 0.0

        node = self.repo_mapper._repo_map.modules[file_path]

        # Calculate individual scores
        factors = {}

        # 1. Recency score
        factors["recency"] = self._recency_score(file_path, node)

        # 2. Dependency score
        factors["dependencies"] = self._dependency_score(file_path)

        # 3. Entry point score
        factors["entry_points"] = self._entry_point_score(file_path)

        # 4. Test coverage score
        factors["test_coverage"] = self._test_coverage_score(file_path)

        # 5. Change frequency score
        factors["change_frequency"] = await self._change_frequency_score(file_path)

        # 6. Graph centrality score
        factors["graph_centrality"] = self._graph_centrality_score(file_path)

        # Apply weights and calculate final score
        final_score = 0.0
        for factor, score in factors.items():
            weight = self.WEIGHTS.get(factor, 0.0)
            final_score += score * weight

        # Boost score based on context
        if context:
            final_score = self._apply_context_boost(final_score, file_path, context)

        # Cap at 1.0
        final_score = min(1.0, final_score)

        # Cache the result
        self._importance_cache[file_path] = FileImportance(
            file_path=file_path,
            score=final_score,
            factors=factors,
            last_calculated=datetime.now(),
        )

        return final_score

    def _recency_score(self, file_path: str, node) -> float:
        """Score based on how recently the file was modified."""
        if not node.last_modified:
            return 0.0

        try:
            last_modified = datetime.fromisoformat(node.last_modified)
            time_since_modified = datetime.now() - last_modified

            # Full score if modified within RECENT_TIMEDELTA
            if time_since_modified <= self.RECENT_TIMEDELTA:
                return 1.0

            # Linear decay over the last month
            if time_since_modified <= timedelta(days=30):
                days_old = time_since_modified.days
                return max(0.0, 1.0 - (days_old - 7) / 23.0)

            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _dependency_score(self, file_path: str) -> float:
        """Score based on how many files depend on this file."""
        if not self.repo_mapper._repo_map:
            return 0.0

        # Count dependents
        dependents = 0
        for other_file, deps in self.repo_mapper._repo_map.dependency_graph.items():
            if file_path in deps:
                dependents += 1

        # Normalize score (0-5 dependents = linear scale, >5 = full score)
        if dependents >= 5:
            return 1.0
        elif dependents > 0:
            return dependents / 5.0
        else:
            return 0.0

    def _entry_point_score(self, file_path: str) -> float:
        """Score based on whether file is an entry point."""
        if not self.repo_mapper._repo_map:
            return 0.0

        # Check if in entry points list
        if file_path in self.repo_mapper._repo_map.entry_points:
            return 1.0

        # Check for common entry point patterns
        file_name = os.path.basename(file_path).lower()
        if file_name in ["main.py", "cli.py", "app.py", "index.py", "__main__.py"]:
            return 0.8

        # Check if has main function
        if self.repo_mapper._repo_map.modules[file_path].functions:
            for func in self.repo_mapper._repo_map.modules[file_path].functions:
                if func.name == "main":
                    return 0.6

        return 0.0

    def _test_coverage_score(self, file_path: str) -> float:
        """Score based on test coverage."""
        if not self.repo_mapper._repo_map:
            return 0.0

        # Check if it's a test file
        if file_path in self.repo_mapper._repo_map.test_files:
            return 0.3  # Test files get some points but not full

        # Look for corresponding test file
        base_name = os.path.splitext(file_path)[0]
        possible_test_files = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"tests/{os.path.basename(file_path)}",
            f"test/{os.path.basename(file_path)}",
        ]

        has_test = any(
            test_file in self.repo_mapper._repo_map.modules for test_file in possible_test_files
        )

        return 1.0 if has_test else 0.2  # Small score even without tests

    async def _change_frequency_score(self, file_path: str) -> float:
        """Score based on how frequently the file is changed."""
        # This would ideally integrate with git history
        # For now, use a simple heuristic based on file type and location

        file_name = os.path.basename(file_path).lower()
        file_dir = os.path.dirname(file_path).lower()

        # Configuration files tend to change frequently
        if file_name.endswith((".yaml", ".yml", ".json", ".toml", ".ini", ".conf")):
            return 0.8

        # Documentation files
        if file_name.endswith((".md", ".rst", ".txt")) or "docs" in file_dir:
            return 0.6

        # Setup/CI files
        if any(name in file_dir for name in ["setup", "ci", "github", ".git"]):
            return 0.7

        # Source code files get moderate score
        if file_name.endswith(".py"):
            return 0.4

        return 0.2

    def _graph_centrality_score(self, file_path: str) -> float:
        """Score based on position in dependency graph."""
        if not self.repo_mapper._repo_map:
            return 0.0

        # Calculate betweenness centrality (simplified)
        total_files = len(self.repo_mapper._repo_map.modules)
        if total_files <= 1:
            return 0.0

        # Get dependencies and dependents
        dependencies = self.repo_mapper._repo_map.dependency_graph.get(file_path, set())
        dependents = set()
        for other_file, deps in self.repo_mapper._repo_map.dependency_graph.items():
            if file_path in deps:
                dependents.add(other_file)

        # Score based on connection ratio
        connections = len(dependencies) + len(dependents)
        max_connections = total_files - 1

        if max_connections > 0:
            return min(1.0, connections / max_connections)
        return 0.0

    def _apply_context_boost(self, base_score: float, file_path: str, context: Dict) -> float:
        """Apply score adjustments based on context."""
        boosted_score = base_score

        # Boost target file
        target_file = context.get("target_file")
        if target_file and file_path == target_file:
            boosted_score = min(1.0, boosted_score + 0.3)

        # Boost files in same directory as target
        if target_file:
            target_dir = os.path.dirname(target_file)
            file_dir = os.path.dirname(file_path)
            if target_dir == file_dir and file_path != target_file:
                boosted_score = min(1.0, boosted_score + 0.1)

        # Boost based on operation type
        operation = context.get("operation", "").lower()
        if operation == "fix" and file_path == target_file:
            boosted_score = min(1.0, boosted_score + 0.2)
        elif operation == "test" and "test" in file_path:
            boosted_score = min(1.0, boosted_score + 0.2)
        elif operation == "refactor" and self._dependency_score(file_path) > 0.5:
            boosted_score = min(1.0, boosted_score + 0.15)

        return boosted_score

    async def rank_files(
        self, file_paths: List[str], context: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Rank a list of files by importance.

        Args:
            file_paths: List of file paths to rank.
            context: Additional context for scoring.

        Returns:
            List of (file_path, score) tuples sorted by score descending.
        """
        scored_files = []

        for file_path in file_paths:
            score = await self.score_file(file_path, context)
            scored_files.append((file_path, score))

        # Sort by score descending
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return scored_files

    def get_importance_factors(self, file_path: str) -> Optional[Dict[str, float]]:
        """
        Get the individual factor scores for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary of factor scores or None if not cached.
        """
        if file_path in self._importance_cache:
            return self._importance_cache[file_path].factors
        return None

    def clear_cache(self) -> None:
        """Clear the importance score cache."""
        self._importance_cache.clear()

    async def get_top_files(self, limit: int = 10, context: Optional[Dict] = None) -> List[tuple]:
        """
        Get the top N most important files in the repository.

        Args:
            limit: Maximum number of files to return.
            context: Additional context for scoring.

        Returns:
            List of (file_path, score) tuples.
        """
        if not self.repo_mapper._repo_map:
            return []

        all_files = list(self.repo_mapper._repo_map.modules.keys())
        return (await self.rank_files(all_files, context))[:limit]

    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update the scoring weights.

        Args:
            new_weights: New weight dictionary.
        """
        # Validate weights sum to 1.0
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")

        self.WEIGHTS.update(new_weights)
        # Clear cache since weights changed
        self.clear_cache()
