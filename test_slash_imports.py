#!/usr/bin/env python3
"""Test importing slash commands."""

import asyncio
import sys

def test_imports():
    """Test that slash command modules can be imported."""
    print("Testing slash command imports...")

    try:
        # Test importing the base module
        from vibe_coder.commands.slash.base import SlashCommand, CommandContext
        print("✓ Successfully imported SlashCommand and CommandContext")

        # Test importing individual command modules
        from vibe_coder.commands.slash.commands import code
        from vibe_coder.commands.slash.commands import debug
        from vibe_coder.commands.slash.commands import git
        from vibe_coder.commands.slash.commands import model
        from vibe_coder.commands.slash.commands import provider
        from vibe_coder.commands.slash.commands import project
        from vibe_coder.commands.slash.commands import system
        from vibe_coder.commands.slash.commands import test
        print("✓ Successfully imported all command modules")

        # Test the registry
        from vibe_coder.commands.slash.registry import command_registry
        print(f"✓ Command registry has {len(command_registry.commands)} registered commands")

        # List available commands
        print("\nAvailable commands:")
        for name, cmd in command_registry.commands.items():
            print(f"  - /{name}: {cmd.description}")

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    print("\nAll imports successful!")
    return True


def test_slash_parser():
    """Test the slash command parser."""
    print("\n" + "="*50)
    print("Testing slash command parser...")

    try:
        from vibe_coder.commands.slash.parser import SlashParser
        print("✓ Successfully imported SlashParser")

        # Test parsing simple commands
        parser = SlashParser()

        # Test empty input
        result = parser.parse("")
        print(f"✓ Empty input: {result}")

        # Test parsing commands with arguments
        test_commands = [
            "/help",
            "/code create a function",
            "/test run all",
            "/git status",
            "/model gpt-4",
            "/project overview",
        ]

        print("\nParsing test commands:")
        for cmd in test_commands:
            result = parser.parse(cmd)
            print(f"  Input: {cmd}")
            print(f"  Parsed: {result}")

    except Exception as e:
        print(f"✗ Error testing parser: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\nParser test completed!")
    return True


if __name__ == "__main__":
    success = True
    success = test_imports() and success
    success = test_slash_parser() and success

    if success:
        print("\n✅ All slash command tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)