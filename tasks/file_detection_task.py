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
    This class is responsible for tracking file system changes and storing them in a list.

    Attributes:
        changes (List[str]): A list to store detected file changes.
    """
    def __init__(self):
        self.changes: List[str] = []

    def on_any_event(self, event):
        """
        Called when a file system event occurs.
        This method filters and stores relevant file system events.

        Args:
            event (FileSystemEvent): The event object representing the file system event.
        """
        if event.is_directory:
            return
        elif event.event_type in ['created', 'modified', 'deleted']:
            self.changes.append(f"File {event.src_path} has been {event.event_type}")

class FileDetector:
    """
    A class to manage file detection using Watchdog.

    This class sets up and executes file detection, monitoring a specified folder for changes.

    Attributes:
        database_folder_path (Path): The path to the folder to be monitored.
        event_handler (FolderChangeHandler): The handler for file system events.
        observer (Observer): The Watchdog observer for monitoring file system events.
    """

    def __init__(self,
                 database_folder_path: Path
        ):
        """
        Initialize the FileDetector.

        Args:
            database_folder_path (Path): The path to the folder to be monitored.
        """
        self.database_folder_path = database_folder_path
        self.event_handler = FolderChangeHandler()
        self.observer = Observer()

    def start_detection(self, duration: int):
        """
        Start the file detection process for a specified duration.
        This method sets up and starts the Watchdog observer, then waits for the specified duration.

        Args:
            duration (int): The duration to monitor for changes, in seconds.
        """
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

    def detect_changes(self, duration: int = 300) -> List[str]:
        """
        Prefect task to detect changes in the specified folder.
        This method starts the detection process and returns the detected changes.

        Args:
            duration (int): The duration to monitor for changes, in seconds. Default is 300 (5 minutes).

        Returns:
            List[str]: A list of detected file changes.
        """
        self.start_detection(duration)
        return self.event_handler.changes

class FileDetectionTask:
    """
    A wrapper class for FileDetector to be used as a Prefect task.

    This class provides an interface to create and use FileDetector as a Prefect task.

    Attributes:
        file_detector (FileDetector): The FileDetector instance used for file detection.
    """
    def __init__(self,
                 database_folder_path: Path
        ):
        """
        Initialize the FileDetectionTask.

        Args:
            database_folder_path (Path): The path to the folder to be monitored.
        """
        self.file_detector = FileDetector(database_folder_path)
    

    def get_changes(self, duration: int = 300) -> List[str]:
        """
        Retrieve the method to get changes from the FileDetector.

        Returns:
            Callable: The get_changes method of the FileDetector instance.
        """
        return detect_changes_task(self.file_detector, duration)

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=25))
def detect_changes_task(file_detector: FileDetector, duration: int = 300) -> List[str]:
    """
    Prefect task to detect changes in the specified folder.

    Args:
        file_detector (FileDetector): The FileDetector instance to use.
        duration (int): The duration to monitor for changes, in seconds. Default is 300 (5 minutes).

    Returns:
        List[str]: A list of detected file changes.
    """
    return file_detector.detect_changes(duration)
