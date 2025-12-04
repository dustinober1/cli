"""
Plugin manager for loading and managing plugins.

This module provides plugin discovery, loading, lifecycle management,
and security validation.
"""

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from vibe_coder.plugins.base import (
    AnalysisPlugin,
    BasePlugin,
    CommandPlugin,
    FormatterPlugin,
    IntegrationPlugin,
    PluginMetadata,
    PluginPermission,
)

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Exception raised for plugin errors."""

    pass


class PluginManager:
    """Manage plugin lifecycle."""

    def __init__(
        self,
        plugins_dir: Optional[str] = None,
        auto_discover: bool = True,
    ):
        """
        Initialize the plugin manager.

        Args:
            plugins_dir: Directory containing plugins
            auto_discover: Whether to auto-discover plugins on init
        """
        if plugins_dir:
            self.plugins_dir = Path(plugins_dir).expanduser()
        else:
            self.plugins_dir = Path.home() / ".vibe" / "plugins"

        self.plugins: Dict[str, BasePlugin] = {}
        self.metadata_cache: Dict[str, PluginMetadata] = {}
        self.enabled_plugins: set = set()
        self.disabled_plugins: set = set()

        # Ensure plugins directory exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        if auto_discover:
            self.discover_plugins()

    def discover_plugins(self) -> List[PluginMetadata]:
        """
        Find all available plugins.

        Returns:
            List of discovered plugin metadata
        """
        discovered = []

        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                metadata = self._load_plugin_metadata(item)
                if metadata:
                    self.metadata_cache[metadata.name] = metadata
                    discovered.append(metadata)

        return discovered

    def load_plugin(self, plugin_name: str) -> BasePlugin:
        """
        Load and initialize a plugin.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            Loaded plugin instance

        Raises:
            PluginError: If plugin cannot be loaded
        """
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]

        plugin_dir = self.plugins_dir / plugin_name
        if not plugin_dir.exists():
            raise PluginError(f"Plugin not found: {plugin_name}")

        # Load metadata
        metadata = self._load_plugin_metadata(plugin_dir)
        if not metadata:
            raise PluginError(f"Invalid plugin metadata: {plugin_name}")

        # Validate permissions
        if not self._validate_permissions(metadata):
            raise PluginError(f"Plugin {plugin_name} requires dangerous permissions")

        # Check dependencies
        missing_deps = self._check_dependencies(metadata)
        if missing_deps:
            raise PluginError(f"Plugin {plugin_name} missing dependencies: {missing_deps}")

        # Load module
        try:
            plugin_module = self._import_plugin_module(plugin_dir, metadata)
        except Exception as e:
            raise PluginError(f"Failed to import plugin {plugin_name}: {e}")

        # Get plugin class
        plugin_class = self._get_plugin_class(plugin_module, metadata)

        # Instantiate plugin
        try:
            plugin = plugin_class(metadata)
        except Exception as e:
            raise PluginError(f"Failed to instantiate plugin {plugin_name}: {e}")

        # Validate plugin
        is_valid, errors = plugin.validate()
        if not is_valid:
            raise PluginError(f"Plugin validation failed: {', '.join(errors)}")

        # Initialize plugin
        try:
            plugin.on_load()
        except Exception as e:
            raise PluginError(f"Plugin initialization failed: {e}")

        self.plugins[plugin_name] = plugin
        self.enabled_plugins.add(plugin_name)

        logger.info(f"Loaded plugin: {plugin_name} v{metadata.version}")
        return plugin

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if plugin was unloaded
        """
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]

        try:
            plugin.on_unload()
        except Exception as e:
            logger.warning(f"Error during plugin unload: {e}")

        del self.plugins[plugin_name]
        self.enabled_plugins.discard(plugin_name)
        self.disabled_plugins.discard(plugin_name)

        logger.info(f"Unloaded plugin: {plugin_name}")
        return True

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if plugin was enabled
        """
        if plugin_name not in self.plugins:
            # Try to load it first
            try:
                self.load_plugin(plugin_name)
            except PluginError:
                return False

        plugin = self.plugins[plugin_name]
        plugin.on_enable()
        self.enabled_plugins.add(plugin_name)
        self.disabled_plugins.discard(plugin_name)

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of the plugin to disable

        Returns:
            True if plugin was disabled
        """
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.on_disable()
        self.disabled_plugins.add(plugin_name)
        self.enabled_plugins.discard(plugin_name)

        return True

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a loaded plugin by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: Type[BasePlugin]) -> List[BasePlugin]:
        """
        Get all plugins of a specific type.

        Args:
            plugin_type: Plugin class type

        Returns:
            List of matching plugins
        """
        return [p for p in self.plugins.values() if isinstance(p, plugin_type) and p.enabled]

    def get_command_plugins(self) -> List[CommandPlugin]:
        """Get all command plugins."""
        return self.get_plugins_by_type(CommandPlugin)

    def get_analysis_plugins(self) -> List[AnalysisPlugin]:
        """Get all analysis plugins."""
        return self.get_plugins_by_type(AnalysisPlugin)

    def get_formatter_plugins(self) -> List[FormatterPlugin]:
        """Get all formatter plugins."""
        return self.get_plugins_by_type(FormatterPlugin)

    def get_integration_plugins(self) -> List[IntegrationPlugin]:
        """Get all integration plugins."""
        return self.get_plugins_by_type(IntegrationPlugin)

    async def execute_plugin(self, plugin_name: str, *args, **kwargs) -> Any:
        """
        Execute a plugin.

        Args:
            plugin_name: Name of the plugin
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Plugin execution result
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"Plugin not loaded: {plugin_name}")

        if not plugin.enabled:
            raise PluginError(f"Plugin disabled: {plugin_name}")

        return await plugin.execute(*args, **kwargs)

    def list_plugins(self, include_disabled: bool = False) -> List[Dict]:
        """
        List all plugins.

        Args:
            include_disabled: Include disabled plugins

        Returns:
            List of plugin info dictionaries
        """
        result = []

        # Include discovered but not loaded plugins
        for name, metadata in self.metadata_cache.items():
            if name in self.plugins:
                plugin = self.plugins[name]
                result.append(
                    {
                        **plugin.get_info(),
                        "loaded": True,
                        "enabled": plugin.enabled,
                    }
                )
            elif include_disabled:
                result.append(
                    {
                        "name": metadata.name,
                        "version": metadata.version,
                        "author": metadata.author,
                        "description": metadata.description,
                        "loaded": False,
                        "enabled": False,
                        "permissions": [p.value for p in metadata.permissions],
                        "tags": metadata.tags,
                    }
                )

        return result

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """
        Get detailed plugin information.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin info dictionary or None
        """
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_info()

        if plugin_name in self.metadata_cache:
            metadata = self.metadata_cache[plugin_name]
            return metadata.to_dict()

        return None

    def install_plugin(self, source: str) -> bool:
        """
        Install a plugin from source.

        Args:
            source: Path to plugin directory or archive

        Returns:
            True if installation succeeded
        """
        source_path = Path(source)

        if source_path.is_dir():
            # Copy directory
            import shutil

            metadata = self._load_plugin_metadata(source_path)
            if not metadata:
                raise PluginError("Invalid plugin: missing metadata")

            dest = self.plugins_dir / metadata.name
            if dest.exists():
                shutil.rmtree(dest)

            shutil.copytree(source_path, dest)
            self.metadata_cache[metadata.name] = metadata

            logger.info(f"Installed plugin: {metadata.name}")
            return True

        raise PluginError(f"Unsupported plugin source: {source}")

    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Uninstall a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if uninstallation succeeded
        """
        # Unload first
        self.unload_plugin(plugin_name)

        # Remove directory
        import shutil

        plugin_dir = self.plugins_dir / plugin_name
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)

        # Remove from cache
        self.metadata_cache.pop(plugin_name, None)

        logger.info(f"Uninstalled plugin: {plugin_name}")
        return True

    def _load_plugin_metadata(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """Load plugin.json metadata."""
        metadata_file = plugin_dir / "plugin.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
                return PluginMetadata.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse plugin metadata: {e}")
            return None

    def _import_plugin_module(self, plugin_dir: Path, metadata: PluginMetadata):
        """Import plugin module."""
        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            raise PluginError(f"Plugin missing __init__.py: {metadata.name}")

        spec = importlib.util.spec_from_file_location(
            f"vibe_plugins.{metadata.name}",
            init_file,
        )
        if not spec or not spec.loader:
            raise PluginError(f"Failed to create module spec: {metadata.name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        return module

    def _get_plugin_class(self, module, metadata: PluginMetadata) -> Type[BasePlugin]:
        """Get plugin class from module."""
        entry_point = metadata.entry_point or "Plugin"

        if not hasattr(module, entry_point):
            raise PluginError(f"Plugin missing entry point: {entry_point}")

        plugin_class = getattr(module, entry_point)

        if not issubclass(plugin_class, BasePlugin):
            raise PluginError("Plugin class must inherit from BasePlugin")

        return plugin_class

    def _validate_permissions(self, metadata: PluginMetadata) -> bool:
        """Validate plugin permissions are acceptable."""
        dangerous_permissions = {
            PluginPermission.EXECUTE,
            PluginPermission.NETWORK,
        }

        for perm in metadata.permissions:
            if perm in dangerous_permissions:
                logger.warning(
                    f"Plugin {metadata.name} requests dangerous permission: {perm.value}"
                )
                # Could prompt user for confirmation here
                # For now, allow all permissions

        return True

    def _check_dependencies(self, metadata: PluginMetadata) -> List[str]:
        """Check if plugin dependencies are met."""
        missing = []

        for dep in metadata.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)

        return missing

    def get_stats(self) -> Dict:
        """Get plugin manager statistics."""
        return {
            "total_discovered": len(self.metadata_cache),
            "total_loaded": len(self.plugins),
            "enabled": len(self.enabled_plugins),
            "disabled": len(self.disabled_plugins),
            "plugins_dir": str(self.plugins_dir),
        }
