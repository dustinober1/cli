"""
AST-based code analyzer for Python files.

This module provides deep code analysis using Python's Abstract Syntax Tree,
extracting function signatures, class definitions, imports, and complexity metrics.
"""

import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from vibe_coder.intelligence.types import ClassSignature, FileNode, FunctionSignature


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity of a function."""

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each 'and' or 'or' adds complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.complexity += 1
        # Count ifs in comprehension
        self.complexity += len(node.ifs)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        # Ternary operator
        self.complexity += 1
        self.generic_visit(node)


def calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST node."""
    visitor = ComplexityVisitor()
    visitor.visit(node)
    return visitor.complexity


class PythonASTAnalyzer:
    """Analyze Python files using AST."""

    def __init__(self):
        self._cache: Dict[str, Tuple[float, FileNode]] = {}

    async def analyze_file(self, file_path: str) -> Optional[FileNode]:
        """
        Extract metadata from Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            FileNode with extracted metadata, or None if parsing fails
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None

        # Check cache
        mtime = path.stat().st_mtime
        if file_path in self._cache:
            cached_mtime, cached_node = self._cache[file_path]
            if cached_mtime == mtime:
                return cached_node

        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=file_path)
        except (SyntaxError, UnicodeDecodeError):
            return None

        # Extract module path from file path
        module_path = self._get_module_path(file_path)

        # Count lines
        lines_of_code = len(content.splitlines())

        # Extract functions and classes
        functions = self.extract_functions(tree, module_path, file_path)
        classes = self.extract_classes(tree, module_path, file_path)

        # Extract imports
        imports = self.extract_imports(tree)

        # Calculate type hints coverage
        type_hints_coverage = self._calculate_type_hints_coverage(functions, classes)

        # Check for module docstring
        has_docstring = ast.get_docstring(tree) is not None

        # Get dependencies from imports
        dependencies = self._extract_dependencies(imports)

        file_node = FileNode(
            path=file_path,
            language="python",
            lines_of_code=lines_of_code,
            functions=functions,
            classes=classes,
            imports=imports,
            dependencies=dependencies,
            type_hints_coverage=type_hints_coverage,
            has_docstring=has_docstring,
            last_modified=datetime.fromtimestamp(mtime).isoformat(),
        )

        # Update cache
        self._cache[file_path] = (mtime, file_node)

        return file_node

    def extract_functions(
        self, tree: ast.Module, module_path: str, file_path: str
    ) -> List[FunctionSignature]:
        """Walk AST and extract function metadata."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods (they're inside classes)
                parent = self._get_parent(tree, node)
                if isinstance(parent, ast.ClassDef):
                    continue

                func = self._extract_function_signature(
                    node, module_path, file_path, is_method=False
                )
                functions.append(func)

        return functions

    def extract_classes(
        self, tree: ast.Module, module_path: str, file_path: str
    ) -> List[ClassSignature]:
        """Walk AST and extract class metadata."""
        classes = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._extract_class_signature(node, module_path, file_path)
                classes.append(cls)

        return classes

    def extract_imports(self, tree: ast.Module) -> List[str]:
        """Extract all import statements."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        imports.append(f"{module}.{alias.name}")
                    else:
                        imports.append(alias.name)

        return imports

    def _extract_function_signature(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_path: str,
        file_path: str,
        is_method: bool = False,
    ) -> FunctionSignature:
        """Extract metadata from a function definition."""
        # Get parameters
        parameters = []
        for arg in node.args.args:
            param_name = arg.arg
            if arg.annotation:
                param_type = self._get_annotation_string(arg.annotation)
                param_name = f"{param_name}: {param_type}"
            parameters.append(param_name)

        # Get return type
        return_type = None
        if node.returns:
            return_type = self._get_annotation_string(node.returns)

        # Get docstring
        docstring = ast.get_docstring(node)

        # Calculate complexity
        complexity = calculate_complexity(node)

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        return FunctionSignature(
            name=node.name,
            module_path=module_path,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            complexity=complexity,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            decorators=decorators,
        )

    def _extract_class_signature(
        self, node: ast.ClassDef, module_path: str, file_path: str
    ) -> ClassSignature:
        """Extract metadata from a class definition."""
        # Get base classes
        bases = []
        for base in node.bases:
            bases.append(self._get_annotation_string(base))

        # Get methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_function_signature(
                    item, module_path, file_path, is_method=True
                )
                methods.append(method)

        # Get class attributes
        attributes = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_name = item.target.id
                if item.annotation:
                    attr_type = self._get_annotation_string(item.annotation)
                    attr_name = f"{attr_name}: {attr_type}"
                attributes.append(attr_name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Check if dataclass
        is_dataclass = "dataclass" in decorators

        return ClassSignature(
            name=node.name,
            module_path=module_path,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            bases=bases,
            methods=methods,
            attributes=attributes,
            docstring=docstring,
            decorators=decorators,
            is_dataclass=is_dataclass,
        )

    def _get_annotation_string(self, node: ast.AST) -> str:
        """Convert an annotation AST node to string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation_string(node.value)
            slice_val = self._get_annotation_string(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Attribute):
            value = self._get_annotation_string(node.value)
            return f"{value}.{node.attr}"
        elif isinstance(node, ast.Tuple):
            elts = ", ".join(self._get_annotation_string(e) for e in node.elts)
            return elts
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Union type (X | Y)
            left = self._get_annotation_string(node.left)
            right = self._get_annotation_string(node.right)
            return f"{left} | {right}"
        else:
            return ast.unparse(node) if hasattr(ast, "unparse") else "..."

    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get the name of a decorator."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            value = self._get_decorator_name(node.value)
            return f"{value}.{node.attr}"
        else:
            return ast.unparse(node) if hasattr(ast, "unparse") else "decorator"

    def _get_parent(self, tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        """Find the parent node of a target node in the AST."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    return node
        return None

    def _get_module_path(self, file_path: str) -> str:
        """Convert file path to module path."""
        path = Path(file_path)
        # Remove .py extension
        module = path.stem
        # Try to build full module path
        parts = []
        current = path.parent
        while current.name and (current / "__init__.py").exists():
            parts.insert(0, current.name)
            current = current.parent
        parts.append(module)
        return ".".join(parts)

    def _calculate_type_hints_coverage(
        self, functions: List[FunctionSignature], classes: List[ClassSignature]
    ) -> float:
        """Calculate percentage of functions with type hints."""
        total = 0
        typed = 0

        for func in functions:
            total += 1
            if func.return_type or any(":" in p for p in func.parameters):
                typed += 1

        for cls in classes:
            for method in cls.methods:
                total += 1
                if method.return_type or any(":" in p for p in method.parameters):
                    typed += 1

        if total == 0:
            return 0.0
        return round((typed / total) * 100, 1)

    def _extract_dependencies(self, imports: List[str]) -> Set[str]:
        """Extract external dependencies from imports."""
        dependencies = set()
        stdlib_modules = {
            "abc",
            "ast",
            "asyncio",
            "collections",
            "contextlib",
            "copy",
            "dataclasses",
            "datetime",
            "enum",
            "functools",
            "hashlib",
            "io",
            "itertools",
            "json",
            "logging",
            "math",
            "os",
            "pathlib",
            "pickle",
            "random",
            "re",
            "shutil",
            "string",
            "sys",
            "tempfile",
            "threading",
            "time",
            "typing",
            "unittest",
            "uuid",
            "warnings",
        }

        for imp in imports:
            # Get root module
            root = imp.split(".")[0]
            if root not in stdlib_modules and not root.startswith("_"):
                dependencies.add(root)

        return dependencies

    def clear_cache(self) -> None:
        """Clear the file cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_files": len(self._cache),
        }
