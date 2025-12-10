"""
Type definitions for repository intelligence.

This module defines data structures for representing code metadata
extracted via AST analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any


@dataclass
class FunctionSignature:
    """Function metadata extracted via AST."""

    name: str
    module_path: str
    file_path: str
    line_start: int
    line_end: int
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    complexity: int = 1
    is_async: bool = False
    is_method: bool = False
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "module_path": self.module_path,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "complexity": self.complexity,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "decorators": self.decorators,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FunctionSignature":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            module_path=data["module_path"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            parameters=data.get("parameters", []),
            return_type=data.get("return_type"),
            docstring=data.get("docstring"),
            complexity=data.get("complexity", 1),
            is_async=data.get("is_async", False),
            is_method=data.get("is_method", False),
            decorators=data.get("decorators", []),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        async_prefix = "async " if self.is_async else ""
        params = ", ".join(self.parameters)
        ret = f" -> {self.return_type}" if self.return_type else ""
        return f"{async_prefix}{self.name}({params}){ret}"


@dataclass
class ClassSignature:
    """Class metadata extracted via AST."""

    name: str
    module_path: str
    file_path: str
    line_start: int
    line_end: int
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionSignature] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_dataclass: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "module_path": self.module_path,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "bases": self.bases,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": self.attributes,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "is_dataclass": self.is_dataclass,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ClassSignature":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            module_path=data["module_path"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            bases=data.get("bases", []),
            methods=[FunctionSignature.from_dict(m) for m in data.get("methods", [])],
            attributes=data.get("attributes", []),
            docstring=data.get("docstring"),
            decorators=data.get("decorators", []),
            is_dataclass=data.get("is_dataclass", False),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        bases_str = f"({', '.join(self.bases)})" if self.bases else ""
        return f"class {self.name}{bases_str}"


@dataclass
class FileNode:
    """File-level metadata."""

    path: str
    language: str
    lines_of_code: int = 0
    functions: List[FunctionSignature] = field(default_factory=list)
    classes: List[ClassSignature] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    type_hints_coverage: float = 0.0
    has_docstring: bool = False
    last_modified: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "imports": self.imports,
            "dependencies": list(self.dependencies),
            "type_hints_coverage": self.type_hints_coverage,
            "has_docstring": self.has_docstring,
            "last_modified": self.last_modified,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FileNode":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            language=data["language"],
            lines_of_code=data.get("lines_of_code", 0),
            functions=[FunctionSignature.from_dict(f) for f in data.get("functions", [])],
            classes=[ClassSignature.from_dict(c) for c in data.get("classes", [])],
            imports=data.get("imports", []),
            dependencies=set(data.get("dependencies", [])),
            type_hints_coverage=data.get("type_hints_coverage", 0.0),
            has_docstring=data.get("has_docstring", False),
            last_modified=data.get("last_modified"),
        )


@dataclass
class RepositoryMap:
    """Complete codebase structure."""

    root_path: str
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    modules: Dict[str, FileNode] = field(default_factory=dict)
    dependency_graph: Dict[str, Set[str]] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "root_path": self.root_path,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "languages": self.languages,
            "modules": {k: v.to_dict() for k, v in self.modules.items()},
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()},
            "entry_points": self.entry_points,
            "test_files": self.test_files,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RepositoryMap":
        """Create from dictionary."""
        return cls(
            root_path=data["root_path"],
            total_files=data.get("total_files", 0),
            total_lines=data.get("total_lines", 0),
            languages=data.get("languages", {}),
            modules={k: FileNode.from_dict(v) for k, v in data.get("modules", {}).items()},
            dependency_graph={k: set(v) for k, v in data.get("dependency_graph", {}).items()},
            entry_points=data.get("entry_points", []),
            test_files=data.get("test_files", []),
            generated_at=data.get("generated_at", datetime.now().isoformat()),
        )

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        lines = [
            f"Repository: {self.root_path}",
            f"Total Files: {self.total_files}",
            f"Total Lines: {self.total_lines}",
            "",
            "Languages:",
        ]
        for lang, count in sorted(self.languages.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {lang}: {count} files")

        if self.entry_points:
            lines.append("")
            lines.append("Entry Points:")
            for ep in self.entry_points[:5]:
                lines.append(f"  - {ep}")

        return "\n".join(lines)


@dataclass
class SymbolReference:
    """Represents a symbol reference in code."""

    name: str
    file_path: str
    line_number: int
    column: int
    reference_type: str  # "definition", "usage", "import"
    context: str
    symbol_type: Optional[str] = None  # "function", "class", "variable", "module"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "reference_type": self.reference_type,
            "context": self.context,
            "symbol_type": self.symbol_type,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SymbolReference":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            file_path=data["file_path"],
            line_number=data["line_number"],
            column=data["column"],
            reference_type=data["reference_type"],
            context=data["context"],
            symbol_type=data.get("symbol_type"),
        )


@dataclass
class Definition:
    """Represents a symbol definition location."""

    symbol: str
    file_path: str
    line_number: int
    column: int
    type: str  # "function", "class", "variable", "module"
    signature: Optional[str] = None
    docstring: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "type": self.type,
            "signature": self.signature,
            "docstring": self.docstring,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Definition":
        """Create from dictionary."""
        return cls(
            symbol=data["symbol"],
            file_path=data["file_path"],
            line_number=data["line_number"],
            column=data["column"],
            type=data["type"],
            signature=data.get("signature"),
            docstring=data.get("docstring"),
        )


class FileEventType(Enum):
    """File system event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """Represents a file system event."""

    path: str
    event_type: FileEventType
    timestamp: datetime
    old_path: Optional[str] = None  # For moved events

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "old_path": self.old_path,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FileEvent":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            event_type=FileEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            old_path=data.get("old_path"),
        )


@dataclass
class TokenBudget:
    """Token allocation for different context sections."""

    total: int
    available: int
    reserved_response: int
    allocations: Dict[str, int] = field(default_factory=dict)  # section -> token count

    def allocate(self, section: str, tokens: int) -> bool:
        """Allocate tokens to a section if available."""
        if tokens <= self.available:
            self.allocations[section] = tokens
            self.available -= tokens
            return True
        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "total": self.total,
            "available": self.available,
            "reserved_response": self.reserved_response,
            "allocations": self.allocations,
        }


@dataclass
class ContextItem:
    """An item that can be included in AI context."""

    path: str
    content: str
    importance: float
    token_count: int
    type: str  # "file", "function", "class", "import", "summary"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "content": self.content,
            "importance": self.importance,
            "token_count": self.token_count,
            "type": self.type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ContextItem":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            content=data["content"],
            importance=data["importance"],
            token_count=data["token_count"],
            type=data["type"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileImportance:
    """File importance metadata."""

    file_path: str
    score: float
    factors: Dict[str, float] = field(default_factory=dict)  # factor_name -> score
    last_calculated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "score": self.score,
            "factors": self.factors,
            "last_calculated": self.last_calculated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FileImportance":
        """Create from dictionary."""
        return cls(
            file_path=data["file_path"],
            score=data["score"],
            factors=data.get("factors", {}),
            last_calculated=datetime.fromisoformat(data.get("last_calculated", datetime.now().isoformat())),
        )
