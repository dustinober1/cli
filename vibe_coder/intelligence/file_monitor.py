"""
Real-time file system monitoring for repository intelligence.

This module provides file watching capabilities using the watchdog library
to detect changes and trigger incremental updates to the repository map.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from vibe_coder.intelligence.types import FileEvent, FileEventType

if TYPE_CHECKING:
    from vibe_coder.intelligence.repo_mapper import RepositoryMapper


class RepositoryEventHandler(FileSystemEventHandler):
    """Handles file system events for repository monitoring."""

    def __init__(
        self,
        repo_mapper: "RepositoryMapper",
        on_file_change: Optional[Callable[[FileEvent], None]] = None,
    ):
        super().__init__()
        self.repo_mapper = repo_mapper
        self.on_file_change = on_file_change
        self._debounce_queue: Dict[str, FileEvent] = {}
        self._debounce_time = 0.5  # seconds
        self._debounce_task: Optional[asyncio.Task] = None
        self._loop = None  # Store reference to event loop

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation."""
        if not event.is_directory:
            self._queue_event(
                FileEvent(
                    path=event.src_path,
                    event_type=FileEventType.CREATED,
                    timestamp=datetime.now(),
                )
            )

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        if not event.is_directory:
            self._queue_event(
                FileEvent(
                    path=event.src_path,
                    event_type=FileEventType.MODIFIED,
                    timestamp=datetime.now(),
                )
            )

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion."""
        if not event.is_directory:
            self._queue_event(
                FileEvent(
                    path=event.src_path,
                    event_type=FileEventType.DELETED,
                    timestamp=datetime.now(),
                )
            )

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move/rename."""
        if not event.is_directory:
            self._queue_event(
                FileEvent(
                    path=event.dest_path,
                    event_type=FileEventType.MOVED,
                    timestamp=datetime.now(),
                    old_path=event.src_path,
                )
            )

    def _queue_event(self, event: FileEvent) -> None:
        """Queue an event for debouncing."""
        self._debounce_queue[event.path] = event

        # Get or create the event loop
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, we'll use a timer instead
                import threading
                import time

                def process_delayed():
                    time.sleep(self._debounce_time)
                    # Process events in the main thread context
                    if self._debounce_queue:
                        events = list(self._debounce_queue.values())
                        self._debounce_queue.clear()
                        # Schedule processing in main thread
                        import concurrent.futures

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(self._process_events_sync, events)
                            # Don't wait for result to avoid blocking

                # Start timer thread
                timer_thread = threading.Thread(target=process_delayed, daemon=True)
                timer_thread.start()
                return

        # Cancel existing debounce task
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        # Schedule new debounce task
        self._debounce_task = asyncio.run_coroutine_threadsafe(
            self._process_debounced_events(), self._loop
        )

    def _process_events_sync(self, events: List[FileEvent]) -> None:
        """Process events synchronously (from non-async thread)."""
        for event in events:
            try:
                if event.event_type == FileEventType.DELETED:
                    # Handle deletion
                    rel_path = os.path.relpath(event.path, self.repo_mapper.root_path)
                    if (
                        self.repo_mapper._repo_map
                        and rel_path in self.repo_mapper._repo_map.modules
                    ):
                        del self.repo_mapper._repo_map.modules[rel_path]
                elif event.event_type == FileEventType.MOVED:
                    # Handle move
                    if event.old_path:
                        old_rel = os.path.relpath(event.old_path, self.repo_mapper.root_path)
                        new_rel = os.path.relpath(event.path, self.repo_mapper.root_path)
                        if (
                            self.repo_mapper._repo_map
                            and old_rel in self.repo_mapper._repo_map.modules
                        ):
                            node = self.repo_mapper._repo_map.modules[old_rel]
                            node.path = event.path
                            self.repo_mapper._repo_map.modules[new_rel] = node
                            del self.repo_mapper._repo_map.modules[old_rel]

                # Notify callback
                if self.on_file_change:
                    self.on_file_change(event)
            except Exception as e:
                print(f"Error processing event {event}: {e}")

    async def _process_debounced_events(self) -> None:
        """Process debounced events after delay."""
        await asyncio.sleep(self._debounce_time)

        if not self._debounce_queue:
            return

        # Get a snapshot of events
        events = list(self._debounce_queue.values())
        self._debounce_queue.clear()

        # Process each event
        for event in events:
            await self._handle_event(event)

    async def _handle_event(self, event: FileEvent) -> None:
        """Handle a single file event."""
        # Update repository map
        if event.event_type == FileEventType.DELETED:
            # Handle deletion
            rel_path = os.path.relpath(event.path, self.repo_mapper.root_path)
            if self.repo_mapper._repo_map and rel_path in self.repo_mapper._repo_map.modules:
                del self.repo_mapper._repo_map.modules[rel_path]
        elif event.event_type == FileEventType.MOVED:
            # Handle move
            if event.old_path:
                old_rel = os.path.relpath(event.old_path, self.repo_mapper.root_path)
                new_rel = os.path.relpath(event.path, self.repo_mapper.root_path)
                if self.repo_mapper._repo_map and old_rel in self.repo_mapper._repo_map.modules:
                    node = self.repo_mapper._repo_map.modules[old_rel]
                    node.path = event.path
                    self.repo_mapper._repo_map.modules[new_rel] = node
                    del self.repo_mapper._repo_map.modules[old_rel]
        else:
            # Handle creation/modification - trigger incremental update
            await self.repo_mapper.update_on_file_change(event.path)

        # Notify callback
        if self.on_file_change:
            self.on_file_change(event)


