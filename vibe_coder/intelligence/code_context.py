"""
Code context provider for AI operations.

This module provides intelligent context extraction for AI-powered
code generation, fixing, and refactoring operations.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.types import FileNode


class OperationType(Enum):
    """Types of AI operations."""

    GENERATE = "generate"
    FIX = "fix"
    REFACTOR = "refactor"
    EXPLAIN = "explain"
    TEST = "test"
    DOCUMENT = "document"


@dataclass
class ContextRequest:
    """Request for code context."""

    operation: OperationType
    target_file: Optional[str] = None
    target_function: Optional[str] = None
    target_class: Optional[str] = None
    related_files: Optional[List[str]] = None
    token_budget: int = 8000
    include_tests: bool = False
    include_docstrings: bool = True


@dataclass
class ContextResult:
    """Result of context extraction."""

    context: str
    files_included: List[str]
    functions_included: List[str]
    classes_included: List[str]
    token_estimate: int
    truncated: bool = False


class CodeContextProvider:
    """Provide relevant code context for AI operations."""

    # Approximate characters per token
    CHARS_PER_TOKEN = 4

    def __init__(self, repo_mapper: RepositoryMapper):
        self.repo_mapper = repo_mapper

    async def get_context(self, request: ContextRequest) -> ContextResult:
        """
        Get minimal sufficient context for operation.

        Args:
            request: Context request with operation type and parameters

        Returns:
            ContextResult with extracted context and metadata
        """
        # Ensure repository is scanned
        await self.repo_mapper.scan_repository()

        if request.operation == OperationType.GENERATE:
            return await self._get_generation_context(request)
        elif request.operation == OperationType.FIX:
            return await self._get_fix_context(request)
        elif request.operation == OperationType.REFACTOR:
            return await self._get_refactor_context(request)
        elif request.operation == OperationType.EXPLAIN:
            return await self._get_explain_context(request)
        elif request.operation == OperationType.TEST:
            return await self._get_test_context(request)
        elif request.operation == OperationType.DOCUMENT:
            return await self._get_document_context(request)
        else:
            return await self._get_generic_context(request)

    async def _get_generation_context(self, request: ContextRequest) -> ContextResult:
        """Get context for code generation."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Start with project overview
        overview = self._get_project_overview()
        lines.append(overview)
        current_chars += len(overview)

        # Add target file context if specified
        if request.target_file:
            file_context = await self._get_file_context(
                request.target_file,
                include_docstrings=request.include_docstrings,
            )
            if file_context and current_chars + len(file_context) < char_budget:
                lines.append("")
                lines.append(file_context)
                current_chars += len(file_context)
                files_included.append(request.target_file)

        # Add related files
        related = await self._get_related_files(
            request.target_file,
            request.related_files or [],
            char_budget - current_chars,
        )
        if related:
            lines.append("")
            lines.append("RELATED CODE:")
            lines.append(related["context"])
            current_chars += len(related["context"])
            files_included.extend(related["files"])
            functions_included.extend(related["functions"])

        # Add patterns from similar files
        patterns = self._get_code_patterns(request.target_file)
        if patterns and current_chars + len(patterns) < char_budget:
            lines.append("")
            lines.append("CODE PATTERNS:")
            lines.append(patterns)
            current_chars += len(patterns)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_fix_context(self, request: ContextRequest) -> ContextResult:
        """Get context for fixing code errors."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Focus on the file with the error
        if request.target_file:
            file_content = await self._read_file_content(request.target_file)
            if file_content:
                header = f"FILE TO FIX: {request.target_file}"
                lines.append(header)
                lines.append("```python")
                lines.append(file_content)
                lines.append("```")
                current_chars = sum(len(line) + 1 for line in lines)
                files_included.append(request.target_file)

        # Add relevant imports and dependencies
        if request.target_file and current_chars < char_budget:
            deps = await self._get_dependency_context(
                request.target_file,
                char_budget - current_chars,
            )
            if deps:
                lines.append("")
                lines.append("DEPENDENCIES:")
                lines.append(deps)
                current_chars += len(deps)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_refactor_context(self, request: ContextRequest) -> ContextResult:
        """Get context for refactoring operations."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Include the target file
        if request.target_file:
            file_content = await self._read_file_content(request.target_file)
            if file_content:
                header = f"FILE TO REFACTOR: {request.target_file}"
                lines.append(header)
                lines.append("```python")
                lines.append(file_content)
                lines.append("```")
                current_chars = sum(len(line) + 1 for line in lines)
                files_included.append(request.target_file)

        # Include files that use this file
        if request.target_file:
            usages = await self._get_usage_context(
                request.target_file,
                char_budget - current_chars,
            )
            if usages:
                lines.append("")
                lines.append("FILES THAT USE THIS CODE:")
                lines.append(usages)
                current_chars += len(usages)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_explain_context(self, request: ContextRequest) -> ContextResult:
        """Get context for explaining code."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Include the code to explain
        if request.target_file:
            file_content = await self._read_file_content(request.target_file)
            if file_content:
                header = f"CODE TO EXPLAIN: {request.target_file}"
                lines.append(header)
                lines.append("```python")
                lines.append(file_content)
                lines.append("```")
                current_chars = sum(len(line) + 1 for line in lines)
                files_included.append(request.target_file)

            # Include file metadata
            if self.repo_mapper._repo_map:
                rel_path = self._get_relative_path(request.target_file)
                node = self.repo_mapper._repo_map.modules.get(rel_path)
                if node:
                    meta = self._format_file_metadata(node)
                    if current_chars + len(meta) < char_budget:
                        lines.append("")
                        lines.append("FILE METADATA:")
                        lines.append(meta)
                        current_chars += len(meta)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_test_context(self, request: ContextRequest) -> ContextResult:
        """Get context for generating tests."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Include the code to test
        if request.target_file:
            file_content = await self._read_file_content(request.target_file)
            if file_content:
                header = f"CODE TO TEST: {request.target_file}"
                lines.append(header)
                lines.append("```python")
                lines.append(file_content)
                lines.append("```")
                current_chars = sum(len(line) + 1 for line in lines)
                files_included.append(request.target_file)

        # Include existing test patterns
        if request.include_tests:
            test_patterns = await self._get_test_patterns(char_budget - current_chars)
            if test_patterns:
                lines.append("")
                lines.append("EXISTING TEST PATTERNS:")
                lines.append(test_patterns)
                current_chars += len(test_patterns)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_document_context(self, request: ContextRequest) -> ContextResult:
        """Get context for documenting code."""
        lines = []
        files_included = []
        functions_included = []
        classes_included = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN
        current_chars = 0

        # Include the code to document
        if request.target_file:
            file_content = await self._read_file_content(request.target_file)
            if file_content:
                header = f"CODE TO DOCUMENT: {request.target_file}"
                lines.append(header)
                lines.append("```python")
                lines.append(file_content)
                lines.append("```")
                current_chars = sum(len(line) + 1 for line in lines)
                files_included.append(request.target_file)

            # Include existing documentation patterns
            doc_patterns = self._get_documentation_patterns()
            if doc_patterns and current_chars + len(doc_patterns) < char_budget:
                lines.append("")
                lines.append("DOCUMENTATION PATTERNS:")
                lines.append(doc_patterns)
                current_chars += len(doc_patterns)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=files_included,
            functions_included=functions_included,
            classes_included=classes_included,
            token_estimate=token_estimate,
            truncated=current_chars >= char_budget,
        )

    async def _get_generic_context(self, request: ContextRequest) -> ContextResult:
        """Get generic context."""
        lines = []
        char_budget = request.token_budget * self.CHARS_PER_TOKEN

        # Get compressed repository representation
        compressed = self.repo_mapper.compress_representation(max_tokens=request.token_budget)
        lines.append(compressed)

        context = "\n".join(lines)
        token_estimate = len(context) // self.CHARS_PER_TOKEN

        return ContextResult(
            context=context,
            files_included=[],
            functions_included=[],
            classes_included=[],
            token_estimate=token_estimate,
            truncated=len(context) >= char_budget,
        )

    def _get_project_overview(self) -> str:
        """Get brief project overview."""
        if not self.repo_mapper._repo_map:
            return "PROJECT: Unknown"

        repo = self.repo_mapper._repo_map
        lines = [
            f"PROJECT: {Path(repo.root_path).name}",
            f"FILES: {repo.total_files} | LINES: {repo.total_lines}",
        ]

        # Add main languages
        if repo.languages:
            top_langs = sorted(repo.languages.items(), key=lambda x: x[1], reverse=True)[:3]
            lang_str = ", ".join(f"{lang}: {count}" for lang, count in top_langs)
            lines.append(f"LANGUAGES: {lang_str}")

        return "\n".join(lines)

    async def _get_file_context(
        self, file_path: str, include_docstrings: bool = True
    ) -> Optional[str]:
        """Get context for a specific file."""
        if not self.repo_mapper._repo_map:
            return None

        rel_path = self._get_relative_path(file_path)
        node = self.repo_mapper._repo_map.modules.get(rel_path)

        if not node:
            return None

        lines = [f"FILE: {rel_path} ({node.lines_of_code} lines)"]

        # Add functions
        if node.functions:
            lines.append("FUNCTIONS:")
            for func in node.functions:
                lines.append(f"  - {func}")
                if include_docstrings and func.docstring:
                    doc_preview = func.docstring[:80].replace("\n", " ")
                    lines.append(f"      {doc_preview}...")

        # Add classes
        if node.classes:
            lines.append("CLASSES:")
            for cls in node.classes:
                lines.append(f"  - {cls}")
                for method in cls.methods[:5]:
                    lines.append(f"      - {method}")

        return "\n".join(lines)

    async def _get_related_files(
        self,
        target_file: Optional[str],
        related_files: List[str],
        char_budget: int,
    ) -> Optional[Dict]:
        """Get context for related files."""
        if not self.repo_mapper._repo_map:
            return None

        files = []
        functions = []
        lines = []
        current_chars = 0

        # Add explicitly related files
        for file_path in related_files:
            if current_chars >= char_budget:
                break

            rel_path = self._get_relative_path(file_path)
            node = self.repo_mapper._repo_map.modules.get(rel_path)
            if node:
                file_lines = self._format_file_summary(node)
                if current_chars + len(file_lines) < char_budget:
                    lines.append(file_lines)
                    current_chars += len(file_lines)
                    files.append(rel_path)
                    functions.extend(f.name for f in node.functions)

        # Add files from dependency graph
        if target_file:
            rel_target = self._get_relative_path(target_file)
            deps = self.repo_mapper._repo_map.dependency_graph.get(rel_target, set())
            for dep in deps:
                if current_chars >= char_budget:
                    break

                node = self.repo_mapper._repo_map.modules.get(dep)
                if node and dep not in files:
                    file_lines = self._format_file_summary(node)
                    if current_chars + len(file_lines) < char_budget:
                        lines.append(file_lines)
                        current_chars += len(file_lines)
                        files.append(dep)
                        functions.extend(f.name for f in node.functions)

        if not lines:
            return None

        return {
            "context": "\n".join(lines),
            "files": files,
            "functions": functions,
        }

    async def _get_dependency_context(self, file_path: str, char_budget: int) -> Optional[str]:
        """Get context for file dependencies."""
        if not self.repo_mapper._repo_map:
            return None

        rel_path = self._get_relative_path(file_path)
        node = self.repo_mapper._repo_map.modules.get(rel_path)

        if not node:
            return None

        lines = []
        current_chars = 0

        for dep in sorted(node.dependencies):
            dep_line = f"  - {dep}"
            if current_chars + len(dep_line) < char_budget:
                lines.append(dep_line)
                current_chars += len(dep_line) + 1

        return "\n".join(lines) if lines else None

    async def _get_usage_context(self, file_path: str, char_budget: int) -> Optional[str]:
        """Get context for files that use this file."""
        if not self.repo_mapper._repo_map:
            return None

        rel_path = self._get_relative_path(file_path)
        usages = []

        for file, deps in self.repo_mapper._repo_map.dependency_graph.items():
            if rel_path in deps:
                usages.append(file)

        if not usages:
            return None

        lines = []
        current_chars = 0

        for usage in usages[:10]:
            node = self.repo_mapper._repo_map.modules.get(usage)
            if node:
                usage_line = f"  - {usage} ({node.lines_of_code} lines)"
                if current_chars + len(usage_line) < char_budget:
                    lines.append(usage_line)
                    current_chars += len(usage_line) + 1

        return "\n".join(lines) if lines else None

    async def _get_test_patterns(self, char_budget: int) -> Optional[str]:
        """Get patterns from existing test files."""
        if not self.repo_mapper._repo_map:
            return None

        lines = []
        current_chars = 0

        for test_file in self.repo_mapper._repo_map.test_files[:3]:
            node = self.repo_mapper._repo_map.modules.get(test_file)
            if node and node.functions:
                lines.append(f"From {test_file}:")
                for func in node.functions[:3]:
                    func_line = f"  - {func}"
                    if current_chars + len(func_line) < char_budget:
                        lines.append(func_line)
                        current_chars += len(func_line) + 1

        return "\n".join(lines) if lines else None

    async def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content."""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.repo_mapper.root_path / path

            return path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return None

    def _get_relative_path(self, file_path: str) -> str:
        """Get path relative to repository root."""
        path = Path(file_path)
        if path.is_absolute():
            try:
                return str(path.relative_to(self.repo_mapper.root_path))
            except ValueError:
                return str(path)
        return str(path)

    def _format_file_summary(self, node: FileNode) -> str:
        """Format a brief file summary."""
        parts = [Path(node.path).name, f"({node.lines_of_code} lines)"]

        if node.functions:
            parts.append(f"{len(node.functions)} funcs")
        if node.classes:
            parts.append(f"{len(node.classes)} classes")

        return " ".join(parts)

    def _format_file_metadata(self, node: FileNode) -> str:
        """Format file metadata for context."""
        lines = [
            f"Language: {node.language}",
            f"Lines: {node.lines_of_code}",
            f"Functions: {len(node.functions)}",
            f"Classes: {len(node.classes)}",
            f"Type Coverage: {node.type_hints_coverage}%",
        ]
        return "\n".join(lines)

    def _get_code_patterns(self, target_file: Optional[str]) -> Optional[str]:
        """Get common code patterns from the project."""
        if not self.repo_mapper._repo_map or not target_file:
            return None

        lines = []
        rel_path = self._get_relative_path(target_file)

        # Find similar files (same directory)
        target_dir = str(Path(rel_path).parent)
        similar_files = []

        for file_path, node in self.repo_mapper._repo_map.modules.items():
            if str(Path(file_path).parent) == target_dir and file_path != rel_path:
                similar_files.append(node)

        if not similar_files:
            return None

        # Extract patterns from similar files
        common_imports = set()
        common_patterns = []

        for node in similar_files[:3]:
            common_imports.update(node.imports[:5])
            if node.classes:
                for cls in node.classes[:1]:
                    common_patterns.append(str(cls))

        if common_imports:
            lines.append("Common imports:")
            for imp in list(common_imports)[:5]:
                lines.append(f"  - {imp}")

        if common_patterns:
            lines.append("Common patterns:")
            for pattern in common_patterns[:3]:
                lines.append(f"  - {pattern}")

        return "\n".join(lines) if lines else None

    def _get_documentation_patterns(self) -> str:
        """Get documentation style patterns from the project."""
        lines = [
            "Documentation style:",
            "  - Use Google-style docstrings",
            "  - Include Args, Returns, Raises sections",
            "  - Type hints in function signatures",
            "  - Module docstring at file start",
        ]
        return "\n".join(lines)
