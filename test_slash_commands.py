#!/usr/bin/env python3
"""Test new repository-related slash commands."""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_coder.commands.slash.commands.repo import (
    ScanCommand,
    ContextCommand,
    ReferencesCommand,
    ImportanceCommand,
    MonitorCommand,
)
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.commands.chat import ChatCommand


async def test_repo_commands():
    """Test repository-related slash commands."""
    print("Testing repository slash commands...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test repository
        Path(temp_dir / "main.py").write_text("""#!/usr/bin/env python3
'''Main entry point.'''

def main():
    '''Main function.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

        Path(temp_dir / "utils.py").write_text("""'''Utility functions.'''

def helper():
    '''Helper function.'''
    return "helper"
""")

        Path(temp_dir / "test_main.py").write_text("""'''Tests.'''

import unittest

class TestMain(unittest.TestCase):
    def test_main(self):
        pass
""")

        # Initialize chat command with repository
        chat_command = ChatCommand()
        await chat_command._initialize_repository_intelligence()

        # Override the working directory for testing
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create command context
            ctx = CommandContext(
                command="",
                args={},
                chat_command=chat_command,
                user_message=""
            )

            # Test 1: Scan command
            print("\nTest 1: /scan command...")
            scan_cmd = ScanCommand()
            result = await scan_cmd.execute(ctx)
            print(f"Scan result: {result}")

            # Test 2: Context command
            print("\nTest 2: /context command...")
            context_cmd = ContextCommand()
            result = await context_cmd.execute(ctx)
            print(f"Context result: {result}")

            # Test 3: Context for specific file
            print("\nTest 3: /context command for specific file...")
            result = await context_cmd.execute(ctx, file="main.py")
            print(f"Context for main.py result: {result}")

            # Test 4: References command
            print("\nTest 4: /references command...")
            refs_cmd = ReferencesCommand()
            result = await refs_cmd.execute(ctx, "main")
            print(f"References result: {result}")

            # Test 5: Importance command
            print("\nTest 5: /importance command...")
            importance_cmd = ImportanceCommand()
            result = await importance_cmd.execute(ctx, limit=5)
            print(f"Importance result: {result}")

            # Test 6: Monitor status
            print("\nTest 6: /monitor status command...")
            monitor_cmd = MonitorCommand()
            result = await monitor_cmd.execute(ctx, "status")
            print(f"Monitor status result: {result}")

        finally:
            os.chdir(original_cwd)

    print("\nRepository slash commands test completed!")


async def test_command_registration():
    """Test that all repository commands are properly registered."""
    print("\n" + "="*50)
    print("Testing command registration...")

    # Import and check registration
    from vibe_coder.commands.slash.commands.repo import register

    # Get registered commands
    commands = register()

    print(f"\nRegistered repository commands: {len(commands)}")
    for cmd in commands:
        print(f"  - /{cmd.name} - {cmd.help_text}")

    # Verify expected commands
    expected_commands = ["scan", "context", "references", "importance", "monitor"]
    registered_names = [cmd.name for cmd in commands]

    print("\nVerification:")
    all_registered = True
    for expected in expected_commands:
        if expected in registered_names:
            print(f"  ✓ /{expected} registered")
        else:
            print(f"  ✗ /{expected} NOT registered")
            all_registered = False

    if all_registered:
        print("\n✅ All repository commands successfully registered!")
    else:
        print("\n❌ Some commands are missing!")

    print("\nCommand registration test completed!")


async def test_command_help():
    """Test command help texts."""
    print("\n" + "="*50)
    print("Testing command help texts...")

    commands = [
        ScanCommand(),
        ContextCommand(),
        ReferencesCommand(),
        ImportanceCommand(),
        MonitorCommand(),
    ]

    print("\nCommand help texts:")
    for cmd in commands:
        print(f"\n/{cmd.name}")
        print(f"  Help: {cmd.help_text}")

        # Show example usage
        if cmd.name == "scan":
            print(f"  Example: /scan [path]")
        elif cmd.name == "context":
            print(f"  Example: /context [file]")
        elif cmd.name == "references":
            print(f"  Example: /references <symbol> [file]")
        elif cmd.name == "importance":
            print(f"  Example: /importance [limit]")
        elif cmd.name == "monitor":
            print(f"  Example: /monitor [on|off|status]")

    print("\nCommand help test completed!")


if __name__ == "__main__":
    asyncio.run(test_repo_commands())
    asyncio.run(test_command_registration())
    asyncio.run(test_command_help())