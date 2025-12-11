"""
Tests for file system monitoring functionality.

This module tests the FileWatcher and RepositoryEventHandler classes
which provide real-time file system monitoring for repository intelligence.
"""

import asyncio
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from vibe_coder.intelligence.file_monitor import FileWatcher, RepositoryEventHandler
from vibe_coder.intelligence.types import FileEvent, FileEventType


class TestRepositoryEventHandler:
    """Test RepositoryEventHandler class."""

    def test_init(self, tmp_path):
        """Test handler initialization."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        callback = MagicMock()
        handler = RepositoryEventHandler(mock_mapper, callback)

        assert handler.repo_mapper == mock_mapper
        assert handler.on_file_change == callback
        assert handler._debounce_queue == {}
        assert handler._debounce_time == 0.5
        assert handler._debounce_task is None
        assert handler._loop is None

    def test_on_created_event(self, tmp_path):
        """Test handling file creation event."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock file system event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(tmp_path / "new_file.py")

        # Mock event loop
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            handler.on_created(mock_event)

            # Check event was queued
            assert str(tmp_path / "new_file.py") in handler._debounce_queue
            event = handler._debounce_queue[str(tmp_path / "new_file.py")]
            assert event.event_type == FileEventType.CREATED
            assert event.path == str(tmp_path / "new_file.py")
            assert isinstance(event.timestamp, datetime)

    def test_on_modified_event(self, tmp_path):
        """Test handling file modification event."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock file system event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(tmp_path / "modified_file.py")

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            handler.on_modified(mock_event)

            # Check event was queued
            assert str(tmp_path / "modified_file.py") in handler._debounce_queue
            event = handler._debounce_queue[str(tmp_path / "modified_file.py")]
            assert event.event_type == FileEventType.MODIFIED

    def test_on_deleted_event(self, tmp_path):
        """Test handling file deletion event."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock file system event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(tmp_path / "deleted_file.py")

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            handler.on_deleted(mock_event)

            # Check event was queued
            assert str(tmp_path / "deleted_file.py") in handler._debounce_queue
            event = handler._debounce_queue[str(tmp_path / "deleted_file.py")]
            assert event.event_type == FileEventType.DELETED

    def test_on_moved_event(self, tmp_path):
        """Test handling file move/rename event."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock file system event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(tmp_path / "old_name.py")
        mock_event.dest_path = str(tmp_path / "new_name.py")

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            handler.on_moved(mock_event)

            # Check event was queued
            assert str(tmp_path / "new_name.py") in handler._debounce_queue
            event = handler._debounce_queue[str(tmp_path / "new_name.py")]
            assert event.event_type == FileEventType.MOVED
            assert event.old_path == str(tmp_path / "old_name.py")

    def test_ignore_directory_events(self, tmp_path):
        """Test that directory events are ignored."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock directory event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(tmp_path / "new_directory")

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            handler.on_created(mock_event)

            # Check no event was queued
            assert len(handler._debounce_queue) == 0

    @pytest.mark.asyncio
    async def test_process_debounced_events(self, tmp_path):
        """Test processing of debounced events."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)
        mock_mapper.update_on_file_change = AsyncMock()

        handler = RepositoryEventHandler(mock_mapper)

        # Queue some events
        event1 = FileEvent(
            path=str(tmp_path / "file1.py"),
            event_type=FileEventType.CREATED,
            timestamp=datetime.now()
        )
        event2 = FileEvent(
            path=str(tmp_path / "file2.py"),
            event_type=FileEventType.MODIFIED,
            timestamp=datetime.now()
        )

        handler._debounce_queue = {
            str(tmp_path / "file1.py"): event1,
            str(tmp_path / "file2.py"): event2,
        }

        # Process events
        await handler._process_debounced_events()

        # Check queue was cleared
        assert len(handler._debounce_queue) == 0

        # Check update_on_file_change was called for created/modified
        assert mock_mapper.update_on_file_change.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_deleted_event(self, tmp_path):
        """Test handling deleted events."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        # Mock repository map with file
        mock_repo_map = MagicMock()
        mock_repo_map.modules = {"test_file.py": MagicMock()}
        mock_mapper._repo_map = mock_repo_map

        handler = RepositoryEventHandler(mock_mapper)

        event = FileEvent(
            path=str(tmp_path / "test_file.py"),
            event_type=FileEventType.DELETED,
            timestamp=datetime.now()
        )

        await handler._handle_event(event)

        # Check file was removed from repository map
        assert "test_file.py" not in mock_repo_map.modules

    @pytest.mark.asyncio
    async def test_handle_moved_event(self, tmp_path):
        """Test handling moved events."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        # Mock repository map with file
        old_node = MagicMock()
        old_node.path = str(tmp_path / "old_name.py")

        mock_repo_map = MagicMock()
        mock_repo_map.modules = {"old_name.py": old_node}
        mock_mapper._repo_map = mock_repo_map

        handler = RepositoryEventHandler(mock_mapper)

        event = FileEvent(
            path=str(tmp_path / "new_name.py"),
            event_type=FileEventType.MOVED,
            timestamp=datetime.now(),
            old_path=str(tmp_path / "old_name.py")
        )

        await handler._handle_event(event)

        # Check file was moved in repository map
        assert "old_name.py" not in mock_repo_map.modules
        assert "new_name.py" in mock_repo_map.modules
        assert mock_repo_map.modules["new_name.py"].path == str(tmp_path / "new_name.py")

    def test_debounce_multiple_events(self, tmp_path):
        """Test that multiple events for the same file are debounced."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        handler = RepositoryEventHandler(mock_mapper)

        # Mock file system event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(tmp_path / "rapid_file.py")

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            # Trigger multiple events quickly
            handler.on_modified(mock_event)
            handler.on_modified(mock_event)
            handler.on_created(mock_event)

            # Should only have one entry (the last one)
            assert len(handler._debounce_queue) == 1
            assert str(tmp_path / "rapid_file.py") in handler._debounce_queue
            # Last event should be CREATED
            assert handler._debounce_queue[str(tmp_path / "rapid_file.py")].event_type == FileEventType.CREATED


