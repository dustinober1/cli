"""
Tests for file importance scoring functionality.

This module tests the ImportanceScorer class which provides algorithms
to score files based on various factors like recency, dependencies,
and graph centrality.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from vibe_coder.intelligence.importance_scorer import ImportanceScorer
from vibe_coder.intelligence.types import FileImportance, FileNode, FunctionSignature


class TestImportanceScorerInitialization:
    """Test ImportanceScorer initialization."""

    def test_init(self, tmp_path):
        """Test scorer initialization."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        scorer = ImportanceScorer(mock_mapper)

        assert scorer.repo_mapper == mock_mapper
        assert scorer._importance_cache == {}
        assert scorer._git_history == {}

    def test_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        total = sum(ImportanceScorer.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_weight_keys(self):
        """Test that all expected weight keys are present."""
        expected_keys = {
            "recency",
            "dependencies",
            "entry_points",
            "test_coverage",
            "change_frequency",
            "graph_centrality",
        }
        assert set(ImportanceScorer.WEIGHTS.keys()) == expected_keys


class TestRecencyScore:
    """Test recency scoring functionality."""

    def test_recency_score_recent_file(self):
        """Test recency score for recently modified file."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Create file node modified recently
        node = MagicMock()
        node.last_modified = (datetime.now() - timedelta(days=2)).isoformat()

        score = scorer._recency_score("test.py", node)
        assert score == 1.0

    def test_recency_score_old_file(self):
        """Test recency score for old file."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Create file node modified 20 days ago
        node = MagicMock()
        node.last_modified = (datetime.now() - timedelta(days=20)).isoformat()

        score = scorer._recency_score("test.py", node)
        assert 0.0 < score < 1.0
        # Should be decaying linearly
        expected_score = 1.0 - (20 - 7) / 23.0
        assert abs(score - expected_score) < 0.01

    def test_recency_score_very_old_file(self):
        """Test recency score for very old file."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Create file node modified 40 days ago
        node = MagicMock()
        node.last_modified = (datetime.now() - timedelta(days=40)).isoformat()

        score = scorer._recency_score("test.py", node)
        assert score == 0.0

    def test_recency_score_no_timestamp(self):
        """Test recency score when no timestamp is available."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Create file node without timestamp
        node = MagicMock()
        node.last_modified = None

        score = scorer._recency_score("test.py", node)
        assert score == 0.0

    def test_recency_score_invalid_timestamp(self):
        """Test recency score with invalid timestamp."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Create file node with invalid timestamp
        node = MagicMock()
        node.last_modified = "invalid-date"

        score = scorer._recency_score("test.py", node)
        assert score == 0.0


class TestDependencyScore:
    """Test dependency scoring functionality."""

    def test_dependency_score_many_dependents(self):
        """Test dependency score for file with many dependents."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.dependency_graph = {
            "file1.py": {"target.py"},
            "file2.py": {"target.py"},
            "file3.py": {"target.py"},
            "file4.py": {"target.py"},
            "file5.py": {"target.py"},
            "file6.py": {"target.py"},  # 6 dependents
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._dependency_score("target.py")
        assert score == 1.0  # Cap at 1.0 for 5+ dependents

    def test_dependency_score_few_dependents(self):
        """Test dependency score for file with few dependents."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.dependency_graph = {
            "file1.py": {"target.py"},
            "file2.py": {"target.py"},
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._dependency_score("target.py")
        assert score == 2.0 / 5.0  # 2 dependents out of 5 for full score

    def test_dependency_score_no_dependents(self):
        """Test dependency score for file with no dependents."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.dependency_graph = {}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._dependency_score("target.py")
        assert score == 0.0

    def test_dependency_score_no_repo_map(self):
        """Test dependency score when no repository map is available."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._dependency_score("target.py")
        assert score == 0.0


class TestEntryPointScore:
    """Test entry point scoring functionality."""

    def test_entry_point_score_in_list(self):
        """Test entry point score for file in entry points list."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.entry_points = ["main.py", "cli.py"]
        mock_mapper._repo_map.modules = {"main.py": MagicMock()}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._entry_point_score("main.py")
        assert score == 1.0

    def test_entry_point_score_common_names(self):
        """Test entry point score for common entry point names."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.entry_points = []
        mock_mapper._repo_map.modules = {
            "cli.py": MagicMock(),
            "app.py": MagicMock(),
            "index.py": MagicMock(),
            "__main__.py": MagicMock(),
        }

        scorer = ImportanceScorer(mock_mapper)

        for filename in ["cli.py", "app.py", "index.py", "__main__.py"]:
            score = scorer._entry_point_score(filename)
            assert score == 0.8

    def test_entry_point_score_with_main_function(self):
        """Test entry point score for file with main function."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.entry_points = []

        # Create file with main function
        main_func = FunctionSignature(
            name="main", module_path="module", file_path="module.py", line_start=1, line_end=10
        )

        mock_mapper._repo_map.modules = {"module.py": MagicMock(functions=[main_func])}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._entry_point_score("module.py")
        assert score == 0.6

    def test_entry_point_score_regular_file(self):
        """Test entry point score for regular file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.entry_points = []
        mock_mapper._repo_map.modules = {"utils.py": MagicMock(functions=[])}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._entry_point_score("utils.py")
        assert score == 0.0


class TestTestCoverageScore:
    """Test test coverage scoring functionality."""

    def test_test_coverage_score_test_file(self):
        """Test test coverage score for a test file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.test_files = ["test_main.py", "test_utils.py"]
        mock_mapper._repo_map.modules = {"test_main.py": MagicMock()}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._test_coverage_score("test_main.py")
        assert score == 0.3

    def test_test_coverage_score_with_test(self):
        """Test test coverage score for file with corresponding test."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.test_files = []
        mock_mapper._repo_map.modules = {
            "main.py": MagicMock(),
            "test_main.py": MagicMock(),
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._test_coverage_score("main.py")
        assert score == 1.0  # Has test_main.py

    def test_test_coverage_score_no_test(self):
        """Test test coverage score for file without test."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.test_files = []
        mock_mapper._repo_map.modules = {
            "utils.py": MagicMock(),
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._test_coverage_score("utils.py")
        assert score == 0.2  # Small score even without tests

    def test_test_coverage_score_test_directory(self):
        """Test test coverage score for file with test in tests/ directory."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.test_files = []
        mock_mapper._repo_map.modules = {
            "src/main.py": MagicMock(),
            "tests/main.py": MagicMock(),
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._test_coverage_score("src/main.py")
        assert score == 1.0  # Has tests/main.py


@pytest.mark.asyncio
class TestChangeFrequencyScore:
    """Test change frequency scoring functionality."""

    async def test_change_frequency_score_config_files(self):
        """Test change frequency score for configuration files."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        config_files = [
            "config.yaml",
            "settings.yml",
            "package.json",
            "pyproject.toml",
            "app.ini",
            "database.conf",
        ]

        for filename in config_files:
            score = await scorer._change_frequency_score(filename)
            assert score == 0.8

    async def test_change_frequency_score_doc_files(self):
        """Test change frequency score for documentation files."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        doc_files = [
            "README.md",
            "guide.rst",
            "notes.txt",
            "docs/api.md",
        ]

        for filename in doc_files:
            score = await scorer._change_frequency_score(filename)
            assert score == 0.6

    async def test_change_frequency_score_ci_files(self):
        """Test change frequency score for CI/setup files."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        ci_files = [
            "setup.py",
            "ci/build.sh",
            ".github/workflows/test.yml",
            ".gitignore",
        ]

        for filename in ci_files:
            score = await scorer._change_frequency_score(filename)
            assert score == 0.7

    async def test_change_frequency_score_python_files(self):
        """Test change frequency score for Python files."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        score = await scorer._change_frequency_score("module.py")
        assert score == 0.4

    async def test_change_frequency_score_other_files(self):
        """Test change frequency score for other file types."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        score = await scorer._change_frequency_score("data.bin")
        assert score == 0.2


