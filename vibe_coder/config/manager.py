"""
Configuration manager for persisting and retrieving provider settings.

This module provides the ConfigManager class which handles all file I/O operations
for persisting configuration to ~/.vibe/config.json. It acts as the interface
between the application and the persistent configuration store.
"""

import json
from pathlib import Path
from typing import Optional

from vibe_coder.types.config import AIProvider, AppConfig, MCPServer


class ConfigManager:
    """
    Manages application configuration persistence to disk.

    This class handles:
    - Loading configuration from ~/.vibe/config.json
    - Saving configuration changes back to disk
    - Provider CRUD operations with automatic persistence
    - Automatic directory creation

    Attributes:
        config_dir: Path to configuration directory (defaults to ~/.vibe)
        config_file: Path to config.json file

    Examples:
        >>> manager = ConfigManager()
        >>> provider = AIProvider(name="my-openai", api_key="sk-...", endpoint="https://...")
        >>> manager.set_provider("my-openai", provider)
        >>> retrieved = manager.get_provider("my-openai")
        >>> manager.save_config()
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize ConfigManager and load existing configuration.

        Args:
            config_dir: Optional path to config directory. Defaults to ~/.vibe

        Side effects:
            - Creates config directory if it doesn't exist
            - Creates default config.json if it doesn't exist
            - Loads existing configuration from disk
        """
        self.config_dir = config_dir or Path.home() / ".vibe"
        self.config_file = self.config_dir / "config.json"

        # Create directory if needed
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load config from disk, or create default
        if self.config_file.exists():
            self._config = self._load_config()
        else:
            self._config = AppConfig.default()
            self._save_config()

    def get_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """
        Get a provider by name, or get the current provider.

        Args:
            name: Provider name to retrieve. If None, returns current provider.

        Returns:
            AIProvider if found, None otherwise

        Examples:
            >>> manager.get_provider("my-openai")  # Get specific provider
            >>> manager.get_provider()  # Get current provider
        """
        return self._config.get_provider(name)

    def set_provider(self, name: str, provider: AIProvider) -> None:
        """
        Store a provider in configuration and save to disk.

        Args:
            name: Key to store provider under
            provider: AIProvider object to store

        Examples:
            >>> provider = AIProvider(name="my-openai", ...)
            >>> manager.set_provider("my-openai", provider)
        """
        self._config.set_provider(name, provider)
        self._save_config()

    def set_current_provider(self, name: str) -> None:
        """
        Set the current active provider.

        Args:
            name: Name of provider to make current

        Raises:
            ValueError: If provider doesn't exist

        Examples:
            >>> manager.set_current_provider("my-openai")
        """
        if not self._config.has_provider(name):
            raise ValueError(f"Provider '{name}' not found")
        self._config.current_provider = name
        self._save_config()

    def get_current_provider(self) -> Optional[AIProvider]:
        """
        Get the currently active provider.

        Returns:
            Current AIProvider if set, None otherwise

        Examples:
            >>> current = manager.get_current_provider()
        """
        return self._config.get_provider()

    def list_providers(self) -> list[str]:
        """
        Get list of all configured provider names.

        Returns:
            List of provider names

        Examples:
            >>> providers = manager.list_providers()
            >>> # ['my-openai', 'my-anthropic', 'local-ollama']
        """
        return self._config.list_providers()

    def delete_provider(self, name: str) -> None:
        """
        Delete a provider from configuration.

        Args:
            name: Name of provider to delete

        Side effects:
            - Removes provider from config
            - Clears current_provider if it was the deleted provider
            - Persists changes to disk

        Examples:
            >>> manager.delete_provider("old-provider")
        """
        self._config.delete_provider(name)
        self._save_config()

    def has_provider(self, name: str) -> bool:
        """
        Check if a provider is configured.

        Args:
            name: Provider name to check

        Returns:
            True if provider exists, False otherwise

        Examples:
            >>> if manager.has_provider("my-openai"):
            ...     print("Provider exists")
        """
        return self._config.has_provider(name)

    def get_mcp_server(self, name: str) -> Optional[MCPServer]:
        """
        Get an MCP server by name.

        Args:
            name: MCP server name

        Returns:
            MCPServer if found, None otherwise
        """
        return self._config.mcp_servers.get(name)

    def list_mcp_servers(self) -> list[str]:
        """
        Get list of all configured MCP server names.

        Returns:
            List of MCP server names
        """
        return list(self._config.mcp_servers.keys())

    def set_mcp_server(self, name: str, server: MCPServer) -> None:
        """
        Store an MCP server in configuration and save to disk.

        Args:
            name: Key to store server under
            server: MCPServer object to store
        """
        self._config.mcp_servers[name] = server
        self._save_config()

    def delete_mcp_server(self, name: str) -> None:
        """
        Delete an MCP server from configuration.

        Args:
            name: Name of server to delete
        """
        if name in self._config.mcp_servers:
            del self._config.mcp_servers[name]
            self._save_config()

    def reset_config(self) -> None:
        """
        Reset configuration to defaults.

        Side effects:
            - Clears all providers
            - Resets to default settings
            - Persists changes to disk

        Examples:
            >>> manager.reset_config()
        """
        self._config = AppConfig.default()
        self._save_config()

    def get_config(self) -> AppConfig:
        """
        Get the current AppConfig object.

        Returns:
            Current AppConfig instance

        Examples:
            >>> config = manager.get_config()
            >>> config.debug_mode = True
            >>> manager.save_config()
        """
        return self._config

    def set_config(self, config: AppConfig) -> None:
        """
        Replace the entire configuration.

        Args:
            config: New AppConfig object to use

        Side effects:
            - Replaces current configuration
            - Persists changes to disk

        Examples:
            >>> new_config = AppConfig(current_provider="test")
            >>> manager.set_config(new_config)
        """
        self._config = config
        self._save_config()

    def save_config(self) -> None:
        """
        Explicitly save configuration to disk.

        Normally not needed as set_provider and other methods auto-save.
        Use this if you modify the config object directly.

        Examples:
            >>> config = manager.get_config()
            >>> config.debug_mode = True
            >>> manager.save_config()
        """
        self._save_config()

    def _load_config(self) -> AppConfig:
        """
        Load configuration from config.json file.

        Returns:
            AppConfig instance loaded from disk

        Raises:
            json.JSONDecodeError: If config.json is malformed
            ValueError: If config.json is missing required fields

        Raises:
            FileNotFoundError: If config file doesn't exist (shouldn't happen if
                              __init__ was called, but possible if deleted externally)
        """
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except FileNotFoundError:
            # File was deleted externally, return default
            return AppConfig.default()
        except json.JSONDecodeError as e:
            # Config file is corrupted, return default with warning
            print(f"Warning: Config file corrupted ({e}), using defaults")
            return AppConfig.default()

    def _save_config(self) -> None:
        """
        Save configuration to config.json file.

        The file is written with 2-space indentation for readability.
        Creates the config directory if needed.

        Raises:
            IOError: If unable to write to config file
            OSError: If unable to create config directory
        """
        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert config to dict and write
        config_dict = self._config.to_dict()
        with open(self.config_file, "w") as f:
            json.dump(config_dict, f, indent=2)


# Singleton instance for module-level access
config_manager = ConfigManager()