class TestFileWatcher:
    """Test FileWatcher class."""

    def test_init(self, tmp_path):
        """Test watcher initialization."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        callback = MagicMock()
        watcher = FileWatcher(mock_mapper, callback)

        assert watcher.repo_mapper == mock_mapper
        assert watcher.event_handler.repo_mapper == mock_mapper
        assert watcher.event_handler.on_file_change == callback
        assert watcher.is_monitoring is False
        assert len(watcher.monitored_paths) == 0

    def test_start_monitoring(self, tmp_path):
        """Test starting file monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)

        # Mock observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer = MagicMock()
            mock_observer_class.return_value = mock_observer
            mock_observer.is_alive.return_value = False

            watcher.start_monitoring()

            # Check observer was created and started
            mock_observer_class.assert_called_once()
            mock_observer.schedule.assert_called_once()
            mock_observer.start.assert_called_once()

            # Check status
            assert watcher.is_monitoring is True
            assert str(tmp_path.resolve()) in watcher.monitored_paths

    def test_start_monitoring_with_paths(self, tmp_path):
        """Test starting monitoring with specific paths."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)

        # Create subdirectories
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer = MagicMock()
            mock_observer_class.return_value = mock_observer
            mock_observer.is_alive.return_value = False

            watcher.start_monitoring(
                paths=[str(subdir1), str(subdir2)],
                recursive=False
            )

            # Check both paths were scheduled
            assert mock_observer.schedule.call_count == 2
            calls = mock_observer.schedule.call_args_list
            assert str(subdir1.resolve()) in [call[0][1] for call in calls]
            assert str(subdir2.resolve()) in [call[0][1] for call in calls]

            # Check recursive flag
            for call in calls:
                assert call[1]['recursive'] is False

    def test_start_monitoring_already_running(self, tmp_path):
        """Test starting monitoring when already running."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True

        # Mock observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer = MagicMock()
            mock_observer_class.return_value = mock_observer

            watcher.start_monitoring()

            # Should not start again
            mock_observer.start.assert_not_called()

    def test_stop_monitoring(self, tmp_path):
        """Test stopping file monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True
        watcher.monitored_paths.add(str(tmp_path))

        # Mock observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer = MagicMock()
            mock_observer.is_alive.return_value = True
            mock_observer._watches = [MagicMock()]
            watcher.observer = mock_observer

            watcher.stop_monitoring()

            # Check observer was stopped
            mock_observer.unschedule.assert_called_once()
            mock_observer.stop.assert_called_once()
            mock_observer.join.assert_called_once()

            # Check status
            assert watcher.is_monitoring is False
            assert len(watcher.monitored_paths) == 0

    def test_stop_monitoring_not_running(self, tmp_path):
        """Test stopping monitoring when not running."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = False

        # Mock observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer = MagicMock()
            watcher.observer = mock_observer

            watcher.stop_monitoring()

            # Should not stop
            mock_observer.stop.assert_not_called()

    def test_add_path(self, tmp_path):
        """Test adding a path to monitor."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True

        new_path = tmp_path / "new_subdir"
        new_path.mkdir()

        # Mock observer
        with patch.object(watcher.observer, 'schedule') as mock_schedule:
            watcher.add_path(str(new_path))

            mock_schedule.assert_called_once_with(
                watcher.event_handler,
                str(new_path.resolve()),
                recursive=True
            )

            assert str(new_path.resolve()) in watcher.monitored_paths

    def test_add_path_not_monitoring(self, tmp_path):
        """Test adding path when not monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = False

        # Mock observer
        with patch.object(watcher.observer, 'schedule') as mock_schedule:
            watcher.add_path(str(tmp_path))

            # Should not schedule
            mock_schedule.assert_not_called()

    def test_remove_path(self, tmp_path):
        """Test removing a path from monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True
        path_to_remove = str(tmp_path / "subdir")
        watcher.monitored_paths.add(path_to_remove)

        # Mock observer with multiple paths
        with patch.object(watcher.observer, 'schedule') as mock_schedule, \
             patch.object(watcher.observer, 'start') as mock_start, \
             patch.object(watcher.observer, 'is_alive', return_value=True):

            watcher.remove_path(path_to_remove)

            # Path should be removed
            assert path_to_remove not in watcher.monitored_paths
            # Should restart monitoring
            mock_start.assert_called_once()

    def test_remove_path_last_one(self, tmp_path):
        """Test removing the last monitored path."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True
        path_to_remove = str(tmp_path)
        watcher.monitored_paths.add(path_to_remove)

        # Mock observer
        with patch.object(watcher.observer, 'stop') as mock_stop, \
             patch.object(watcher.observer, 'is_alive', return_value=True):

            watcher.remove_path(path_to_remove)

            # Should stop monitoring since no paths left
            assert watcher.is_monitoring is False
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_change(self, tmp_path):
        """Test waiting for file changes."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        # Create a file watcher with mock observer
        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True

        # Mock file event
        test_event = FileEvent(
            path=str(tmp_path / "changed.py"),
            event_type=FileEventType.MODIFIED,
            timestamp=datetime.now()
        )

        # Mock wait_for_change
        with patch('asyncio.wait_for') as mock_wait_for:
            async def mock_wait(event, timeout=None):
                # Simulate immediate change
                event.set()

            mock_wait_for.side_effect = mock_wait

            # Call the method
            result = await watcher.wait_for_change(timeout=5.0)

            # Should have called wait_for_change
            mock_wait_for.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_change_timeout(self, tmp_path):
        """Test waiting for file changes with timeout."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True

        # Mock timeout
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            result = await watcher.wait_for_change(timeout=1.0)

            # Should return None on timeout
            assert result is None

    def test_get_status(self, tmp_path):
        """Test getting monitoring status."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = True
        watcher.monitored_paths.add(str(tmp_path))

        # Mock observer
        mock_observer = MagicMock()
        mock_observer.is_alive.return_value = True
        watcher.observer = mock_observer

        status = watcher.get_status()

        assert status["is_monitoring"] is True
        assert str(tmp_path) in status["monitored_paths"]
        assert status["observer_alive"] is True

    def test_get_status_not_monitoring(self, tmp_path):
        """Test getting status when not monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)
        watcher.is_monitoring = False

        status = watcher.get_status()

        assert status["is_monitoring"] is False
        assert len(status["monitored_paths"]) == 0
        assert status["observer_alive"] is False


