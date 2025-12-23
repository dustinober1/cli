"""
Repository mapping and analysis.

This module provides high-level repository scanning, dependency graph building,
and caching capabilities for efficient code analysis.
"""

import asyncio
import fnmatch
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from vibe_coder.intelligence.ast_analyzer import PythonASTAnalyzer
from vibe_coder.intelligence.file_monitor import FileWatcher
from vibe_coder.intelligence.importance_scorer import ImportanceScorer
from vibe_coder.intelligence.reference_resolver import ReferenceResolver
from vibe_coder.intelligence.types import ContextItem, FileEvent, FileNode, RepositoryMap


class RepositoryMapper:
    """High-level repository analysis orchestrator."""

    # Default patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        "*.egg-info",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        "*.min.js",
        "*.bundle.js",
    ]

    # File extensions to analyze
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }

    def __init__(
        self,
        root_path: str,
        cache_dir: Optional[str] = None,
        ignore_patterns: Optional[List[str]] = None,
        enable_monitoring: bool = False,
        enable_importance_scoring: bool = True,
        enable_reference_resolution: bool = True,
    ):
        self.root_path = Path(root_path).resolve()
        self.cache_dir = Path(cache_dir) if cache_dir else self.root_path / ".vibe_cache"
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS

        # Language-specific analyzers
        self.python_analyzer = PythonASTAnalyzer()

        # In-memory cache
        self._repo_map: Optional[RepositoryMap] = None
        self._file_cache: Dict[str, FileNode] = {}

        # Enhanced features
        self.enable_monitoring = enable_monitoring
        self.enable_importance_scoring = enable_importance_scoring
        self.enable_reference_resolution = enable_reference_resolution

        # Initialize components
        self.file_watcher: Optional[FileWatcher] = None
        self.importance_scorer: Optional[ImportanceScorer] = None
        self.reference_resolver: Optional[ReferenceResolver] = None

        if self.enable_importance_scoring:
            self.importance_scorer = ImportanceScorer(self)

        if self.enable_reference_resolution:
            self.reference_resolver = ReferenceResolver(self)

    async def scan_repository(self, use_cache: bool = True) -> RepositoryMap:
        """
        Complete repository scan with caching.

        Args:
            use_cache: Whether to use cached results if available

        Returns:
            RepositoryMap with complete codebase structure
        """
        # Try to load from cache
        if use_cache and self._repo_map:
            return self._repo_map

        if use_cache:
            cached = self._load_cache()
            if cached:
                self._repo_map = cached
                return cached

        # Discover all files
        files = self._discover_files()

        # Analyze files in parallel
        file_nodes = await self._analyze_files(files)

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(file_nodes)

        # Identify entry points and test files
        entry_points = self._find_entry_points(file_nodes)
        test_files = self._find_test_files(files)

        # Calculate statistics
        total_lines = sum(node.lines_of_code for node in file_nodes.values())
        languages = self._count_languages(file_nodes)

        self._repo_map = RepositoryMap(
            root_path=str(self.root_path),
            total_files=len(file_nodes),
            total_lines=total_lines,
            languages=languages,
            modules=file_nodes,
            dependency_graph=dependency_graph,
            entry_points=entry_points,
            test_files=test_files,
            generated_at=datetime.now().isoformat(),
        )

        # Save to cache
        self._save_cache(self._repo_map)

        # Initialize reference resolver after scanning
        if self.enable_reference_resolution and self.reference_resolver:
            await self.reference_resolver.build_indexes()

        return self._repo_map

    def _discover_files(self) -> List[Path]:
        """Find all analyzable files in the repository."""
        files = []

        for root, dirs, filenames in os.walk(self.root_path):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not any(fnmatch.fnmatch(d, pattern) for pattern in self.ignore_patterns)
            ]

            for filename in filenames:
                # Check if file matches ignore patterns
                if any(fnmatch.fnmatch(filename, pattern) for pattern in self.ignore_patterns):
                    continue

                file_path = Path(root) / filename
                ext = file_path.suffix.lower()

                if ext in self.LANGUAGE_EXTENSIONS:
                    files.append(file_path)

        return files

    async def _analyze_files(self, files: List[Path]) -> Dict[str, FileNode]:
        """Analyze all files in parallel."""
        file_nodes = {}

        # Create tasks for parallel analysis
        tasks = []
        for file_path in files:
            ext = file_path.suffix.lower()
            language = self.LANGUAGE_EXTENSIONS.get(ext, "unknown")

            if language == "python":
                tasks.append(self._analyze_python_file(file_path))
            else:
                # For non-Python files, create basic FileNode
                tasks.append(self._create_basic_file_node(file_path, language))

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, FileNode):
                # Use relative path as key
                rel_path = str(Path(result.path).relative_to(self.root_path))
                file_nodes[rel_path] = result
            elif isinstance(result, Exception):
                # Log error but continue
                pass

        return file_nodes

    async def _analyze_python_file(self, file_path: Path) -> Optional[FileNode]:
        """Analyze a Python file."""
        return await self.python_analyzer.analyze_file(str(file_path))

    async def _create_basic_file_node(self, file_path: Path, language: str) -> FileNode:
        """Create a basic FileNode for non-Python files."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = len(content.splitlines())
        except (UnicodeDecodeError, IOError):
            lines = 0

        return FileNode(
            path=str(file_path),
            language=language,
            lines_of_code=lines,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
        )

    def _build_dependency_graph(self, file_nodes: Dict[str, FileNode]) -> Dict[str, Set[str]]:
        """Create import/dependency relationships."""
        graph: Dict[str, Set[str]] = {}

        for file_path, node in file_nodes.items():
            deps = set()

            for imp in node.imports:
                # Try to find matching file in repository
                matching_file = self._find_import_file(imp, file_nodes)
                if matching_file:
                    deps.add(matching_file)

            if deps:
                graph[file_path] = deps

        return graph

    def _find_import_file(self, import_path: str, file_nodes: Dict[str, FileNode]) -> Optional[str]:
        """Find the file that corresponds to an import path."""
        # Convert import path to potential file paths
        parts = import_path.split(".")
        potential_paths = []

        # Try as module
        module_path = "/".join(parts) + ".py"
        potential_paths.append(module_path)

        # Try as package
        package_path = "/".join(parts) + "/__init__.py"
        potential_paths.append(package_path)

        for path in potential_paths:
            for file_path in file_nodes.keys():
                if file_path.endswith(path):
                    return file_path

        return None

    def _find_entry_points(self, file_nodes: Dict[str, FileNode]) -> List[str]:
        """Identify entry points in the codebase."""
        entry_points = []

        for file_path, node in file_nodes.items():
            # Check for common entry point patterns
            if "cli.py" in file_path or "main.py" in file_path:
                entry_points.append(file_path)
                continue

            # Check for __main__ block
            for func in node.functions:
                if func.name == "main":
                    entry_points.append(file_path)
                    break

        return sorted(set(entry_points))

    def _find_test_files(self, files: List[Path]) -> List[str]:
        """Identify test files."""
        test_files = []

        for file_path in files:
            name = file_path.name.lower()
            if name.startswith("test_") or name.endswith("_test.py"):
                rel_path = str(file_path.relative_to(self.root_path))
                test_files.append(rel_path)
            elif "tests" in file_path.parts or "test" in file_path.parts:
                rel_path = str(file_path.relative_to(self.root_path))
                test_files.append(rel_path)

        return sorted(set(test_files))

    def _count_languages(self, file_nodes: Dict[str, FileNode]) -> Dict[str, int]:
        """Count files by language."""
        counts: Dict[str, int] = {}
        for node in file_nodes.values():
            counts[node.language] = counts.get(node.language, 0) + 1
        return counts

    def compress_representation(self, max_tokens: int = 8000) -> str:
        """
        Create AI-friendly compressed representation.

        Args:
            max_tokens: Approximate token budget (chars / 4)

        Returns:
            Compressed string representation suitable for AI context
        """
        if not self._repo_map:
            return "Repository not scanned yet."

        lines = [
            f"PROJECT: {self.root_path.name}",
            f"FILES: {self._repo_map.total_files}",
            f"LINES: {self._repo_map.total_lines}",
            "",
            "STRUCTURE:",
        ]

        # Group files by directory
        dirs: Dict[str, List[FileNode]] = {}
        for file_path, node in self._repo_map.modules.items():
            dir_path = str(Path(file_path).parent)
            if dir_path not in dirs:
                dirs[dir_path] = []
            dirs[dir_path].append(node)

        # Build tree representation
        char_budget = max_tokens * 4  # Approximate chars per token
        current_chars = len("\n".join(lines))

        for dir_path in sorted(dirs.keys()):
            if current_chars > char_budget:
                lines.append("  ... (truncated)")
                break

            dir_line = f"  {dir_path}/"
            lines.append(dir_line)
            current_chars += len(dir_line) + 1

            for node in sorted(dirs[dir_path], key=lambda n: n.path):
                if current_chars > char_budget:
                    break

                file_name = Path(node.path).name
                func_count = len(node.functions)
                class_count = len(node.classes)

                parts = [file_name, f"({node.lines_of_code} lines)"]
                if func_count:
                    parts.append(f"{func_count} funcs")
                if class_count:
                    parts.append(f"{class_count} classes")

                file_line = f"    {' '.join(parts)}"
                lines.append(file_line)
                current_chars += len(file_line) + 1

                # Add function signatures (brief)
                for func in node.functions[:3]:  # Limit to first 3
                    if current_chars > char_budget:
                        break
                    func_line = f"      - {func}"
                    lines.append(func_line)
                    current_chars += len(func_line) + 1

                # Add class names
                for cls in node.classes[:3]:
                    if current_chars > char_budget:
                        break
                    cls_line = f"      - {cls}"
                    lines.append(cls_line)
                    current_chars += len(cls_line) + 1

        # Add dependencies section
        if self._repo_map.dependency_graph and current_chars < char_budget:
            lines.append("")
            lines.append("DEPENDENCIES:")

            all_deps = set()
            for node in self._repo_map.modules.values():
                all_deps.update(node.dependencies)

            for dep in sorted(all_deps):
                if current_chars > char_budget:
                    break
                dep_line = f"  - {dep}"
                lines.append(dep_line)
                current_chars += len(dep_line) + 1

        # Add entry points
        if self._repo_map.entry_points and current_chars < char_budget:
            lines.append("")
            lines.append("ENTRY POINTS:")
            for ep in self._repo_map.entry_points[:5]:
                ep_line = f"  - {ep}"
                lines.append(ep_line)
                current_chars += len(ep_line) + 1

        return "\n".join(lines)

    async def update_on_file_change(self, file_path: str) -> None:
        """Incrementally update cache on file changes."""
        path = Path(file_path)
        if not path.exists():
            # File was deleted
            rel_path = str(path.relative_to(self.root_path))
            if self._repo_map and rel_path in self._repo_map.modules:
                del self._repo_map.modules[rel_path]
            return

        # Re-analyze the file
        ext = path.suffix.lower()
        if ext == ".py":
            node = await self.python_analyzer.analyze_file(str(path))
            if node and self._repo_map:
                rel_path = str(path.relative_to(self.root_path))
                self._repo_map.modules[rel_path] = node
                self._repo_map.generated_at = datetime.now().isoformat()

    def get_context_for_file(self, file_path: str, context_size: int = 8000) -> str:
        """
        Get relevant context for code generation.

        Args:
            file_path: Target file for context
            context_size: Token budget

        Returns:
            Related files and functions within token budget
        """
        if not self._repo_map:
            return ""

        rel_path = str(Path(file_path).relative_to(self.root_path))
        target_node = self._repo_map.modules.get(rel_path)

        if not target_node:
            return f"File not found in repository: {file_path}"

        lines = [
            f"CONTEXT FOR: {rel_path}",
            "",
            "FILE OVERVIEW:",
            f"  Language: {target_node.language}",
            f"  Lines: {target_node.lines_of_code}",
        ]

        # Add imports
        if target_node.imports:
            lines.append("")
            lines.append("IMPORTS:")
            for imp in target_node.imports[:10]:
                lines.append(f"  - {imp}")

        # Add functions
        if target_node.functions:
            lines.append("")
            lines.append("FUNCTIONS:")
            for func in target_node.functions:
                lines.append(f"  - {func}")
                if func.docstring:
                    doc_preview = func.docstring[:100].replace("\n", " ")
                    lines.append(f"      {doc_preview}")

        # Add classes
        if target_node.classes:
            lines.append("")
            lines.append("CLASSES:")
            for cls in target_node.classes:
                lines.append(f"  - {cls}")
                for method in cls.methods[:5]:
                    lines.append(f"      - {method}")

        # Add related files from dependency graph
        if rel_path in self._repo_map.dependency_graph:
            lines.append("")
            lines.append("DEPENDENCIES:")
            for dep in self._repo_map.dependency_graph[rel_path]:
                lines.append(f"  - {dep}")

        # Add files that depend on this file
        dependents = []
        for file, deps in self._repo_map.dependency_graph.items():
            if rel_path in deps:
                dependents.append(file)

        if dependents:
            lines.append("")
            lines.append("USED BY:")
            for dep in dependents[:5]:
                lines.append(f"  - {dep}")

        return "\n".join(lines)

    def _load_cache(self) -> Optional[RepositoryMap]:
        """Load cached repository map from disk."""
        cache_file = self.cache_dir / "repo_map.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RepositoryMap.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_cache(self, repo_map: RepositoryMap) -> None:
        """Save repository map to disk cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "repo_map.json"

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(repo_map.to_dict(), f, indent=2)

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._repo_map = None
        self._file_cache.clear()
        self.python_analyzer.clear_cache()

        cache_file = self.cache_dir / "repo_map.json"
        if cache_file.exists():
            cache_file.unlink()

    def get_stats(self) -> Dict:
        """Get repository statistics."""
        if not self._repo_map:
            return {"status": "not_scanned"}

        return {
            "root_path": str(self.root_path),
            "total_files": self._repo_map.total_files,
            "total_lines": self._repo_map.total_lines,
            "languages": self._repo_map.languages,
            "entry_points": len(self._repo_map.entry_points),
            "test_files": len(self._repo_map.test_files),
            "generated_at": self._repo_map.generated_at,
        }

    # Enhanced features methods

    def start_monitoring(self, on_file_change=None) -> None:
        """Start real-time file monitoring."""
        if not self.enable_monitoring:
            return

        if not self.file_watcher:
            self.file_watcher = FileWatcher(self, on_file_change)

        self.file_watcher.start_monitoring()

    def stop_monitoring(self) -> None:
        """Stop real-time file monitoring."""
        if self.file_watcher:
            self.file_watcher.stop_monitoring()

    async def compress_with_importance(
        self,
        max_tokens: int = 8000,
        target_file: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> str:
        """
        Create AI-friendly compressed representation with importance scoring.

        Args:
            max_tokens: Approximate token budget
            target_file: File being operated on for context
            operation: Type of operation for context

        Returns:
            Compressed string representation suitable for AI context
        """
        if not self._repo_map:
            return "Repository not scanned yet."

        # If importance scoring is disabled, use original method
        if not self.enable_importance_scoring or not self.importance_scorer:
            return self.compress_representation(max_tokens)

        # Score all files
        context = {"target_file": target_file, "operation": operation}
        scored_files = []

        for file_path, node in self._repo_map.modules.items():
            importance = await self.importance_scorer.score_file(file_path, context)
            scored_files.append((file_path, node, importance))

        # Sort by importance
        scored_files.sort(key=lambda x: x[2], reverse=True)

        lines = []
        lines.append(f"PROJECT: {self.root_path.name}")
        lines.append(f"FILES: {self._repo_map.total_files} | LINES: {self._repo_map.total_lines}")

        # Add languages
        if self._repo_map.languages:
            top_langs = sorted(self._repo_map.languages.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            lang_str = ", ".join(f"{lang}: {count}" for lang, count in top_langs)
            lines.append(f"LANGUAGES: {lang_str}")

        lines.append("")
        lines.append("STRUCTURE (by importance):")

        # Build compressed view with importance
        char_budget = max_tokens * 4  # Approximate chars per token
        current_chars = len("\n".join(lines))

        # Always include target file first
        if target_file and target_file in self._repo_map.modules:
            target_node = self._repo_map.modules[target_file]
            target_repr = self._format_file_with_importance(
                target_node, 1.0, char_budget - current_chars
            )
            if target_repr:
                lines.append(target_repr)
                current_chars += len(target_repr) + 1

        # Add other files by importance
        for file_path, node, importance in scored_files:
            if current_chars >= char_budget:
                lines.append("  ... (truncated)")
                break

            if file_path == target_file:
                continue  # Already included

            file_repr = self._format_file_with_importance(
                node, importance, char_budget - current_chars
            )
            if file_repr:
                lines.append(file_repr)
                current_chars += len(file_repr) + 1

        return "\n".join(lines)

    def _format_file_with_importance(
        self, node: FileNode, importance: float, char_budget: int
    ) -> Optional[str]:
        """Format a file representation based on importance."""
        rel_path = str(Path(node.path).relative_to(self.root_path))

        if importance > 0.8:
            # High importance - include full details
            lines = [f"  {rel_path} (HIGH - {node.lines_of_code} lines)"]

            if node.functions:
                lines.append("    FUNCTIONS:")
                for func in node.functions[:5]:
                    lines.append(f"      - {func}")

            if node.classes:
                lines.append("    CLASSES:")
                for cls in node.classes[:3]:
                    lines.append(f"      - {cls}")

        elif importance > 0.5:
            # Medium importance - include summary
            parts = [rel_path, f"({node.lines_of_code} lines)"]
            if node.functions:
                parts.append(f"{len(node.functions)} funcs")
            if node.classes:
                parts.append(f"{len(node.classes)} classes")
            lines = [f"  {' '.join(parts)}"]

        elif importance > 0.2:
            # Low importance - minimal info
            lines = [f"  {rel_path} ({node.lines_of_code} lines)"]
        else:
            return None  # Skip very low importance files

        result = "\n".join(lines)
        return result if len(result) <= char_budget else None

    async def get_context_items(
        self,
        target_file: Optional[str] = None,
        operation: Optional[str] = None,
        max_items: int = 20,
    ) -> List[ContextItem]:
        """
        Get context items for AI operations.

        Args:
            target_file: Target file for context
            operation: Type of operation
            max_items: Maximum number of items to return

        Returns:
            List of context items with importance scores
        """
        if not self._repo_map:
            return []

        context_items = []
        context = {"target_file": target_file, "operation": operation}

        # Get scored files
        if self.enable_importance_scoring and self.importance_scorer:
            scored_files = await self.importance_scorer.rank_files(
                list(self._repo_map.modules.keys()), context
            )
        else:
            # Default ordering without importance scoring
            scored_files = [(fp, 0.5) for fp in self._repo_map.modules.keys()]

        for file_path, importance in scored_files[:max_items]:
            node = self._repo_map.modules[file_path]

            # Create context item
            content = self._get_file_summary(node)
            estimated_tokens = len(content) // 4  # Rough estimate

            item = ContextItem(
                path=file_path,
                content=content,
                importance=importance,
                token_count=estimated_tokens,
                type="file",
                metadata={
                    "language": node.language,
                    "lines_of_code": node.lines_of_code,
                    "functions": len(node.functions),
                    "classes": len(node.classes),
                },
            )

            context_items.append(item)

        return context_items

    def _get_file_summary(self, node: FileNode) -> str:
        """Get a summary of a file's content."""
        lines = [f"File: {Path(node.path).name} ({node.lines_of_code} lines)"]

        if node.functions:
            lines.append("Functions:")
            for func in node.functions[:5]:
                lines.append(f"  - {func}")

        if node.classes:
            lines.append("Classes:")
            for cls in node.classes[:3]:
                lines.append(f"  - {cls}")

        return "\n".join(lines)
