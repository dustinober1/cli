"""
Individual slash command implementations.

This package contains all the individual slash commands organized by category.
"""

# Import all command modules to register them
from .system import *
from .code import *
from .debug import *
from .test import *
from .git import *
from .project import *

__all__ = []