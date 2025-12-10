#!/usr/bin/env python3
"""Test chat command integration with repository intelligence."""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_coder.commands.chat import ChatCommand


async def test_chat_repository_integration():
    """Test that chat command integrates with repository intelligence."""
    print("Testing chat command repository integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple project
        main_file = Path(temp_dir) / "main.py"
        main_file.write_text("""#!/usr/bin/env python3
'''Main entry point.'''

from calculator import Calculator

def main():
    '''Main function.'''
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
""")

        calc_file = Path(temp_dir) / "calculator.py"
        calc_file.write_text("""'''Calculator module.'''

class Calculator:
    '''Simple calculator class.'''

    def __init__(self):
        self.history = []

    def add(self, a, b):
        '''Add two numbers.'''
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        '''Subtract two numbers.'''
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
""")

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create chat command
            chat = ChatCommand()

            # Test 1: Initialize repository intelligence
            print("\nTest 1: Initializing repository intelligence...")
            await chat._initialize_repository_intelligence()

            if chat.repo_mapper:
                print("✓ Repository mapper initialized")
                print(f"  Root: {chat.repo_mapper.root_path}")
                print(f"  Modules scanned: {len(chat.repo_mapper._repo_map.modules) if chat.repo_mapper._repo_map else 0}")
            else:
                print("✗ Repository mapper not initialized")

            # Test 2: Repository map stats
            print("\nTest 2: Repository statistics...")
            if chat.repo_mapper and chat.repo_mapper._repo_map:
                stats = chat.repo_mapper.get_stats()
                print(f"  Total files: {stats['total_files']}")
                print(f"  Total lines: {stats['total_lines']}")
                print(f"  Entry points: {stats['entry_points']}")

            # Test 3: Context extraction
            print("\nTest 3: Testing context extraction...")
            # This tests the integration between chat and context extraction
            working_dir = os.getcwd()
            print(f"  Working directory: {working_dir}")

            # Check if files are detected
            files = list(Path(working_dir).glob("*.py"))
            print(f"  Python files found: {len(files)}")
            for f in files:
                print(f"    - {f.name}")

            # Test 4: Welcome message includes repository info
            print("\nTest 4: Testing welcome message...")
            # Create a mock provider for testing
            from vibe_coder.types.config import AIProvider

            provider = AIProvider(
                name="test",
                api_key="test_key",
                endpoint="https://api.example.com",
                model="gpt-4"
            )

            # This would normally be called when chat starts
            welcome = chat._get_welcome_message()
            print(f"  Welcome message includes repository info: {'repository' in welcome.lower()}")

        finally:
            os.chdir(original_cwd)

    print("\nChat repository integration test completed!")


async def test_context_injection():
    """Test that context is injected into chat messages."""
    print("\n" + "="*50)
    print("Testing context injection...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        app_file = Path(temp_dir) / "app.py"
        app_file.write_text("""
from data_processor import DataProcessor

def main():
    processor = DataProcessor()
    data = processor.load_data()
    results = processor.process(data)
    return results
""")

        processor_file = Path(temp_dir) / "data_processor.py"
        processor_file.write_text("""
class DataProcessor:
    def __init__(self):
        self.data = []

    def load_data(self):
        return [1, 2, 3, 4, 5]

    def process(self, data):
        return [x * 2 for x in data]
""")

        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            chat = ChatCommand()
            await chat._initialize_repository_intelligence()

            # Test that repository context is available
            if chat.repo_mapper:
                print("✓ Repository mapper available in chat")

                # Check if repository is scanned
                if chat.repo_mapper._repo_map:
                    module_count = len(chat.repo_mapper._repo_map.modules)
                    print(f"  Repository scanned: {module_count} modules")
                else:
                    print("  Repository not yet scanned")

                # Test context compression
                if hasattr(chat.repo_mapper, 'compress_with_importance'):
                    compressed = await chat.repo_mapper.compress_with_importance(
                        max_tokens=1000,
                        target_file="app.py"
                    )
                    print(f"  Context compression works: {len(compressed) > 0}")

        finally:
            os.chdir(original_cwd)

    print("\nContext injection test completed!")


async def test_file_monitoring_in_chat():
    """Test file monitoring integration in chat."""
    print("\n" + "="*50)
    print("Testing file monitoring in chat...")

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('Hello')")

        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            chat = ChatCommand()
            await chat._initialize_repository_intelligence()

            # Check if monitoring is enabled by default
            if chat.repo_mapper:
                has_monitoring = chat.repo_mapper.enable_monitoring
                print(f"  Monitoring enabled: {has_monitoring}")

                # Test monitoring status
                if hasattr(chat.repo_mapper, 'file_watcher') and chat.repo_mapper.file_watcher:
                    status = chat.repo_mapper.file_watcher.get_status()
                    print(f"  Monitor status: {status}")

        finally:
            os.chdir(original_cwd)

    print("\nFile monitoring test completed!")


if __name__ == "__main__":
    asyncio.run(test_chat_repository_integration())
    asyncio.run(test_context_injection())
    asyncio.run(test_file_monitoring_in_chat())