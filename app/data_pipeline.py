from typing import Dict, List
from pathlib import Path
from datetime import datetime
import numpy as np

import faiss
import json
import re

from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.indexing_functions import IndexingFunctions


class FileDetector:
    def __init__(
            self,
            db_folder_path: Path,
            memory_file_path: Path
        ):
        self.db_folder_path = db_folder_path
        self.memory_file_path = memory_file_path
    
    def check_changes(self):
        changes = []
        # Load memory db information
        with open(self.memory_file_path, "r") as file:
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

class FileProcessor:
    def __init__(
            self,
            change_dict: Dict = {},
    ):
        self.ef = EmbeddingFunctions()
        self.rf = ReadingFunctions()
        self.indf = IndexingFunctions()
        self.change_dict = change_dict
    
    def update_memory(self, memory_data, memory_json_path:Path):
        with open(memory_json_path, "w") as file:
            memory_data = json.dump(memory_data, file, indent=4)
    
    def sync_db(
        self,
        changes: List[Dict[str, str]],
        db_folder_path: Path,
        updated_memory: List[Dict[str, str]],
        ):
        # Read changed pdf files
        for change in changes:
            # Create embeddings
            sentences = self.rf.read_pdf(pdf_path=change["file_path"])
            embeddings = self.ef.create_vector_embeddings_from_sentences(sentences=sentences)

            # Detect changed domain
            pattern = r'domain\d+'
            match = re.search(pattern, change["file_path"])
            if match:
                domain = match[0]
                if domain in self.change_dict.keys():
                    self.change_dict[domain]["sentences"].extend(sentences)
                    self.change_dict[domain]["embeddings"] = np.vstack((self.change_dict[domain]["embeddings"], embeddings))
                else:
                    self.change_dict[domain] = {"sentences": sentences, "embeddings": embeddings}
        
        # Update corresponding index
        for key, value in self.change_dict.items():
            # Open corresponding index if already created, if not initialize one
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                index =  faiss.deserialize_index(index_object["index"])
                sentences = index_object["sentences"]

                # Append necessary parts to the index
                index.add(value["embeddings"])
                sentences.extend(value["sentences"])

                # Overwrite the index
                index_bytes = faiss.serialize_index(index=index)
                self.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)
            except FileNotFoundError:
                # Create the index
                index_bytes = self.indf.create_index_bytes(embeddings=embeddings)
                self.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)         

        # Update memory
        memory_json_path = db_folder_path / "memory.json"
        self.update_memory(memory_json_path=memory_json_path, memory_data=updated_memory)
    
    def clean_processor(self):
        self.change_dict = {}
