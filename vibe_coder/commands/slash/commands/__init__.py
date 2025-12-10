"""
Individual slash command implementations.

This package contains all the individual slash commands organized by category.
"""

# Import all command modules to register them
from . import code  # noqa: F401
from . import debug  # noqa: F401
from . import git  # noqa: F401
from . import project  # noqa: F401
from . import repo  # noqa: F401
from . import system  # noqa: F401
from . import test  # noqa: F401

__all__ = []
