from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
import numpy as np
import re
import json
import time
import faiss

from prefect.deployments import Deployment
from prefect import task, flow, get_run_logger

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.indexing_functions import IndexingFunctions
from functions.chatbot_functions import ChatbotFunctions


class FileDetectionFlow:
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

        return changes, memory_data
    
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
            change_dict: Dict = {},
    ):
        self.ef = EmbeddingFunctions()
        self.rf = ReadingFunctions()
        self.indf = IndexingFunctions()
        self.change_dict = change_dict
        self.main_folder_path = Path(__file__).resolve().parent.parent
    
    def clean_processor(self):
        self.change_dict = {}
    
    def update_memory(self, memory_data, memory_json_path:Path):
        with open(memory_json_path, "w") as file:
            memory_data = json.dump(memory_data, file, indent=4)

@flow
def detection_flow():
    logger = get_run_logger()
    logger.info("Starting file change detection flow...")
    changes, db_folder_path, updated_memory = check_changes_task()
    
    if changes:
        logger.info(f"File changes detected. Starting processing flow...")
        processing_flow(db_folder_path=db_folder_path, changed_files=changes, updated_memory=updated_memory)
    else:
        logger.info("No changes detected during this flow run.")

@flow
def processing_flow(
    db_folder_path: Path,
    updated_memory:List[Dict[str, str]],
    changed_files: List[Dict[str, str]] = []
    ):
    logger = get_run_logger()
    logger.info("Starting file processing flow...")
    update_db_task(changes=changed_files, db_folder_path=db_folder_path, updated_memory=updated_memory)
    logger.info("Processing flow finished successfully!")

@task(retries=3)
def check_changes_task() -> List[dict]:
    changes = []
    # Initialize logger and file detector
    logger = get_run_logger()
    detector = FileDetector(duration=30)

    # Check the absolute database folder path
    logger.info("Database folder path is under check...")
    detector.db_folder = detector.check_db_path()
    logger.info(f"Database folder path is valid")
    
    # Check memory changes
    logger.info(f"Checking memory changes...")
    changes, memory_data = detector.check_changes()
    if changes:
        logger.info(f"Detected {len(changes)} changes from memory!")
        for i, change in enumerate(changes):
            logger.info(f"Change {i + 1}: {change["file_path"]}")
    else:
        logger.info(f"Memory is sync.")
    return changes, detector.db_folder_path, memory_data

@task(retries=3)
def update_db_task(
    changes: List[Dict[str, str]],
    db_folder_path: Path,
    updated_memory: List[Dict[str, str]]
    ):
    processor = FileProcessor()
    logger = get_run_logger()
    logger.info("Embedding the new sentences...")
    # Read changed pdf files
    for change in changes:
        # Create embeddings
        sentences = processor.rf.read_pdf(pdf_path=change["file_path"])
        embeddings = processor.ef.create_vector_embeddings_from_sentences(sentences=sentences)

        # Detect changed domain
        pattern = r'domain\d+'
        match = re.search(pattern, change["file_path"])
        if match:
            domain = match[0]
            if domain in processor.change_dict.keys():
                processor.change_dict[domain]["sentences"].extend(sentences)
                processor.change_dict[domain]["embeddings"] = np.vstack((processor.change_dict[domain]["embeddings"], embeddings))
            else:
                processor.change_dict[domain] = {"sentences": sentences, "embeddings": embeddings}
    
    logger.info("Updating indexes...")
    # Update corresponding index
    for key, value in processor.change_dict.items():
        # Open corresponding index if already created, if not initialize one
        index_path = db_folder_path / "indexes" / (key + ".pickle")
        try:
            index_object = processor.indf.load_index(index_path)
            index =  faiss.deserialize_index(index_object["index"])
            sentences = index_object["sentences"]

            # Append necessary parts to the index
            index.add(value["embeddings"])
            sentences.extend(value["sentences"])

            # Overwrite the index
            index_bytes = faiss.serialize_index(index=index)
            processor.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)
        except FileNotFoundError:
            # Create the index
            index_bytes = processor.indf.create_index_bytes(embeddings=embeddings)
            processor.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)         

    # Update memory
    memory_json_path = db_folder_path / "memory.json"
    processor.update_memory(memory_json_path=memory_json_path, memory_data=updated_memory)
    logger.info("New files indexed. Memory updated.")