"""
Cross-file reference resolution for repository intelligence.

This module provides symbol tracking and reference resolution across
multiple files in a repository.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from vibe_coder.intelligence.types import Definition, FileNode, SymbolReference

if TYPE_CHECKING:
    from vibe_coder.intelligence.repo_mapper import RepositoryMapper


class ReferenceResolver:
    """Resolves cross-file symbol references."""

    def __init__(self, repo_mapper: "RepositoryMapper"):
        self.repo_mapper = repo_mapper
        self._symbol_index: Dict[str, List[Definition]] = {}  # symbol -> definitions
        self._reference_index: Dict[str, List[SymbolReference]] = {}  # file -> references
        self._import_map: Dict[str, str] = {}  # import_path -> actual_file_path
        self._dirty_files: Set[str] = set()

    async def build_indexes(self) -> None:
        """Build comprehensive symbol and reference indexes."""
        if not self.repo_mapper._repo_map:
            await self.repo_mapper.scan_repository()

        # Clear existing indexes
        self._symbol_index.clear()
        self._reference_index.clear()
        self._import_map.clear()

        # First pass: build symbol definitions and import map
        for file_path, node in self.repo_mapper._repo_map.modules.items():
            await self._index_definitions(file_path, node)

        # Second pass: resolve imports and map to actual files
        await self._resolve_imports()

        # Third pass: find all references
        for file_path, node in self.repo_mapper._repo_map.modules.items():
            await self._index_references(file_path, node)

    async def _index_definitions(self, file_path: str, node: FileNode) -> None:
        """Index all symbol definitions in a file."""
        # Index functions
        for func in node.functions:
            symbol = func.name
            if symbol not in self._symbol_index:
                self._symbol_index[symbol] = []

            self._symbol_index[symbol].append(
                Definition(
                    symbol=symbol,
                    file_path=file_path,
                    line_number=func.line_start,
                    column=0,  # AST doesn't provide column
                    type="function",
                    signature=str(func),
                    docstring=func.docstring,
                )
            )

        # Index classes and their methods
        for cls in node.classes:
            # Index class itself
            symbol = cls.name
            if symbol not in self._symbol_index:
                self._symbol_index[symbol] = []

            self._symbol_index[symbol].append(
                Definition(
                    symbol=symbol,
                    file_path=file_path,
                    line_number=cls.line_start,
                    column=0,
                    type="class",
                    signature=str(cls),
                    docstring=cls.docstring,
                )
            )

            # Index methods
            for method in cls.methods:
                # Method names include class scope for uniqueness
                method_symbol = f"{cls.name}.{method.name}"
                if method_symbol not in self._symbol_index:
                    self._symbol_index[method_symbol] = []

                self._symbol_index[method_symbol].append(
                    Definition(
                        symbol=method_symbol,
                        file_path=file_path,
                        line_number=method.line_start,
                        column=0,
                        type="method",
                        signature=str(method),
                        docstring=method.docstring,
                    )
                )

    async def _resolve_imports(self) -> None:
        """Resolve import statements to actual file paths."""
        if not self.repo_mapper._repo_map:
            return

        for file_path, node in self.repo_mapper._repo_map.modules.items():
            file_dir = os.path.dirname(file_path)

            for import_path in node.imports:
                # Try to resolve to actual file
                resolved_path = await self._resolve_import_path(import_path, file_dir)
                if resolved_path:
                    self._import_map[import_path] = resolved_path

    async def _resolve_import_path(
        self, import_path: str, from_dir: str
    ) -> Optional[str]:
        """Resolve an import path to an actual file path."""
        # Convert import path to potential file paths
        parts = import_path.split(".")

        # Try different patterns
        patterns = []

        # Try as module (e.g., foo.bar -> foo/bar.py)
        patterns.append("/".join(parts) + ".py")

        # Try as package (e.g., foo.bar -> foo/bar/__init__.py)
        patterns.append("/".join(parts) + "/__init__.py")

        # Try relative imports (if starts with .)
        if import_path.startswith("."):
            relative_parts = import_path.lstrip(".").split(".")
            levels = len(import_path) - len(import_path.lstrip("."))

            # Go up the directory structure
            target_dir = from_dir
            for _ in range(levels):
                target_dir = os.path.dirname(target_dir)

            for i, part in enumerate(relative_parts):
                if i < len(relative_parts) - 1:
                    target_dir = os.path.join(target_dir, part)
                else:
                    # Last part - try as file or package
                    patterns.append(os.path.join(target_dir, part + ".py"))
                    patterns.append(os.path.join(target_dir, part, "__init__.py"))

        # Check if any pattern matches a file in the repository
        for pattern in patterns:
            for repo_file in self.repo_mapper._repo_map.modules.keys():
                if repo_file.endswith(pattern):
                    return repo_file

        return None

    async def _index_references(self, file_path: str, node: FileNode) -> None:
        """Index all symbol references in a file."""
        if file_path not in self._reference_index:
            self._reference_index[file_path] = []

        # For Python files, we could parse AST to find references
        # For now, we'll use a simpler approach based on available data

        # Track imported symbols
        imported_symbols = set()
        for import_path in node.imports:
            imported_symbols.add(import_path.split(".")[-1])  # Get last part

            # Also check if this import defines symbols we can reference
            resolved_path = self._import_map.get(import_path)
            if resolved_path and resolved_path in self.repo_mapper._repo_map.modules:
                imported_node = self.repo_mapper._repo_map.modules[resolved_path]

                # Add all top-level symbols from imported module
                for func in imported_node.functions:
                    imported_symbols.add(func.name)
                for cls in imported_node.classes:
                    imported_symbols.add(cls.name)

        # In a full implementation, we would parse the file content with AST
        # to find all Name nodes and check if they reference our indexed symbols
        # For now, we'll create placeholder references for imported symbols

        for symbol in imported_symbols:
            # This is a simplified approach - in reality, we'd parse the AST
            # to find actual usage locations and context
            self._reference_index[file_path].append(
                SymbolReference(
                    name=symbol,
                    file_path=file_path,
                    line_number=1,  # Would be actual line from AST
                    column=1,  # Would be actual column from AST
                    reference_type="usage",
                    context=f"Imported symbol {symbol}",
                    symbol_type="unknown",
                )
            )

    async def find_references(
        self, symbol: str, file_path: Optional[str] = None
    ) -> List[SymbolReference]:
        """
        Find all references to a symbol.

        Args:
            symbol: The symbol to search for.
            file_path: If specified, only search in this file.

        Returns:
            List of symbol references.
        """
        references = []

        if file_path:
            # Search in specific file
            if file_path in self._reference_index:
                for ref in self._reference_index[file_path]:
                    if ref.name == symbol or ref.name.endswith(f".{symbol}"):
                        references.append(ref)
        else:
            # Search in all files
            for refs in self._reference_index.values():
                for ref in refs:
                    if ref.name == symbol or ref.name.endswith(f".{symbol}"):
                        references.append(ref)

        return references

    async def find_definition(
        self, symbol: str, from_file: Optional[str] = None
    ) -> Optional[Definition]:
        """
        Find where a symbol is defined.

        Args:
            symbol: The symbol to find.
            from_file: The file where the symbol is referenced (for context).

        Returns:
            The definition location or None if not found.
        """
        # Check exact symbol match
        if symbol in self._symbol_index:
            definitions = self._symbol_index[symbol]
            if len(definitions) == 1:
                return definitions[0]

            # Multiple definitions - try to find the best one
            if from_file:
                # Prefer definitions in the same file
                for defn in definitions:
                    if defn.file_path == from_file:
                        return defn

                # Prefer definitions in imported modules
                if from_file in self.repo_mapper._repo_map.modules:
                    node = self.repo_mapper._repo_map.modules[from_file]
                    for imp in node.imports:
                        if imp in self._import_map:
                            resolved_path = self._import_map[imp]
                            for defn in definitions:
                                if defn.file_path == resolved_path:
                                    return defn

            # Return the first definition if no better match found
            return definitions[0]

        # Check for qualified names (e.g., Class.method)
        if "." in symbol:
            parts = symbol.split(".")
            if parts[0] in self._symbol_index:
                for defn in self._symbol_index[parts[0]]:
                    if defn.type == "class":
                        # Look for the method in the class
                        class_name = defn.symbol
                        method_name = parts[1]
                        qualified_method = f"{class_name}.{method_name}"
                        if qualified_method in self._symbol_index:
                            method_defs = self._symbol_index[qualified_method]
                            return method_defs[0] if method_defs else None

        return None

    async def get_dependencies(
        self, file_path: str, include_indirect: bool = False
    ) -> List[str]:
        """
        Get all files that this file depends on.

        Args:
            file_path: The file to analyze.
            include_indirect: Whether to include indirect dependencies.

        Returns:
            List of dependent file paths.
        """
        if not self.repo_mapper._repo_map or file_path not in self.repo_mapper._repo_map.modules:
            return []

        node = self.repo_mapper._repo_map.modules[file_path]
        dependencies = set()

        # Direct dependencies from import map
        for import_path in node.imports:
            if import_path in self._import_map:
                resolved_path = self._import_map[import_path]
                dependencies.add(resolved_path)

                # Add indirect dependencies if requested
                if include_indirect:
                    indirect_deps = await self.get_dependencies(resolved_path, True)
                    dependencies.update(indirect_deps)

        return list(dependencies)

    async def get_dependents(self, file_path: str) -> List[str]:
        """
        Get all files that depend on this file.

        Args:
            file_path: The file to analyze.

        Returns:
            List of dependent file paths.
        """
        dependents = []

        if not self.repo_mapper._repo_map:
            return dependents

        for other_file, node in self.repo_mapper._repo_map.modules.items():
            if other_file == file_path:
                continue

            # Check if this file imports the target file
            for import_path in node.imports:
                if import_path in self._import_map:
                    if self._import_map[import_path] == file_path:
                        dependents.append(other_file)
                        break

        return dependents

    def get_symbol_statistics(self) -> Dict:
        """Get statistics about indexed symbols."""
        total_symbols = len(self._symbol_index)
        total_definitions = sum(len(defs) for defs in self._symbol_index.values())
        total_references = sum(len(refs) for refs in self._reference_index.values())

        # Most referenced symbols
        symbol_ref_counts = {}
        for refs in self._reference_index.values():
            for ref in refs:
                symbol_ref_counts[ref.name] = symbol_ref_counts.get(ref.name, 0) + 1

        most_referenced = sorted(
            symbol_ref_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_symbols": total_symbols,
            "total_definitions": total_definitions,
            "total_references": total_references,
            "most_referenced_symbols": most_referenced,
        }