class TestGraphCentralityScore:
    """Test graph centrality scoring functionality."""

    def test_graph_centrality_highly_connected(self):
        """Test graph centrality score for highly connected file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "a.py": MagicMock(),
            "b.py": MagicMock(),
            "c.py": MagicMock(),
            "d.py": MagicMock(),
            "target.py": MagicMock(),
        }
        mock_mapper._repo_map.dependency_graph = {
            "target.py": {"a.py", "b.py"},  # Depends on 2 files
            "c.py": {"target.py"},  # One dependent
            "d.py": {"target.py"},  # Another dependent
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._graph_centrality_score("target.py")
        # 2 dependencies + 2 dependents = 4 connections out of 4 possible
        assert score == 1.0

    def test_graph_centrality_moderately_connected(self):
        """Test graph centrality score for moderately connected file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "a.py": MagicMock(),
            "b.py": MagicMock(),
            "c.py": MagicMock(),
            "target.py": MagicMock(),
        }
        mock_mapper._repo_map.dependency_graph = {
            "target.py": {"a.py"},  # Depends on 1 file
            "b.py": {"target.py"},  # One dependent
        }

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._graph_centrality_score("target.py")
        # 1 dependency + 1 dependent = 2 connections out of 3 possible
        assert abs(score - (2 / 3)) < 0.01

    def test_graph_centrality_no_connections(self):
        """Test graph centrality score for file with no connections."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "target.py": MagicMock(),
        }
        mock_mapper._repo_map.dependency_graph = {}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._graph_centrality_score("target.py")
        assert score == 0.0

    def test_graph_centrality_single_file(self):
        """Test graph centrality score with only one file."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "target.py": MagicMock(),
        }
        mock_mapper._repo_map.dependency_graph = {}

        scorer = ImportanceScorer(mock_mapper)
        score = scorer._graph_centrality_score("target.py")
        assert score == 0.0