class FileWatcher:
    """Real-time file system monitoring for repositories."""

    def __init__(
        self,
        repo_mapper: "RepositoryMapper",
        on_file_change: Optional[Callable[[FileEvent], None]] = None,
    ):
        self.repo_mapper = repo_mapper
        self.observer = Observer()
        self.event_handler = RepositoryEventHandler(repo_mapper, on_file_change)
        self.is_monitoring = False
        self.monitored_paths: Set[str] = set()

    def start_monitoring(
        self,
        paths: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> None:
        """
        Start monitoring file changes.

        Args:
            paths: List of paths to monitor. If None, monitors the repository root.
            recursive: Whether to monitor subdirectories.
        """
        if self.is_monitoring:
            return

        # Create new observer if needed (threads can't be restarted)
        if hasattr(self.observer, "is_alive") and self.observer.is_alive():
            # Observer already running
            pass
        else:
            # Create new observer
            from watchdog.observers import Observer

            self.observer = Observer()
            self.monitored_paths.clear()

        if paths is None:
            paths = [str(self.repo_mapper.root_path)]

        # Schedule paths for monitoring
        for path in paths:
            abs_path = os.path.abspath(path)
            if abs_path not in self.monitored_paths:
                try:
                    self.observer.schedule(
                        self.event_handler,
                        abs_path,
                        recursive=recursive,
                    )
                    self.monitored_paths.add(abs_path)
                except Exception as e:
                    print(f"Warning: Could not schedule {abs_path}: {e}")

        # Start the observer
        self.observer.start()
        self.is_monitoring = True

    def stop_monitoring(self) -> None:
        """Stop monitoring file changes."""
        if not self.is_monitoring:
            return

        # Unschedule all watches
        try:
            # Note: After calling stop(), the observer cannot be restarted
            if hasattr(self.observer, "_watches"):
                # watchdog 0.9.x+ stores watches as a set
                for watch in list(self.observer._watches):
                    self.observer.unschedule(watch)
            elif hasattr(self.observer, "_handlers"):
                # Older versions might store differently
                for watch in list(self.observer._handlers):
                    self.observer.unschedule(watch)
        except Exception as e:
            # Ignore errors during cleanup
            print(f"Warning during unschedule: {e}")

        # Stop the observer
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

        self.is_monitoring = False
        self.monitored_paths.clear()

    def add_path(self, path: str, recursive: bool = True) -> None:
        """
        Add a path to monitor.

        Args:
            path: Path to monitor.
            recursive: Whether to monitor subdirectories.
        """
        if not self.is_monitoring:
            return

        abs_path = os.path.abspath(path)
        if abs_path not in self.monitored_paths:
            self.observer.schedule(
                self.event_handler,
                abs_path,
                recursive=recursive,
            )
            self.monitored_paths.add(abs_path)

    def remove_path(self, path: str) -> None:
        """
        Remove a path from monitoring.

        Args:
            path: Path to stop monitoring.
        """
        abs_path = os.path.abspath(path)
        if abs_path in self.monitored_paths:
            # watchdog doesn't support unscheduling individual watches
            # We need to restart monitoring with updated paths
            was_monitoring = self.is_monitoring
            if was_monitoring:
                self.stop_monitoring()

            self.monitored_paths.discard(abs_path)

            if was_monitoring and self.monitored_paths:
                # Restart with remaining paths
                for remaining_path in self.monitored_paths:
                    self.observer.schedule(
                        self.event_handler,
                        remaining_path,
                        recursive=True,
                    )
                self.observer.start()
                self.is_monitoring = True

    async def wait_for_change(self, timeout: Optional[float] = None) -> Optional[FileEvent]:
        """
        Wait for the next file change.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            The next file event or None if timeout reached.
        """
        change_event = asyncio.Event()
        last_event: Optional[FileEvent] = None

        def on_change(event: FileEvent) -> None:
            nonlocal last_event
            last_event = event
            change_event.set()

        # Temporarily set callback
        original_callback = self.event_handler.on_file_change
        self.event_handler.on_file_change = on_change

        try:
            # Wait for change
            try:
                await asyncio.wait_for(change_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                return None

            return last_event
        finally:
            # Restore original callback
            self.event_handler.on_file_change = original_callback

    def get_status(self) -> Dict:
        """Get monitoring status information."""
        return {
            "is_monitoring": self.is_monitoring,
            "monitored_paths": list(self.monitored_paths),
            "observer_alive": self.observer.is_alive() if self.is_monitoring else False,
        }
