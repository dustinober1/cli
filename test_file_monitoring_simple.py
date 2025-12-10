#!/usr/bin/env python3
"""Simplified test for file monitoring functionality."""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_coder.intelligence.file_monitor import FileWatcher, FileEvent, FileEventType
from vibe_coder.intelligence.repo_mapper import RepositoryMapper


async def test_file_monitoring():
    """Test basic file monitoring functionality."""
    print("Starting file monitoring test...")

    # Create a temporary repository directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("""
def hello():
    print("Hello, World!")
""")

        # Create repository mapper
        repo_mapper = RepositoryMapper(
            root_path=temp_dir,
            enable_monitoring=False,  # We'll control it manually
            enable_importance_scoring=False,
            enable_reference_resolution=False,
        )
        await repo_mapper.scan_repository()
        print(f"Repository scanned with {len(repo_mapper._repo_map.modules)} modules")

        # Set up file monitoring
        events = []
        def on_change(event):
            events.append(event)
            print(f"Event detected: {event.event_type} on {event.path}")

        # Create file watcher
        watcher = FileWatcher(repo_mapper, on_file_change=on_change)

        # Test 1: Start/stop monitoring
        print("\nTest 1: Start/stop monitoring")
        watcher.start_monitoring()
        print(f"Monitoring started: {watcher.is_monitoring}")
        print(f"Monitored paths: {len(watcher.monitored_paths)}")

        watcher.stop_monitoring()
        print(f"Monitoring stopped: {watcher.is_monitoring}")

        # Test 2: File operations
        print("\nTest 2: File operations")
        watcher.start_monitoring()

        try:
            # Wait a bit for monitoring to stabilize
            await asyncio.sleep(1.0)

            # Clear any initial events
            events.clear()

            # Create a new file
            new_file = Path(temp_dir) / "new_file.py"
            new_file.write_text("print('New file')")
            print(f"Created new file: {new_file}")

            # Wait for event processing (increase time for slower systems)
            await asyncio.sleep(2.0)
            print(f"Events after creation: {len(events)}")

            # Modify existing file
            test_file.write_text("print('Modified content')")
            print(f"Modified test file")

            await asyncio.sleep(2.0)
            print(f"Events after modification: {len(events)}")

            # Delete the file
            new_file.unlink()
            print(f"Deleted new file")

            await asyncio.sleep(2.0)
            print(f"Events after deletion: {len(events)}")

            # Print event summary
            print("\nEvent Summary:")
            for event in events:
                print(f"  - {event.event_type.value}: {Path(event.path).name}")

        finally:
            watcher.stop_monitoring()
            # Give observer time to clean up
            await asyncio.sleep(0.5)

        # Test 3: Wait for change with timeout
        print("\nTest 3: Wait for change with timeout")
        watcher.start_monitoring()

        try:
            # Create a task to make a change
            async def make_change():
                await asyncio.sleep(0.5)
                test_file.write_text("print('Delayed change')")

            change_task = asyncio.create_task(make_change())

            # Wait for the change
            event = await watcher.wait_for_change(timeout=2.0)
            if event:
                print(f"Successfully detected change: {event.event_type.value}")
            else:
                print("Timeout waiting for change")

            await change_task

        finally:
            watcher.stop_monitoring()

        # Test 4: Timeout test
        print("\nTest 4: Timeout test")
        watcher.start_monitoring()

        try:
            event = await watcher.wait_for_change(timeout=0.5)
            if event is None:
                print("Timeout correctly occurred")
            else:
                print("Unexpected event received")
        finally:
            watcher.stop_monitoring()

    print("\nFile monitoring test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_file_monitoring())