class TestContextBoost:
    """Test context-based score boosting."""

    def test_apply_context_boost_target_file(self):
        """Test context boost for target file."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        context = {"target_file": "main.py"}
        base_score = 0.5

        boosted = scorer._apply_context_boost(base_score, "main.py", context)
        assert boosted == min(1.0, 0.5 + 0.3)

    def test_apply_context_boost_same_directory(self):
        """Test context boost for file in same directory."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        context = {"target_file": "src/main.py"}
        base_score = 0.5

        boosted = scorer._apply_context_boost(base_score, "src/utils.py", context)
        assert boosted == min(1.0, 0.5 + 0.1)

    def test_apply_context_boost_fix_operation(self):
        """Test context boost for fix operation."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Mock dependency score
        with patch.object(scorer, "_dependency_score", return_value=0.6):
            context = {"target_file": "buggy.py", "operation": "fix"}
            base_score = 0.5

            boosted = scorer._apply_context_boost(base_score, "buggy.py", context)
            assert boosted == min(1.0, 0.5 + 0.3)  # Target file + fix operation

    def test_apply_context_boost_test_operation(self):
        """Test context boost for test operation."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        context = {"operation": "test"}
        base_score = 0.5

        boosted = scorer._apply_context_boost(base_score, "test_main.py", context)
        assert boosted == min(1.0, 0.5 + 0.2)

    def test_apply_context_boost_refactor_operation(self):
        """Test context boost for refactor operation."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Mock dependency score
        with patch.object(scorer, "_dependency_score", return_value=0.6):
            context = {"operation": "refactor"}
            base_score = 0.5

            boosted = scorer._apply_context_boost(base_score, "core.py", context)
            assert boosted == min(1.0, 0.5 + 0.15)


@pytest.mark.asyncio
class TestScoringIntegration:
    """Test integrated scoring functionality."""

    async def test_score_file_with_all_factors(self, tmp_path):
        """Test scoring a file with all factors considered."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()

        # Create a comprehensive file node
        node = FileNode(
            path="core.py",
            language="python",
            lines_of_code=100,
            functions=[
                FunctionSignature(
                    name="main", module_path="core", file_path="core.py", line_start=1, line_end=50
                )
            ],
            imports=["utils", "models"],
            dependencies={"utils.py", "models.py"},
            type_hints_coverage=0.8,
            has_docstring=True,
            last_modified=(datetime.now() - timedelta(days=3)).isoformat(),
        )

        mock_mapper._repo_map.modules = {"core.py": node}
        mock_mapper._repo_map.entry_points = ["core.py"]
        mock_mapper._repo_map.test_files = []
        mock_mapper._repo_map.dependency_graph = {
            "core.py": {"utils.py", "models.py"},
            "main.py": {"core.py"},
            "app.py": {"core.py"},
        }

        scorer = ImportanceScorer(mock_mapper)
        score = await scorer.score_file("core.py")

        # Should have a high score due to multiple factors
        assert 0.5 < score <= 1.0

        # Check cache was populated
        assert "core.py" in scorer._importance_cache
        assert scorer._importance_cache["core.py"].score == score

    async def test_score_file_not_in_repository(self):
        """Test scoring a file not in the repository."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {}

        scorer = ImportanceScorer(mock_mapper)
        score = await scorer.score_file("nonexistent.py")

        assert score == 0.0

    async def test_score_file_uses_cache(self):
        """Test that scoring uses cached results."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {"test.py": MagicMock()}

        scorer = ImportanceScorer(mock_mapper)

        # Pre-populate cache
        cached = FileImportance(
            file_path="test.py",
            score=0.75,
            factors={"recency": 1.0},
            last_calculated=datetime.now(),
        )
        scorer._importance_cache["test.py"] = cached

        score = await scorer.score_file("test.py")
        assert score == 0.75  # Should use cached value

    async def test_score_file_cache_expired(self):
        """Test that expired cache is refreshed."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {"test.py": MagicMock()}

        scorer = ImportanceScorer(mock_mapper)

        # Pre-populate expired cache
        cached = FileImportance(
            file_path="test.py",
            score=0.75,
            factors={"recency": 1.0},
            last_calculated=datetime.now() - timedelta(minutes=10),  # 10 minutes ago
        )
        scorer._importance_cache["test.py"] = cached

        with patch.object(scorer, "_recency_score", return_value=0.5):
            score = await scorer.score_file("test.py")
            # Should recalculate, not use cached value
            assert score != 0.75

    async def test_rank_files(self):
        """Test ranking multiple files by importance."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "high.py": MagicMock(),
            "medium.py": MagicMock(),
            "low.py": MagicMock(),
        }

        # Mock different scores
        async def mock_score(file_path, context=None):
            if file_path == "high.py":
                return 0.9
            elif file_path == "medium.py":
                return 0.6
            else:
                return 0.3

        scorer = ImportanceScorer(mock_mapper)
        scorer.score_file = mock_score

        ranked = await scorer.rank_files(["low.py", "high.py", "medium.py"])

        # Should be sorted by score descending
        assert ranked[0] == ("high.py", 0.9)
        assert ranked[1] == ("medium.py", 0.6)
        assert ranked[2] == ("low.py", 0.3)


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache(self):
        """Test clearing the importance cache."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Populate cache
        scorer._importance_cache["test.py"] = MagicMock()
        scorer._importance_cache["other.py"] = MagicMock()

        scorer.clear_cache()

        assert len(scorer._importance_cache) == 0

    def test_get_importance_factors_cached(self):
        """Test getting importance factors from cache."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        # Populate cache with factors
        factors = {"recency": 1.0, "dependencies": 0.5}
        cached = FileImportance(
            file_path="test.py", score=0.75, factors=factors, last_calculated=datetime.now()
        )
        scorer._importance_cache["test.py"] = cached

        retrieved = scorer.get_importance_factors("test.py")
        assert retrieved == factors

    def test_get_importance_factors_not_cached(self):
        """Test getting importance factors when not cached."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        retrieved = scorer.get_importance_factors("test.py")
        assert retrieved is None


@pytest.mark.asyncio
class TestTopFiles:
    """Test getting top files by importance."""

    async def test_get_top_files(self):
        """Test getting top N most important files."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = MagicMock()
        mock_mapper._repo_map.modules = {
            "file1.py": MagicMock(),
            "file2.py": MagicMock(),
            "file3.py": MagicMock(),
            "file4.py": MagicMock(),
            "file5.py": MagicMock(),
        }

        # Mock ranking
        async def mock_rank(file_paths, context=None):
            return [(f, 1.0 - i * 0.1) for i, f in enumerate(file_paths)]

        scorer = ImportanceScorer(mock_mapper)
        scorer.rank_files = mock_rank

        top_files = await scorer.get_top_files(limit=3)

        assert len(top_files) == 3
        assert top_files[0] == ("file1.py", 1.0)
        assert top_files[1] == ("file2.py", 0.9)
        assert top_files[2] == ("file3.py", 0.8)

    async def test_get_top_files_no_repo_map(self):
        """Test getting top files when no repository map."""
        mock_mapper = MagicMock()
        mock_mapper._repo_map = None

        scorer = ImportanceScorer(mock_mapper)
        top_files = await scorer.get_top_files()

        assert top_files == []


class TestWeightManagement:
    """Test weight management functionality."""

    def test_update_weights_valid(self):
        """Test updating weights with valid values."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        new_weights = {
            "recency": 0.3,
            "dependencies": 0.3,
            "entry_points": 0.2,
            "test_coverage": 0.1,
            "change_frequency": 0.05,
            "graph_centrality": 0.05,
        }

        scorer.update_weights(new_weights)

        assert scorer.WEIGHTS == new_weights
        # Cache should be cleared
        assert len(scorer._importance_cache) == 0

    def test_update_weights_invalid_sum(self):
        """Test updating weights that don't sum to 1.0."""
        mock_mapper = MagicMock()
        scorer = ImportanceScorer(mock_mapper)

        new_weights = {
            "recency": 0.5,
            "dependencies": 0.3,  # Total = 0.8, not 1.0
        }

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            scorer.update_weights(new_weights)
