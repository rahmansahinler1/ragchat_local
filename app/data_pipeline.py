from typing import Dict, List
from pathlib import Path
from datetime import datetime
import numpy as np

import faiss
import json
import re
import textwrap

from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.indexing_functions import IndexingFunctions
from functions.chatbot_functions import ChatbotFunctions
import globals


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
            "insert": [],
            "delete": [],
            "update": []
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

        # Check for insertion and updates
        memory_file_paths = [item["file_path"] for item in memory_data]
        for data in current_file_data:
            if data in memory_data:
                continue
            elif data["file_path"] in memory_file_paths:
                changes["update"].append({"file_path": data["file_path"], "date_modified": data["date_modified"]})
                memory_index = memory_file_paths.index(data["file_path"])
                memory_data[memory_index]["date_modified"] = data["date_modified"]
            else:
                changes["insert"].append({"file_path": data["file_path"], "date_modified": data["date_modified"]})
                memory_data.append(data)
        
        # Check for deletion
        for i, data in enumerate(memory_data):
            if data not in current_file_data:
                changes["delete"].append({"file_path": data["file_path"], "date_modified": data["date_modified"]})
                memory_data.pop(i)

        return changes, memory_data

class FileProcessor:
    def __init__(
            self,
            change_dict: Dict = {},
    ):
        self.ef = EmbeddingFunctions()
        self.rf = ReadingFunctions()
        self.indf = IndexingFunctions()
        self.cf = ChatbotFunctions()
        self.change_dict = change_dict
    
    def update_memory(
            self,
            updated_memory: List[Dict[str, str]],
            memory_json_path:Path
        ):
        with open(memory_json_path, "w") as file:
            updated_memory = json.dump(updated_memory, file, indent=4)
    
    def create_index(
            self,
            embeddings: np.ndarray,
            index_type: str = "flat"
        ):
        if index_type == "flat":
            index = self.indf.create_flat_index(embeddings=embeddings)
        return index

    
    def index_insert(
        self,
        changes: List[Dict[str, str]],
        db_folder_path: Path,
        ):
        # Add insertion changes to memory
        for change in changes:
            self.pdf_change_to_memory(change=change)
        
        # Index insertion
        for key, value in self.change_dict.items():
            # Open corresponding index if already created, if not initialize one
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                index_object["pdf_path"].extend(path for path in value["pdf_path"])
                index_object["pdf_sentence_amount"].extend(sentence_amount for sentence_amount in value["pdf_sentence_amount"])
                index_object["sentences"].extend(sentence for sentence in value["sentences"])
                index_object["embeddings"] = np.vstack((index_object["embeddings"], value["embeddings"]))
                
                self.indf.save_index(
                    index_object=index_object,
                    save_path=index_path
                )
            except FileNotFoundError:
                self.indf.save_index(index_object=value, save_path=index_path)
        
        self.clean_processor()
    
    def index_update(
        self,
        changes: List[Dict[str, str]],
        db_folder_path: Path,
        ):
        # Add update changes to memory
        for change in changes:
            self.pdf_change_to_memory(change=change)
        
        # Index update
        for key, value in self.change_dict.items():
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                # Take changed file indexes
                file_path_indexes = []
                for pdf_path in value["pdf_path"]:
                    file_path_indexes.append(index_object["pdf_path"].index(pdf_path))            
                # Update corresponding index and sentences with matching change and index object according to sentence amounts
                cumulative_index = 0
                diff = 0
                for i, file_index in enumerate(file_path_indexes):
                    # Data assignments
                    change_index_start = sum(sum(page_sentence_amount) for page_sentence_amount in index_object["pdf_sentence_amount"][:file_index]) + diff
                    change_index_finish = change_index_start + sum(index_object["pdf_sentence_amount"][file_index]) + diff
                    index_object["sentences"][change_index_start:change_index_finish] = value["sentences"][cumulative_index: sum(value["pdf_sentence_amount"][i])]
                    index_object["embeddings"][change_index_start:change_index_finish] = value["embeddings"][cumulative_index: sum(value["pdf_sentence_amount"][i])]
                    # Index differences for next iteration
                    diff = len(value["sentences"][cumulative_index: sum(value["pdf_sentence_amount"][i])]) - len(index_object["sentences"][change_index_start:change_index_finish])
                    cumulative_index = sum(value["pdf_sentence_amount"][i])
                # Update sentence amounts list
                for i, file_index in enumerate(file_path_indexes):
                    index_object["pdf_sentence_amount"][file_index] = value["pdf_sentence_amount"][i]            
                # Save index object
                self.indf.save_index(
                    index_object=index_object,
                    save_path=index_path
                )
            except FileNotFoundError as e:
                raise FileExistsError(f"Index file could not be found for update!: {e}")
        
        self.clean_processor()
    
    def index_delete(
        self,
        changes: List[Dict[str, str]],
        db_folder_path: Path,
        ):
        # Delete corresponding parts from memory
        for change in changes:
            pattern = r'domain\d+'
            match = re.search(pattern, change["file_path"])
            if match:
                domain = match[0]
                index_path = db_folder_path / "indexes" / (domain + ".pickle")
                try:
                    index_object = self.indf.load_index(index_path)
                    file_path_index = index_object["pdf_path"].index(change["file_path"])

                    # Delete corresponding parts from the index object
                    change_index_start = sum(sum(page_sentence_amount) for page_sentence_amount in index_object["pdf_sentence_amount"][:file_path_index])
                    change_index_finish = change_index_start + sum(index_object["pdf_sentence_amount"][file_path_index])
                    del index_object["sentences"][change_index_start:change_index_finish]
                    index_object["embeddings"] = np.delete(index_object["embeddings"], np.arange(change_index_start, change_index_finish), axis=0)
                    index_object["pdf_path"].pop(file_path_index)
                    index_object["pdf_sentence_amount"].pop(file_path_index)

                except FileNotFoundError as e:
                    raise FileExistsError(f"Index file could not be found for update!: {e}")
    
    def search_index(
            self,
            user_query: np.ndarray,
    ):
        query_vector = self.ef.create_vector_embedding_from_query(query=user_query)
        _, I = globals.index.search(query_vector, 5)
        widen_sentences = self.widen_sentences(window_size=1, convergence_vector=I[0])
        context = f"""Context1: {widen_sentences[0]}
        Context2: {widen_sentences[1]}
        Context3: {widen_sentences[2]}
        Context4: {widen_sentences[3]}
        Context5: {widen_sentences[4]}
        """
        resources = self.extract_resources(convergence_vector=I[0])
        resources_text = "- References in " + globals.selected_domain + ":"
        for i, resource in enumerate(resources):
            resources_text += textwrap.dedent(f"""
                {i+1}
                - PDF Name: {resource["pdf_name"].split("/")[-1]}
                - Page Number: {resource["page"]}
            """)
        return self.cf.response_generation(query=user_query, context=context), resources_text
    
    def pdf_change_to_memory(self, change: Dict):
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
                self.change_dict[domain]["pdf_sentence_amount"].append(pdf_data["page_sentence_amount"])
                self.change_dict[domain]["sentences"].extend(pdf_data["sentences"])
                self.change_dict[domain]["embeddings"] = np.vstack((self.change_dict[domain]["embeddings"], pdf_embeddings))
            else:
                self.change_dict[domain] = {
                    "pdf_path": [change["file_path"]],
                    "pdf_sentence_amount": [pdf_data["page_sentence_amount"]],
                    "sentences": pdf_data["sentences"],
                    "embeddings": pdf_embeddings
                }

    def extract_embeddings_from_index(self, index):
        num_vectors = index.ntotal
        dimension = index.d
        all_vectors = np.empty((num_vectors, dimension), dtype=np.float32)
        return index.reconstruct_n(0, num_vectors, all_vectors)

    def widen_sentences(self, window_size: int, convergence_vector: np.ndarray):  
        widen_sentences = []
        for index in convergence_vector:
            start = max(0, index - window_size)
            end = min(len(globals.sentences) - 1, index + window_size)
            widen_sentences.append(f"{globals.sentences[start]} {globals.sentences[index]} {globals.sentences[end]}")
        return widen_sentences

    def extract_resources(self, convergence_vector: np.ndarray):
        resources = []
        for index in convergence_vector:
            cumulative_pdf_sentence_sum = 0
            for i, sentence_amount in enumerate(globals.pdf_sentence_amount):
                cumulative_pdf_sentence_sum += sum(sentence_amount)
                if cumulative_pdf_sentence_sum > index:
                    cumulative_page_sentence_sum = 0
                    for j, page_sentence_amount in enumerate(sentence_amount):
                        cumulative_page_sentence_sum += page_sentence_amount
                        if sum(sum(page_sentence_amount) for page_sentence_amount in globals.pdf_sentence_amount[:i]) + cumulative_page_sentence_sum  > index:
                            resource = {"pdf_name": globals.pdf_files[i], "page": j + 1}
                            if resource not in resources:
                                resources.append(resource)
                            break
        return resources

    def clean_processor(self):
        self.change_dict = {}
    
