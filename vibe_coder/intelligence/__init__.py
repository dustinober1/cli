"""
Intelligence module for repository analysis and code understanding.

This module provides AST-based code analysis, repository mapping,
and intelligent context extraction for AI operations.
"""

from vibe_coder.intelligence.ast_analyzer import PythonASTAnalyzer
from vibe_coder.intelligence.code_context import (
    CodeContextProvider,
    ContextRequest,
    ContextResult,
    OperationType,
)
from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.types import ClassSignature, FileNode, FunctionSignature, RepositoryMap

__all__ = [
    # Types
    "FunctionSignature",
    "ClassSignature",
    "FileNode",
    "RepositoryMap",
    # Analyzers
    "PythonASTAnalyzer",
    # Mappers
    "RepositoryMapper",
    # Context
    "CodeContextProvider",
    "ContextRequest",
    "ContextResult",
    "OperationType",
]