class TestFileEvent:
    """Test FileEvent dataclass."""

    def test_file_event_creation(self):
        """Test creating a file event."""
        timestamp = datetime.now()
        event = FileEvent(
            path="/test/file.py",
            event_type=FileEventType.MODIFIED,
            timestamp=timestamp
        )

        assert event.path == "/test/file.py"
        assert event.event_type == FileEventType.MODIFIED
        assert event.timestamp == timestamp
        assert event.old_path is None

    def test_file_event_with_move(self):
        """Test creating a file event for move operation."""
        timestamp = datetime.now()
        event = FileEvent(
            path="/test/new_file.py",
            event_type=FileEventType.MOVED,
            timestamp=timestamp,
            old_path="/test/old_file.py"
        )

        assert event.path == "/test/new_file.py"
        assert event.event_type == FileEventType.MOVED
        assert event.timestamp == timestamp
        assert event.old_path == "/test/old_file.py"

    def test_file_event_serialization(self):
        """Test file event serialization."""
        timestamp = datetime.now()
        event = FileEvent(
            path="/test/file.py",
            event_type=FileEventType.CREATED,
            timestamp=timestamp,
            old_path="/test/old.py"
        )

        # Convert to dict
        event_dict = event.to_dict()

        assert event_dict["path"] == "/test/file.py"
        assert event_dict["event_type"] == "created"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["old_path"] == "/test/old.py"

    def test_file_event_deserialization(self):
        """Test file event deserialization."""
        timestamp = datetime.now()
        data = {
            "path": "/test/file.py",
            "event_type": "deleted",
            "timestamp": timestamp.isoformat(),
            "old_path": None
        }

        event = FileEvent.from_dict(data)

        assert event.path == "/test/file.py"
        assert event.event_type == FileEventType.DELETED
        assert event.timestamp == timestamp
        assert event.old_path is None


