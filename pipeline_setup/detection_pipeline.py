from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json
import time

from prefect.deployments import Deployment
from prefect import task, flow, get_run_logger

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.indexing_functions import IndexingFunctions
from functions.chatbot_functions import ChatbotFunctions


class DBFileDetectionFlow:
    def __init__(
            self,
            interval: Optional[int] = 600,
        ):
        self.deployment_name = "File Detection Flow"
        self.interval = interval

    def create_deployment(self):
        deployment = Deployment.build_from_flow(
            flow=detection_flow,
            name=self.deployment_name,
            schedule={"interval": self.interval},
            work_queue_name="file_detection",
            work_pool_name="local-worker",
        )
        deployment.apply()

class FileProcessingFlow:
    def __init__(self):
        self.deployment_name = "File Processing Flow"

    def create_deployment(self):
        deployment = Deployment.build_from_flow(
            flow=processing_flow,
            name=self.deployment_name,
            work_queue_name="file_processing",
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
        self.db_folder_path = ""
        self.memory_json_path = ""
        self.config_json_path = Path(__file__).resolve().parent.parent / "utils" / "config.json"
        self.event_handler = FileChangeHandler()
        self.observer = Observer()

    def detect_changes(self):
        logger = get_run_logger()
        self.observer.schedule(
            self.event_handler,
            str(self.db_folder_path),
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
        changes = []
        # Load memory db information
        with open(self.memory_json_path, "r") as file:
            memory_data = json.load(file)
        
        # Load current db information
        current_file_data = []
        for file in self.db_folder_path.rglob("*"):
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

        # Check differences
        for _, data in enumerate(current_file_data):
            if data in memory_data:
                continue
            memory_data.append(data)
            changes.append(data)
        
        # Overwrite the changes if any
        if changes:
            with open(self.memory_json_path, "w") as file:
                memory_data = json.dump(memory_data, file, indent=4)

        return changes
    
    def check_db_path(self):
        try:
            with open(self.config_json_path, "r") as file:
                config_data = json.load(file)
        except FileNotFoundError:
            print(f"Configuration file can't be located in {self.config_json_path}")
            return

        if config_data[0]["db_path"]:
            self.db_folder_path = Path(config_data[0]["db_path"])
            self.memory_json_path = self.db_folder_path / "memory.json"
        else:
            if config_data[0]["environment"] == "Windows":
                db_path = f"C:/Users/{config_data[0]["user_name"]}/Documents/ragchat_local/db"
                config_data[0]["db_path"] = db_path
                self.db_folder_path = Path(db_path)
                self.memory_json_path = self.db_folder_path / "memory.json"
                with open(self.config_json_path, "w") as file:
                    config_data = json.dump(config_data, file, indent=4)
            elif config_data[0]["environment"] == "MacOS":
                # :TODO: Add configuration for macos
                raise EnvironmentError("MacOS is not yet configured for RAG Chat Local!")
            else:
                raise EnvironmentError("Only Windows and MacOS is configured for RAG Chat Local!")

class FileProcessor:
    def __init__(
            self,
            changed_file_paths: List[str],
    ):
        self.ef = EmbeddingFunctions()
        self.cf = ChatbotFunctions()
        self.rf = ReadingFunctions()
        self.indf = IndexingFunctions()
        self.changed_file_paths = changed_file_paths

@flow
def detection_flow():
    logger = get_run_logger()
    logger.info("Starting file change detection...")
    changes = check_changes_task()
    
    if changes:
            logger.info(f"Embedding of new files starting!")
    else:
        logger.info("No changes detected during this flow run.")

@flow
def processing_flow():
    #:TODO: insert file processing flow
    pass

@task(retries=3)
def check_changes_task() -> List[dict]:
    changes = []
    # Initialize logger and file detector
    logger = get_run_logger()
    file_detector = FileDetector(duration=30)

    # Check the absolute database folder path
    logger.info("Database folder path is under check...")
    file_detector.db_folder = file_detector.check_db_path()
    time.sleep(2)
    logger.info(f"Database folder path is valid")
    
    # Check memory changes
    logger.info(f"Checking memory changes...")
    changes = file_detector.check_changes()
    if changes:
        logger.info(f"Detected {len(changes)} changes from memory!")
        for i, change in enumerate(changes):
            logger.info(f"Detection {i + 1}: {change["file_path"]}")
    else:
        logger.info(f"Memory is sync.")
    return changes

@task(retries=3)
def embedding_task():
    #:TODO: insert embedding task
    pass

if __name__ == "__main__":
    detector = FileDetector()
    detector.check_db_path()
    detector.check_changes()
