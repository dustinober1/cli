"""Tests for plugin base classes."""

import pytest

from vibe_coder.plugins.base import (
    AnalysisPlugin,
    BasePlugin,
    CommandPlugin,
    FormatterPlugin,
    HookPlugin,
    PluginMetadata,
    PluginPermission,
)


class TestPluginPermission:
    """Tests for PluginPermission enum."""

    def test_permission_values(self):
        """Test permission enum values."""
        assert PluginPermission.FILE_READ.value == "file_read"
        assert PluginPermission.FILE_WRITE.value == "file_write"
        assert PluginPermission.NETWORK.value == "network"
        assert PluginPermission.EXECUTE.value == "execute"
        assert PluginPermission.CONFIG.value == "config"
        assert PluginPermission.API_CALLS.value == "api_calls"


class TestPluginMetadata:
    """Tests for PluginMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
            entry_point="TestPlugin",
            dependencies=["requests"],
            permissions=[PluginPermission.NETWORK],
            tags=["test", "example"],
        )

        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert len(metadata.permissions) == 1
        assert len(metadata.tags) == 2

    def test_metadata_defaults(self):
        """Test metadata default values."""
        metadata = PluginMetadata(
            name="minimal",
            version="0.1.0",
            author="Author",
            description="Minimal",
        )

        assert metadata.entry_point == "Plugin"
        assert metadata.dependencies == []
        assert metadata.permissions == []
        assert metadata.license == "MIT"

    def test_metadata_to_dict(self):
        """Test serialization."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Desc",
            permissions=[PluginPermission.FILE_READ],
        )

        data = metadata.to_dict()
        assert data["name"] == "test"
        assert data["permissions"] == ["file_read"]

    def test_metadata_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "loaded",
            "version": "2.0.0",
            "author": "Loader",
            "description": "Loaded plugin",
            "permissions": ["network", "execute"],
            "tags": ["loaded"],
        }

        metadata = PluginMetadata.from_dict(data)
        assert metadata.name == "loaded"
        assert len(metadata.permissions) == 2
        assert PluginPermission.NETWORK in metadata.permissions


class TestBasePlugin:
    """Tests for BasePlugin class."""

    def test_plugin_validation(self):
        """Test plugin validation."""

        class TestPlugin(BasePlugin):
            async def execute(self):
                pass

        metadata = PluginMetadata(
            name="valid",
            version="1.0.0",
            author="Author",
            description="Valid",
        )

        plugin = TestPlugin(metadata)
        is_valid, errors = plugin.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_plugin_validation_missing_metadata(self):
        """Test validation with missing metadata."""

        class BadPlugin(BasePlugin):
            async def execute(self):
                pass

        plugin = BadPlugin()
        is_valid, errors = plugin.validate()

        assert is_valid is False
        assert len(errors) > 0

    def test_plugin_has_permission(self):
        """Test permission checking."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Test",
            permissions=[PluginPermission.FILE_READ, PluginPermission.NETWORK],
        )

        class TestPlugin(BasePlugin):
            async def execute(self):
                pass

        plugin = TestPlugin(metadata)

        assert plugin.has_permission(PluginPermission.FILE_READ) is True
        assert plugin.has_permission(PluginPermission.NETWORK) is True
        assert plugin.has_permission(PluginPermission.EXECUTE) is False

    def test_plugin_enable_disable(self):
        """Test enable/disable functionality."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Test",
        )

        class TestPlugin(BasePlugin):
            async def execute(self):
                pass

        plugin = TestPlugin(metadata)
        assert plugin.enabled is True

        plugin.on_disable()
        assert plugin.enabled is False

        plugin.on_enable()
        assert plugin.enabled is True

    def test_plugin_get_info(self):
        """Test getting plugin info."""
        metadata = PluginMetadata(
            name="info-test",
            version="1.2.3",
            author="Tester",
            description="Info test plugin",
            permissions=[PluginPermission.FILE_READ],
            tags=["info", "test"],
        )

        class TestPlugin(BasePlugin):
            async def execute(self):
                pass

        plugin = TestPlugin(metadata)
        info = plugin.get_info()

        assert info["name"] == "info-test"
        assert info["version"] == "1.2.3"
        assert info["enabled"] is True
        assert "file_read" in info["permissions"]


