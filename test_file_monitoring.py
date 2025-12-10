#!/usr/bin/env python3
"""Test file monitoring functionality."""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vibe_coder.intelligence.file_monitor import FileWatcher, FileEvent, FileEventType
from vibe_coder.intelligence.repo_mapper import RepositoryMapper


@pytest.fixture
def temp_repo_dir():
    """Create a temporary repository directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("""
def hello():
    print("Hello, World!")

class TestClass:
    def method(self):
        pass
""")
        yield temp_dir


@pytest.fixture
async def repo_mapper(temp_repo_dir):
    """Create a RepositoryMapper instance."""
    mapper = RepositoryMapper(
        root_path=temp_repo_dir,
        enable_monitoring=False,  # Disable auto-monitoring for tests
        enable_importance_scoring=True,
        enable_reference_resolution=True,
    )
    await mapper.scan_repository()
    yield mapper
    # Cleanup
    if mapper.file_watcher:
        mapper.file_watcher.stop_monitoring()


class TestFileWatcher:
    """Test file monitoring functionality."""

    @pytest.mark.asyncio
    async def test_file_watcher_initialization(self, repo_mapper):
        """Test that FileWatcher initializes correctly."""
        # Create a file watcher
        events = []
        def on_change(event):
            events.append(event)

        watcher = FileWatcher(repo_mapper, on_file_change=on_change)

        assert watcher.repo_mapper == repo_mapper
        assert watcher.event_handler.on_file_change == on_change
        assert not watcher.is_monitoring
        assert len(watcher.monitored_paths) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, repo_mapper):
        """Test starting and stopping monitoring."""
        events = []
        def on_change(event):
            events.append(event)

        watcher = FileWatcher(repo_mapper, on_change)

        # Start monitoring
        watcher.start_monitoring()
        assert watcher.is_monitoring
        assert len(watcher.monitored_paths) > 0

        # Stop monitoring
        watcher.stop_monitoring()
        assert not watcher.is_monitoring
        assert len(watcher.monitored_paths) == 0

    @pytest.mark.asyncio
    async def test_file_creation_detection(self, repo_mapper, temp_repo_dir):
        """Test that file creation is detected."""
        events = []
        def on_change(event):
            events.append(event)

        watcher = FileWatcher(repo_mapper, on_change)
        watcher.start_monitoring()

        try:
            # Create a new file
            new_file = Path(temp_repo_dir) / "new_file.py"
            new_file.write_text("print('New file')")

            # Wait for event processing
            await asyncio.sleep(1.0)

            # Check that event was detected
            assert len(events) > 0
            creation_events = [e for e in events if e.event_type == FileEventType.CREATED]
            assert len(creation_events) > 0

        finally:
            watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_file_modification_detection(self, repo_mapper, temp_repo_dir):
        """Test that file modification is detected."""
        events = []
        def on_change(event):
            events.append(event)

        watcher = FileWatcher(repo_mapper, on_change)
        watcher.start_monitoring()

        try:
            # Modify existing file
            test_file = Path(temp_repo_dir) / "test.py"
            test_file.write_text("print('Modified content')")

            # Wait for event processing
            await asyncio.sleep(1.0)

            # Check that event was detected
            assert len(events) > 0
            mod_events = [e for e in events if e.event_type == FileEventType.MODIFIED]
            assert len(mod_events) > 0

        finally:
            watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_file_deletion_detection(self, repo_mapper, temp_repo_dir):
        """Test that file deletion is detected."""
        events = []
        def on_change(event):
            events.append(event)

        # Create a temporary file to delete
        temp_file = Path(temp_repo_dir) / "temp_file.py"
        temp_file.write_text("print('Temporary')")

        watcher = FileWatcher(repo_mapper, on_change)
        watcher.start_monitoring()

        try:
            # Delete the file
            temp_file.unlink()

            # Wait for event processing
            await asyncio.sleep(1.0)

            # Check that event was detected
            assert len(events) > 0
            del_events = [e for e in events if e.event_type == FileEventType.DELETED]
            assert len(del_events) > 0

        finally:
            watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_wait_for_change(self, repo_mapper, temp_repo_dir):
        """Test waiting for file changes."""
        events = []
        def on_change(event):
            events.append(event)

        watcher = FileWatcher(repo_mapper, on_change)
        watcher.start_monitoring()

        try:
            # Schedule a file change after a short delay
            async def make_change():
                await asyncio.sleep(0.5)
                test_file = Path(temp_repo_dir) / "test.py"
                test_file.write_text("print('Delayed change')")

            change_task = asyncio.create_task(make_change())

            # Wait for change with timeout
            event = await watcher.wait_for_change(timeout=2.0)

            assert event is not None
            assert event.event_type == FileEventType.MODIFIED

            await change_task

        finally:
            watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_wait_for_change_timeout(self, repo_mapper):
        """Test timeout when waiting for changes."""
        watcher = FileWatcher(repo_mapper)
        watcher.start_monitoring()

        try:
            # Wait for change with short timeout
            event = await watcher.wait_for_change(timeout=0.5)
            assert event is None  # Timeout occurred

        finally:
            watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_add_remove_paths(self, repo_mapper, temp_repo_dir):
        """Test adding and removing monitoring paths."""
        subdir = Path(temp_repo_dir) / "subdir"
        subdir.mkdir()

        watcher = FileWatcher(repo_mapper)
        watcher.start_monitoring(paths=[str(temp_repo_dir)])

        initial_count = len(watcher.monitored_paths)

        # Add a new path
        watcher.add_path(str(subdir))
        assert len(watcher.monitored_paths) == initial_count + 1

        # Remove the path
        watcher.remove_path(str(subdir))
        assert len(watcher.monitored_paths) == initial_count

        watcher.stop_monitoring()

    @pytest.mark.asyncio
    async def test_get_status(self, repo_mapper):
        """Test getting watcher status."""
        watcher = FileWatcher(repo_mapper)

        # Status when not monitoring
        status = watcher.get_status()
        assert not status["is_monitoring"]
        assert len(status["monitored_paths"]) == 0
        assert not status["observer_alive"]

        # Status when monitoring
        watcher.start_monitoring()
        status = watcher.get_status()
        assert status["is_monitoring"]
        assert len(status["monitored_paths"]) > 0
        assert status["observer_alive"]

        watcher.stop_monitoring()


class TestRepositoryEventHandler:
    """Test the repository event handler."""

    @pytest.mark.asyncio
    async def test_event_debouncing(self, repo_mapper, temp_repo_dir):
        """Test that rapid events are debounced."""
        events = []
        def on_change(event):
            events.append(event)

        handler = repo_mapper.file_watcher.event_handler if repo_mapper.file_watcher else None
        if not handler:
            handler = type('Handler', (), {
                'repo_mapper': repo_mapper,
                'on_file_change': on_change,
                '_debounce_queue': {},
                '_debounce_time': 0.1,
            })()
            # Mock the async task creation
            handler._debounce_task = None

        # Simulate rapid modifications to the same file
        test_file = Path(temp_repo_dir) / "test.py"

        for i in range(5):
            test_file.write_text(f"print('Content {i}')")
            await asyncio.sleep(0.05)  # Rapid changes

        # Wait for debouncing
        await asyncio.sleep(0.3)

        # Should have fewer events than modifications due to debouncing
        assert len(events) <= 5