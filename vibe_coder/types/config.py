"""
Type definitions for Vibe Coder configuration.

This module defines the data structures for configuration using Python dataclasses.
These are similar to TypeScript interfaces but with runtime validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union


class InteractionMode(Enum):
    """Available interaction modes for the AI assistant."""

    CODE = "code"
    """Generate code based on prompts"""

    ARCHITECT = "architect"
    """High-level design and planning"""

    ASK = "ask"
    """Q&A mode without code generation"""

    AUDIT = "audit"
    """Code review and security analysis"""


class ProviderType(Enum):
    """Recognized AI provider types."""

    OPENAI = "openai"
    """OpenAI (GPT-4, GPT-3.5-turbo, etc.)"""

    ANTHROPIC = "anthropic"
    """Anthropic (Claude models)"""

    OLLAMA = "ollama"
    """Ollama local LLM server"""

    LM_STUDIO = "lm-studio"
    """LM Studio local LLM"""

    VLLM = "vllm"
    """vLLM local LLM server"""

    LOCAL_AI = "local-ai"
    """LocalAI local LLM"""

    GENERIC = "generic"
    """Generic OpenAI-compatible endpoint"""


@dataclass
class MCPServer:
    """
    Configuration for an MCP (Model Context Protocol) server.
    """

    name: str
    """Unique name for this MCP server"""

    command: str
    """Command to execute (for stdio transport) or URL (for sse transport)"""

    args: List[str] = field(default_factory=list)
    """Arguments for the command (for stdio transport)"""

    env: Optional[Dict[str, str]] = None
    """Environment variables for the process"""

    transport: str = "stdio"
    """Transport type: 'stdio' or 'sse'"""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "transport": self.transport,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPServer":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env"),
            transport=data.get("transport", "stdio"),
        )


@dataclass
class AIProvider:
    """
    Configuration for an AI provider.

    This dataclass stores all necessary information to connect to an AI API.
    It includes validation in __post_init__ to ensure values are valid.

    Attributes:
        name: Unique identifier for this provider configuration
        api_key: API key for authentication (can be "not-needed" for local models)
        endpoint: Base URL of the API endpoint
        model: Default model to use (optional, API may have defaults)
        temperature: Response randomness (0.0 = deterministic, 2.0 = very random)
        max_tokens: Maximum response length in tokens (optional)
        headers: Custom HTTP headers to send with requests (optional)

    Examples:
        >>> provider = AIProvider(
        ...     name="my-openai",
        ...     api_key="sk-...",
        ...     endpoint="https://api.openai.com/v1",
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
        >>> provider.temperature
        0.7
    """

    name: str
    """Unique name for this provider (e.g., 'my-openai', 'local-ollama')"""

    api_key: str
    """API key for authentication"""

    endpoint: str
    """Base URL for API endpoint (e.g., 'https://api.openai.com/v1')"""

    model: Optional[str] = None
    """Default model to use (optional)"""

    temperature: float = 0.7
    """Response temperature (0.0-2.0, default 0.7)"""

    max_tokens: Optional[int] = None
    """Maximum tokens in response (optional)"""

    headers: Optional[Dict[str, str]] = None
    """Custom HTTP headers (optional)"""

    def __post_init__(self) -> None:
        """Validate provider configuration after initialization."""
        # Validate temperature is in valid range
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")

        # Validate max_tokens if provided
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")

    def to_dict(self) -> Dict:
        """Convert provider to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AIProvider":
        """Create provider from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=data["name"],
            api_key=data["api_key"],
            endpoint=data["endpoint"],
            model=data.get("model"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens"),
            headers=data.get("headers"),
        )


@dataclass
class AppConfig:
    """
    Application configuration container.

    This is the root configuration object that contains all providers
    and global settings. It persists to ~/.vibe/config.json.

    Attributes:
        current_provider: Name of the currently active provider
        providers: Dictionary of all configured providers
        mcp_servers: Dictionary of configured MCP servers
        default_model: Global default model (overridable per provider)
        default_temperature: Global default temperature
        default_max_tokens: Global default max tokens
        offline_mode: If True, forbid all external network calls
        debug_mode: If True, enable verbose logging

    Examples:
        >>> config = AppConfig(current_provider="my-openai")
        >>> config.providers["my-openai"] = AIProvider(...)
        >>> current = config.get_provider()
        >>> current.name
        'my-openai'
    """

    current_provider: str
    """Name of the currently active provider"""

    providers: Dict[str, AIProvider] = field(default_factory=dict)
    """Dictionary of all configured providers"""

    mcp_servers: Dict[str, MCPServer] = field(default_factory=dict)
    """Dictionary of configured MCP servers"""

    default_model: Optional[str] = None
    """Global default model name (optional)"""

    default_temperature: float = 0.7
    """Global default temperature (0.0-2.0)"""

    default_max_tokens: Optional[int] = None
    """Global default max tokens (optional)"""

    offline_mode: bool = False
    """If True, forbid all external network calls"""

    debug_mode: bool = False
    """If True, enable verbose debugging output"""

    def get_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """
        Get a provider by name, or get the current provider.

        Args:
            name: Provider name to get, or None to get current provider

        Returns:
            AIProvider if found, None otherwise

        Examples:
            >>> config.get_provider()  # Get current provider
            >>> config.get_provider("my-openai")  # Get specific provider
        """
        provider_name = name or self.current_provider
        return self.providers.get(provider_name)

    def set_provider(self, name: str, provider: AIProvider) -> None:
        """
        Store a provider in the configuration.

        Args:
            name: Key to store provider under
            provider: AIProvider object to store

        Examples:
            >>> provider = AIProvider(...)
            >>> config.set_provider("my-openai", provider)
        """
        self.providers[name] = provider

    def list_providers(self) -> List[str]:
        """
        Get list of all configured provider names.

        Returns:
            List of provider names

        Examples:
            >>> config.list_providers()
            ['my-openai', 'my-anthropic', 'local-ollama']
        """
        return list(self.providers.keys())

    def delete_provider(self, name: str) -> None:
        """
        Delete a provider from configuration.

        Args:
            name: Name of provider to delete

        Examples:
            >>> config.delete_provider("my-openai")
        """
        if name in self.providers:
            del self.providers[name]

            # If deleted provider was current, clear current_provider
            if self.current_provider == name:
                self.current_provider = ""

    def has_provider(self, name: str) -> bool:
        """
        Check if a provider is configured.

        Args:
            name: Provider name to check

        Returns:
            True if provider exists

        Examples:
            >>> config.has_provider("my-openai")
            True
        """
        return name in self.providers

    def to_dict(self) -> Dict:
        """Convert config to dictionary for JSON serialization."""
        return {
            "current_provider": self.current_provider,
            "providers": {name: provider.to_dict() for name, provider in self.providers.items()},
            "mcp_servers": {name: server.to_dict() for name, server in self.mcp_servers.items()},
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "offline_mode": self.offline_mode,
            "debug_mode": self.debug_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AppConfig":
        """Create config from dictionary (e.g., loaded from JSON)."""
        config = cls(
            current_provider=data.get("current_provider", ""),
            default_model=data.get("default_model"),
            default_temperature=data.get("default_temperature", 0.7),
            default_max_tokens=data.get("default_max_tokens"),
            offline_mode=data.get("offline_mode", False),
            debug_mode=data.get("debug_mode", False),
        )

        # Reconstruct providers
        providers_data = data.get("providers", {})
        for name, provider_data in providers_data.items():
            config.set_provider(name, AIProvider.from_dict(provider_data))

        # Reconstruct MCP servers
        mcp_data = data.get("mcp_servers", {})
        for name, server_data in mcp_data.items():
            config.mcp_servers[name] = MCPServer.from_dict(server_data)

        return config

    @classmethod
    def default(cls) -> "AppConfig":
        """Create a default configuration."""
        return cls(current_provider="")