class TestCommandPlugin:
    """Tests for CommandPlugin class."""

    def test_register_command(self):
        """Test command registration."""
        metadata = PluginMetadata(
            name="cmd",
            version="1.0.0",
            author="Author",
            description="Command plugin",
        )

        class TestCommandPlugin(CommandPlugin):
            pass

        plugin = TestCommandPlugin(metadata)

        async def handler(*args):
            return "result"

        plugin.register_command("test", handler, "Test command")

        assert "test" in plugin.commands
        assert plugin.get_command("test") is handler

    def test_register_command_with_aliases(self):
        """Test command registration with aliases."""
        metadata = PluginMetadata(
            name="cmd",
            version="1.0.0",
            author="Author",
            description="Command plugin",
        )

        class TestCommandPlugin(CommandPlugin):
            pass

        plugin = TestCommandPlugin(metadata)

        async def handler(*args):
            return "result"

        plugin.register_command(
            "long-command",
            handler,
            aliases=["lc", "longcmd"],
        )

        assert plugin.get_command("long-command") is handler
        assert plugin.get_command("lc") is handler
        assert plugin.get_command("longcmd") is handler

    @pytest.mark.asyncio
    async def test_execute_command(self):
        """Test command execution."""
        metadata = PluginMetadata(
            name="cmd",
            version="1.0.0",
            author="Author",
            description="Command plugin",
        )

        class TestCommandPlugin(CommandPlugin):
            pass

        plugin = TestCommandPlugin(metadata)

        async def greet(name):
            return f"Hello, {name}!"

        plugin.register_command("greet", greet)

        result = await plugin.execute("greet", ["World"])
        assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self):
        """Test executing unknown command."""
        metadata = PluginMetadata(
            name="cmd",
            version="1.0.0",
            author="Author",
            description="Command plugin",
        )

        class TestCommandPlugin(CommandPlugin):
            pass

        plugin = TestCommandPlugin(metadata)

        with pytest.raises(ValueError, match="Unknown command"):
            await plugin.execute("nonexistent", [])


class TestAnalysisPlugin:
    """Tests for AnalysisPlugin class."""

    def test_supports_language(self):
        """Test language support checking."""
        metadata = PluginMetadata(
            name="analyzer",
            version="1.0.0",
            author="Author",
            description="Analyzer",
        )

        class TestAnalyzer(AnalysisPlugin):
            supported_languages = ["python", "javascript"]

            async def analyze(self, code, language, **options):
                return {"analyzed": True}

        plugin = TestAnalyzer(metadata)

        assert plugin.supports_language("python") is True
        assert plugin.supports_language("Python") is True
        assert plugin.supports_language("go") is False

    def test_supports_all_languages(self):
        """Test analyzer that supports all languages."""
        metadata = PluginMetadata(
            name="universal",
            version="1.0.0",
            author="Author",
            description="Universal",
        )

        class UniversalAnalyzer(AnalysisPlugin):
            # No supported_languages specified

            async def analyze(self, code, language, **options):
                return {}

        plugin = UniversalAnalyzer(metadata)

        assert plugin.supports_language("python") is True
        assert plugin.supports_language("rust") is True

    @pytest.mark.asyncio
    async def test_execute_analysis(self):
        """Test analysis execution."""
        metadata = PluginMetadata(
            name="analyzer",
            version="1.0.0",
            author="Author",
            description="Analyzer",
        )

        class TestAnalyzer(AnalysisPlugin):
            async def analyze(self, code, language, **options):
                return {
                    "language": language,
                    "lines": len(code.split("\n")),
                }

        plugin = TestAnalyzer(metadata)
        result = await plugin.execute("print('hello')", "python")

        assert result["language"] == "python"
        assert result["lines"] == 1


class TestFormatterPlugin:
    """Tests for FormatterPlugin class."""

    @pytest.mark.asyncio
    async def test_format_code(self):
        """Test code formatting."""
        metadata = PluginMetadata(
            name="formatter",
            version="1.0.0",
            author="Author",
            description="Formatter",
        )

        class TestFormatter(FormatterPlugin):
            async def format(self, code, language, config=None):
                return code.strip() + "\n"

        plugin = TestFormatter(metadata)
        result = await plugin.execute("  code  ", "python")

        assert result == "code\n"


class TestHookPlugin:
    """Tests for HookPlugin class."""

    def test_register_hook(self):
        """Test hook registration."""
        metadata = PluginMetadata(
            name="hooks",
            version="1.0.0",
            author="Author",
            description="Hooks",
        )

        class TestHookPlugin(HookPlugin):
            pass

        plugin = TestHookPlugin(metadata)

        async def handler(data):
            return data

        plugin.register_hook("pre_request", handler)

        assert "pre_request" in plugin.hooks
        assert "pre_request" in plugin.get_registered_hooks()

    @pytest.mark.asyncio
    async def test_trigger_hook(self):
        """Test hook triggering."""
        metadata = PluginMetadata(
            name="hooks",
            version="1.0.0",
            author="Author",
            description="Hooks",
        )

        class TestHookPlugin(HookPlugin):
            pass

        plugin = TestHookPlugin(metadata)

        async def transform(data):
            data["transformed"] = True
            return data

        plugin.register_hook("process", transform)

        result = await plugin.trigger("process", {"value": 1})
        assert result["transformed"] is True
        assert result["value"] == 1

    @pytest.mark.asyncio
    async def test_trigger_unregistered_hook(self):
        """Test triggering unregistered hook."""
        metadata = PluginMetadata(
            name="hooks",
            version="1.0.0",
            author="Author",
            description="Hooks",
        )

        class TestHookPlugin(HookPlugin):
            pass

        plugin = TestHookPlugin(metadata)

        # Should return data unchanged
        result = await plugin.trigger("unknown", {"value": 42})
        assert result["value"] == 42
