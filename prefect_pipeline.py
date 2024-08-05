import os
from pathlib import Path
from prefect import task, flow
from prefect.tasks import task_input_hash
from datetime import timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

MAIN_FOLDER = Path(__file__).resolve().parent
WATCH_FOLDER = MAIN_FOLDER / "db" / "domain1"


class FolderChangeHandler(FileSystemEventHandler):
    """
    Custom handler for file system events.
    Inherits from watchdog.events.FileSystemEventHandler.
    """

    def on_any_event(self, event):
        """
        Called when a file system event occurs.

        Args:
            event: The event object representing the file system event.
        """
        if event.is_directory:
            return
        elif event.event_type in ['created', 'modified', 'deleted']:
            print(f"File {event.src_path} has been {event.event_type}")

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=10))
def detect_changes():
    """
    Prefect task to detect changes in the specified folder.
    Uses Watchdog to monitor file system events.
    """
    event_handler = FolderChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_FOLDER, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@flow
def folder_monitoring_flow():
    """
    Prefect flow that runs the detect_changes task.
    """
    detect_changes()

if __name__ == "__main__":
    folder_monitoring_flow()