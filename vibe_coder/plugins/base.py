"""
Base plugin classes for the Vibe Coder plugin system.

This module defines abstract base classes for different plugin types
and the plugin metadata structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class PluginPermission(Enum):
    """Permissions that plugins can request."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK = "network"
    EXECUTE = "execute"
    CONFIG = "config"
    API_CALLS = "api_calls"


@dataclass
class PluginMetadata:
    """Plugin information and configuration."""

    name: str
    version: str
    author: str
    description: str
    entry_point: str = "Plugin"
    dependencies: List[str] = field(default_factory=list)
    permissions: List[PluginPermission] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    license: str = "MIT"
    min_vibe_version: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "permissions": [p.value for p in self.permissions],
            "tags": self.tags,
            "homepage": self.homepage,
            "license": self.license,
            "min_vibe_version": self.min_vibe_version,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PluginMetadata":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            author=data["author"],
            description=data["description"],
            entry_point=data.get("entry_point", "Plugin"),
            dependencies=data.get("dependencies", []),
            permissions=[PluginPermission(p) for p in data.get("permissions", [])],
            tags=data.get("tags", []),
            homepage=data.get("homepage"),
            license=data.get("license", "MIT"),
            min_vibe_version=data.get("min_vibe_version"),
        )


class BasePlugin(ABC):
    """Base class for all plugins."""

    metadata: PluginMetadata
    enabled: bool = True

    def __init__(self, metadata: Optional[PluginMetadata] = None):
        """Initialize the plugin."""
        if metadata:
            self.metadata = metadata

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality."""
        pass

    def on_load(self) -> None:
        """Called when plugin is loaded. Override for initialization."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded. Override for cleanup."""
        pass

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        self.enabled = True

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        self.enabled = False

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate plugin integrity.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not hasattr(self, "metadata"):
            errors.append("Plugin missing metadata")
        else:
            if not self.metadata.name:
                errors.append("Plugin missing name")
            if not self.metadata.version:
                errors.append("Plugin missing version")
            if not self.metadata.author:
                errors.append("Plugin missing author")

        return len(errors) == 0, errors

    def has_permission(self, permission: PluginPermission) -> bool:
        """Check if plugin has a specific permission."""
        return permission in self.metadata.permissions

    def get_info(self) -> Dict:
        """Get plugin information."""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "author": self.metadata.author,
            "description": self.metadata.description,
            "enabled": self.enabled,
            "permissions": [p.value for p in self.metadata.permissions],
            "tags": self.metadata.tags,
        }


class CommandPlugin(BasePlugin):
    """Plugin that adds slash commands."""

    commands: Dict[str, Callable] = {}
    aliases: Dict[str, str] = {}

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        aliases: Optional[List[str]] = None,
    ) -> None:
        """
        Register a new command.

        Args:
            name: Command name (without /)
            handler: Async function to handle command
            description: Command description
            aliases: Alternative command names
        """
        self.commands[name] = handler

        if aliases:
            for alias in aliases:
                self.aliases[alias] = name

    def get_command(self, name: str) -> Optional[Callable]:
        """Get command handler by name or alias."""
        if name in self.commands:
            return self.commands[name]
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None

    async def execute(self, command: str, args: List[str]) -> str:
        """Execute named command."""
        handler = self.get_command(command)
        if not handler:
            raise ValueError(f"Unknown command: {command}")
        return await handler(*args)

    def list_commands(self) -> List[Dict]:
        """List all registered commands."""
        return [
            {
                "name": name,
                "handler": handler.__name__,
                "doc": handler.__doc__ or "",
            }
            for name, handler in self.commands.items()
        ]


class AnalysisPlugin(BasePlugin):
    """Plugin that analyzes code."""

    supported_languages: List[str] = []

    def supports_language(self, language: str) -> bool:
        """Check if plugin supports a language."""
        if not self.supported_languages:
            return True  # Supports all if not specified
        return language.lower() in [lang.lower() for lang in self.supported_languages]

    @abstractmethod
    async def analyze(self, code: str, language: str, **options) -> Dict[str, Any]:
        """
        Analyze code and return findings.

        Args:
            code: Source code to analyze
            language: Programming language
            **options: Additional analysis options

        Returns:
            Dictionary with analysis results
        """
        pass

    async def execute(self, code: str, language: str, **options) -> Any:
        """Execute analysis."""
        return await self.analyze(code, language, **options)


class FormatterPlugin(BasePlugin):
    """Plugin that formats code."""

    supported_languages: List[str] = []

    def supports_language(self, language: str) -> bool:
        """Check if plugin supports a language."""
        if not self.supported_languages:
            return True
        return language.lower() in [lang.lower() for lang in self.supported_languages]

    @abstractmethod
    async def format(self, code: str, language: str, config: Optional[Dict] = None) -> str:
        """
        Format code according to rules.

        Args:
            code: Source code to format
            language: Programming language
            config: Optional formatter configuration

        Returns:
            Formatted code
        """
        pass

    async def execute(self, code: str, language: str, config: Optional[Dict] = None) -> str:
        """Execute formatting."""
        return await self.format(code, language, config)


class IntegrationPlugin(BasePlugin):
    """Plugin that integrates external services."""

    service_name: str = ""
    authenticated: bool = False

    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with external service.

        Args:
            credentials: Service credentials

        Returns:
            True if authentication succeeded
        """
        pass

    @abstractmethod
    async def call(self, action: str, params: Dict) -> Any:
        """
        Call external service.

        Args:
            action: Action to perform
            params: Action parameters

        Returns:
            Service response
        """
        pass

    async def execute(self, action: str, params: Dict) -> Any:
        """Execute service call."""
        if not self.authenticated:
            raise RuntimeError(f"Not authenticated with {self.service_name}")
        return await self.call(action, params)

    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return []


class HookPlugin(BasePlugin):
    """Plugin that hooks into Vibe Coder lifecycle events."""

    hooks: Dict[str, Callable] = {}

    def register_hook(self, event: str, handler: Callable) -> None:
        """
        Register a hook for an event.

        Args:
            event: Event name (e.g., "pre_request", "post_response")
            handler: Async function to handle event
        """
        self.hooks[event] = handler

    async def trigger(self, event: str, data: Any) -> Any:
        """
        Trigger a hook.

        Args:
            event: Event name
            data: Event data

        Returns:
            Modified data or result
        """
        if event in self.hooks:
            return await self.hooks[event](data)
        return data

    async def execute(self, event: str, data: Any) -> Any:
        """Execute hook."""
        return await self.trigger(event, data)

    def get_registered_hooks(self) -> List[str]:
        """Get list of registered hook events."""
        return list(self.hooks.keys())
