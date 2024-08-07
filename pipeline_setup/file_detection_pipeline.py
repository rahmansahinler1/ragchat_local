from pathlib import Path
from datetime import timedelta
import time
from typing import List

from prefect.deployments import Deployment
from prefect import task, flow, get_run_logger
from prefect.tasks import task_input_hash

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DBFileDetectionFlow:
    def __init__(
            self,
            interval = 1800,
            duration = 60,
        ):

        self.deployment_name = "DB File Detection"
        self.interval = interval
        self.duration = duration

    def create_deployment(self):
        deployment = Deployment.build_from_flow(
            flow=db_file_detection_flow,
            name="DB File Detection",
            schedule={"interval": self.interval},
            work_queue_name="db_file_detection"
        )
        deployment.apply()

class FolderChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.changes = []

    def on_any_event(self, event):
        if event.event_type in ['created', 'modified', 'deleted'] and not event.is_directory:
            self.changes.append(f"File {event.src_path} has been {event.event_type}")

class FileDetector:
    def __init__(self):
        self.db_folder = "C:/Users/Rahman/Documents/ragchat_local/db/domains"
        self.event_handler = FolderChangeHandler()
        self.observer = Observer()

    def start_detection(self, duration: int):
        logger = get_run_logger()

        self.observer.schedule(
            self.event_handler,
            str(self.db_folder),
            recursive=True,
        )

        self.observer.start()
        logger.info(f"Observer Started")

        try:
            time.sleep(duration)
        finally:
            self.observer.stop()
        self.observer.join()
        logger.info(f"Observer Stopped")

    def detect_changes(self, duration: int = 60) -> List[str]:
        self.start_detection(duration)
        return self.event_handler.changes

@flow
def db_file_detection_flow():
    logger = get_run_logger()
    logger.info("Starting DB File Detection Flow")
    changes = detect_changes_task(duration=60)
    
    if changes:
        logger.info(f"Detected {len(changes)} change(s):")
        for change in changes:
            logger.info(f"  {change}")
    else:
        logger.info("No changes detected during this flow run.")
    
    logger.info(f"Flow completed. Total changes detected: {len(changes)}")
    return changes

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=29))
def detect_changes_task(duration: int = 60) -> List[str]:
    logger = get_run_logger()

    file_detector = FileDetector()
    logger.info(f"Starting detect_changes_task for folder {file_detector.db_folder} with duration {duration}")
    changes = file_detector.detect_changes(duration=duration)
    
    logger.info(f"Detected {len(changes)} changes: {changes}")
    return changes
