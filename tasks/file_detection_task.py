import time
from datetime import timedelta
from typing import List
from pathlib import Path

from prefect import task
from prefect.tasks import task_input_hash

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FolderChangeHandler(FileSystemEventHandler):
    """
    Custom handler for file system events.
    Inherits from watchdog.events.FileSystemEventHandler.
    """
    def __init__(self):
        self.changes: List[str] = []

    def on_any_event(self, event):
        """
        Called when a file system event occurs.

        Args:
            event: The event object representing the file system event.
        """
        if event.is_directory:
            return
        elif event.event_type in ['created', 'modified', 'deleted']:
            self.changes.append(f"File {event.src_path} has been {event.event_type}")

class FileDetector:
    def __init__(self, database_folder_path: Path):
        self.database_folder_path = database_folder_path
        self.event_handler = FolderChangeHandler()
        self.observer = Observer()

    def start_detection(self, duration: int):
        self.observer.schedule(
            self.event_handler,
            str(self.database_folder_path),
            recursive=False
        )
        self.observer.start()

        try:
            time.sleep(duration)
        finally:
            self.observer.stop()
            self.observer.join()

    def get_changes(self) -> List[str]:
        return self.event_handler.changes

    @task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=10))
    def detect_changes(self, duration: int = 300) -> List[str]:
        self.start_detection(duration)
        return self.get_changes()

class FileDetectionTask:
    def __init__(self, database_folder_path: Path):
        self.file_detector = FileDetector(database_folder_path)

    def get_changes(self):
        return self.file_detector.get_changes
