from datetime import timedelta
from typing import List, Optional
from pathlib import Path
import pandas as pd
import time
from datetime import datetime
import json

from prefect.deployments import Deployment
from prefect import task, flow, get_run_logger
from prefect.tasks import task_input_hash

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DBFileDetectionFlow:
    def __init__(
            self,
            interval: Optional[int] = 1800,
        ):
        self.deployment_name = "DB File Detection"
        self.interval = interval

    def create_deployment(self):
        deployment = Deployment.build_from_flow(
            flow=db_file_detection_flow,
            name="DB File Detection",
            schedule={"interval": self.interval},
            work_queue_name="db_file_detection",
            work_pool_name="local-worker",
        )
        deployment.apply()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.changes = []

    def on_any_event(self, event):
        if event.event_type in ['created', 'modified', 'deleted'] and not event.is_directory:
            self.changes.append(f"File {event.src_path} has been {event.event_type}")

class FileDetector:
    def __init__(
        self,
        duration: Optional[int] = 300
    ):
        self.duration = duration
        self.db_folder = Path(__file__).resolve().parent.parent / "db" / "domains"
        self.memory_json_path = Path(__file__).resolve().parent.parent / "utils" / "memory.json"
        self.event_handler = FileChangeHandler()
        self.observer = Observer()

    def detect_changes(self):
        logger = get_run_logger()
        self.observer.schedule(
            self.event_handler,
            str(self.db_folder),
            recursive=True,
        )
        self.observer.start()
        logger.info(f"Observer Started")

        try:
            time.sleep(self.duration)
        finally:
            self.observer.stop()
            
        self.observer.join()
        logger.info(f"Observer Stopped")

        return self.event_handler.changes
    
    def check_changes(self):
        with open(self.memory_json_path, "r") as file:
            memory_data = pd.DataFrame(json.load(file))
        
        current_file_data = []
        for file in self.db_folder.rglob("*"):
            file_data = {}
            file_name = file.parts[-1]
            domain = file.parts[-2]
            
            if file_name.split(".")[-1] != "pdf":
                continue
            
            date_modified = datetime.fromtimestamp(file.stat().st_mtime)
            date_modified_structured = f"{date_modified.month}/{date_modified.day}/{date_modified.year} {date_modified.hour}:{date_modified.minute}"
            file_data["file_path"] = f"db/domains/{domain}/{file_name}"
            file_data["date_modified"] = date_modified_structured
            current_file_data.append(file_data)
            
        current_file_data = pd.DataFrame(current_file_data)
        # :TODO: Add File change detection logic

@flow
def db_file_detection_flow():
    logger = get_run_logger()
    logger.info("Starting DB File Detection Flow")
    changes = detect_changes_task()
    
    if changes:
        logger.info(f"Detected {len(changes)} change(s):")
        for change in changes:
            logger.info(f"  {change}")
    else:
        logger.info("No changes detected during this flow run.")
    
    logger.info(f"Flow completed. Total changes detected: {len(changes)}")
    return changes

@task(retries=3)
def detect_changes_task() -> List[str]:
    logger = get_run_logger()

    file_detector = FileDetector(duration=10)
    logger.info(f"Starting detect_changes_task for folder {file_detector.db_folder} with duration {file_detector.duration}")
    changes = file_detector.detect_changes()
    
    logger.info(f"Detected {len(changes)} changes: {changes}")
    return changes

if __name__ == "__main__":
    detector = FileDetector()
    data = detector.check_changes()