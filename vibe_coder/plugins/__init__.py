"""
Plugin system for Vibe Coder extensibility.

This module provides a plugin architecture for adding custom commands,
analyzers, formatters, and integrations.
"""

from vibe_coder.plugins.base import (
    AnalysisPlugin,
    BasePlugin,
    CommandPlugin,
    FormatterPlugin,
    IntegrationPlugin,
    PluginMetadata,
    PluginPermission,
)
from vibe_coder.plugins.manager import PluginManager

__all__ = [
    # Base classes
    "BasePlugin",
    "CommandPlugin",
    "AnalysisPlugin",
    "FormatterPlugin",
    "IntegrationPlugin",
    # Metadata
    "PluginMetadata",
    "PluginPermission",
    # Manager
    "PluginManager",
]