class TestIntegration:
    """Integration tests for file monitoring."""

    @pytest.mark.asyncio
    async def test_end_to_end_file_change(self, tmp_path):
        """Test end-to-end file change detection and processing."""
        # Create a mock repository mapper
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)
        mock_mapper.update_on_file_change = AsyncMock()

        # Create file watcher
        events_received = []

        def on_change(event):
            events_received.append(event)

        watcher = FileWatcher(mock_mapper, on_change)

        # Create handler directly to test event processing
        handler = watcher.event_handler

        # Simulate file change
        test_file = tmp_path / "test.py"
        test_file.write_text("initial content")

        # Create and handle event
        event = FileEvent(
            path=str(test_file),
            event_type=FileEventType.MODIFIED,
            timestamp=datetime.now()
        )

        await handler._handle_event(event)

        # Check file was updated in mapper
        mock_mapper.update_on_file_change.assert_called_once_with(str(test_file))

        # Check callback was called
        assert len(events_received) == 1
        assert events_received[0].path == str(test_file)

    def test_observer_recreation_on_restart(self, tmp_path):
        """Test that observer is recreated when restarting monitoring."""
        mock_mapper = MagicMock()
        mock_mapper.root_path = str(tmp_path)

        watcher = FileWatcher(mock_mapper)

        # First start - creates observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer1 = MagicMock()
            mock_observer1.is_alive.return_value = False
            mock_observer_class.return_value = mock_observer1

            watcher.start_monitoring()

            assert watcher.observer == mock_observer1

        # Stop monitoring
        watcher.stop_monitoring()

        # Second start - should create new observer
        with patch('vibe_coder.intelligence.file_monitor.Observer') as mock_observer_class:
            mock_observer2 = MagicMock()
            mock_observer2.is_alive.return_value = False
            mock_observer_class.return_value = mock_observer2

            watcher.start_monitoring()

            assert watcher.observer == mock_observer2
            assert watcher.observer != mock_observer1