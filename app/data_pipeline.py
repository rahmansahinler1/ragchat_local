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
        changes = {
            "insert": {},
            "delete": {},
            "update": {}
        }
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
        #:TODO update this loop. Bu loop change tipini detect etmeli ve changes dict'ini dogru bir sekilde update etmeli.
        #:TODO burdaki update tipine gore gerekli fonksiyonlar yazilip cagirilmali.
        for data in current_file_data:
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
    
    def insert_to_db(
        self,
        changes: List[Dict[str, str]],
        db_folder_path: Path,
        updated_memory: List[Dict[str, str]],
        ):
        # Read changed pdf files
        for change in changes:
            # Create embeddings
            pdf_data = self.rf.read_pdf(pdf_path=change["file_path"])
            pdf_embeddings = self.ef.create_vector_embeddings_from_sentences(sentences=pdf_data["sentences"])

            # Detect changed domain
            pattern = r'domain\d+'
            match = re.search(pattern, change["file_path"])
            if match:
                domain = match[0]
                if domain in self.change_dict.keys():
                    self.change_dict[domain]["pdf_path"].append(change["file_path"])
                    self.change_dict[domain]["sentences"].extend(pdf_data["sentences"])
                    self.change_dict[domain]["embeddings"].append(pdf_embeddings)
                    self.change_dict[domain]["embeddings"] = np.vstack((self.change_dict[domain]["embeddings"], pdf_embeddings))
                else:
                    self.change_dict[domain] = {
                        "pdf_path": [change["file_path"]],
                        "page_sentence_amounts": [pdf_data["page_sentence_amount"]],
                        "sentences": pdf_data["sentences"],
                        "embeddings": pdf_embeddings
                    }
        
        # Update corresponding index
        for key, value in self.change_dict.items():
            # Open corresponding index if already created, if not initialize one
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                index =  faiss.deserialize_index(index_object["index_bytes"])
                index_object["pdf_path"].extend(path for path in value["pdf_path"])
                index_object["pdf_sentence_amount"].extend(sentence_amount for sentence_amount in value["pdf_sentence_amount"])
                index_object["sentences"].extend(sentence for sentence in value["sentences"])
                index.add(value["embeddings"])
                index_bytes = faiss.serialize_index(index=index)
                index_object["index_bytes"] = index_bytes
                
                self.indf.save_index(
                    index_object=index_object,
                    save_path=index_path
                )
            except FileNotFoundError:
                index_bytes = self.indf.create_index_bytes(embeddings=value["embeddings"])
                index_object = {**value, "index_bytes": index_bytes}
                self.indf.save_index(index_object=index_object, save_path=index_path)         

        # Update memory
        memory_json_path = db_folder_path / "memory.json"
        self.update_memory(memory_json_path=memory_json_path, memory_data=updated_memory)
    
    def clean_processor(self):
        self.change_dict = {}
