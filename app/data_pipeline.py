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
            
            if file_name.split(".")[-1] not in ["pdf", "docx", "txt", "rtf"]:
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
            self.file_change_to_memory(change=change)
        
        # Index insertion
        for key, value in self.change_dict.items():
            # Open corresponding index if already created, if not initialize one
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                index_object["file_path"].extend(path for path in value["file_path"])
                index_object["file_sentence_amount"].extend(sentence_amount for sentence_amount in value["file_sentence_amount"])
                index_object["sentences"].extend(sentence for sentence in value["sentences"])
                index_object["date"].extend(date for date in value["date"])
                index_object["file_header"].extend(date for date in value["file_header"])
                index_object["page_num"].extend(page for page in value["page_num"])
                index_object["block_num"].extend(block for block in value["block_num"])
                index_object["is_header"].extend(header for header in value["is_header"])
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
            self.file_change_to_memory(change=change)
        
        # Index update
        for key, value in self.change_dict.items():
            index_path = db_folder_path / "indexes" / (key + ".pickle")
            try:
                index_object = self.indf.load_index(index_path)
                # Take changed file indexes
                file_path_indexes = []
                for file_path in value["file_path"]:
                    file_path_indexes.append(index_object["file_path"].index(file_path))           
                # Update corresponding index and sentences with matching change and index object according to sentence amounts
                cumulative_index = 0
                diff = 0
                for i, file_index in enumerate(file_path_indexes):
                    # Data assignments
                    change_index_start = sum(sum(page_sentence_amount) for page_sentence_amount in index_object["file_sentence_amount"][:file_index]) + diff
                    change_index_finish = change_index_start + sum(index_object["file_sentence_amount"][file_index]) + diff
                    index_object["sentences"][change_index_start:change_index_finish] = value["sentences"][cumulative_index: sum(value["file_sentence_amount"][i])]
                    index_object["is_header"][change_index_start:change_index_finish] = value["is_header"][cumulative_index: sum(value["file_sentence_amount"][i])]
                    index_object["page_num"][change_index_start:change_index_finish] = value["page_num"][cumulative_index: sum(value["file_sentence_amount"][i])]
                    index_object["block_num"][change_index_start:change_index_finish] = value["block_num"][cumulative_index: sum(value["file_sentence_amount"][i])]
                    index_object["embeddings"][change_index_start:change_index_finish] = value["embeddings"][cumulative_index: sum(value["file_sentence_amount"][i])]
                    # Index differences for next iteration
                    diff = len(value["sentences"][cumulative_index: sum(value["file_sentence_amount"][i])]) - len(index_object["sentences"][change_index_start:change_index_finish])
                    cumulative_index = sum(value["file_sentence_amount"][i])
                # Update sentence amounts list
                for i, file_index in enumerate(file_path_indexes):
                    index_object["file_sentence_amount"][file_index] = value["file_sentence_amount"][i]
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
                    file_path_index = index_object["file_path"].index(change["file_path"])

                    # Delete corresponding parts from the index object
                    change_index_start = sum(sum(page_sentence_amount) for page_sentence_amount in index_object["file_sentence_amount"][:file_path_index])
                    change_index_finish = change_index_start + sum(index_object["file_sentence_amount"][file_path_index])
                    del index_object["sentences"][change_index_start:change_index_finish]
                    del index_object["is_header"][change_index_start:change_index_finish]
                    del index_object["page_num"][change_index_start:change_index_finish]
                    del index_object["block_num"][change_index_start:change_index_finish]
                    index_object["embeddings"] = np.delete(index_object["embeddings"], np.arange(change_index_start, change_index_finish), axis=0)
                    index_object["file_path"].pop(file_path_index)
                    index_object["date"].pop(file_path_index)
                    index_object["file_header"].pop(file_path_index)
                    index_object["file_sentence_amount"].pop(file_path_index)
                   
                   #Removing pickle if file is empty
                    if len(index_object["file_path"]) == 0:
                        Path.unlink(index_path)
                    else:    
                      # Save index object
                        self.indf.save_index(
                            index_object=index_object,
                            save_path=index_path
                         )

                except FileNotFoundError as e:
                    raise FileExistsError(f"Index file could not be found for update!: {e}")
                
    def index_filter(
            self,
            index_object,
            date = None
        ):
        shape = index_object["embeddings"].shape
        filtered_index = {
                "file_path": [],
                "file_sentence_amount": [],
                "sentences" : [],
                "date" : [],
                "file_header" : [],
                "is_header": [],
                "page_num": [],
                "block_num": [],
                "embeddings": np.empty(shape=shape)
        }
        file_path_indexes = []
        if date:
            date = datetime.strptime(date,"%m/%d/%y")
            for i in range(len(index_object["file_path"])):
                created_date_str = index_object["date"][i]
                created_date = datetime.strptime(created_date_str,"%y-%m-%d")
                if created_date >= date:
                        file_path_indexes.append(i)
                        try:
                            filtered_index["file_path"].append(index_object["file_path"][i])
                            filtered_index["file_sentence_amount"].append(index_object["file_sentence_amount"][i])
                            filtered_index["date"].append(index_object["date"][i])
                            filtered_index["file_header"].append(index_object["file_header"][i])
                        except FileNotFoundError as e:
                            raise FileExistsError(f"Index file could not be found for filtering!: {e}")
                        
            for index in file_path_indexes:
                try:
                    sentence_start = sum(sum(page_sentences) for page_sentences in index_object["file_sentence_amount"][:index])
                    sentence_end =  sentence_start + sum(index_object["file_sentence_amount"][index])

                    filtered_index["sentences"].extend(index_object["sentences"][sentence_start:sentence_end])
                    filtered_index["is_header"].extend(index_object["is_header"][sentence_start:sentence_end])
                    filtered_index["page_num"].extend(index_object["page_num"][sentence_start:sentence_end])
                    filtered_index["block_num"].extend(index_object["block_num"][sentence_start:sentence_end])
                    filtered_index["boost"].extend(index_object["boost"][sentence_start:sentence_end])
                    filtered_index["embeddings"] = np.vstack((index_object["embeddings"][sentence_start:sentence_end],filtered_index["embeddings"]))

                except FileNotFoundError as e:
                    raise FileExistsError(f"Index file could not be found for filtering!: {e}")
            else:
                return filtered_index
        else:
            return index_object

    def generate_additional_queries(self, query):
        return self.cf.query_generation(query=query)

    def search_index(
            self,
            user_query: np.ndarray,
    ):
        all_widen_sentences = []
        dict_resource = {}
        if user_query[0][0] == "[":
            processed_queries = self.query_preprocessing(user_query)
            original_query = processed_queries[0]
        else:
            processed_queries = user_query.split("\n")
            processed_queries = processed_queries[:6]
            original_query = processed_queries[0]

        boost = self.search_index_header(query=original_query)
        boost_file_header = self.search_file_header_index(query=original_query)
        boost_combined = 0.75 * boost + 0.25 * boost_file_header
        for i,query in enumerate(processed_queries):
            if(query=="\n" or query=="\n\n" or query=="no response" or query==""):
                continue
            else:
                query_vector = self.ef.create_vector_embedding_from_query(query=query)
                D, I = globals.index.search(query_vector, len(globals.sentences))
                for j, indexes in enumerate(I[0]):
                    if indexes in dict_resource:
                        dict_resource[indexes].append(D[0][j])
                    else:
                        dict_resource[indexes] = [D[0][j]]
        try:
            avg_index_list = self.avg_resources(dict_resource)
            for key in avg_index_list:
                avg_index_list[key] *= boost_combined[key]
            sorted_dict = dict(sorted(avg_index_list.items(), key=lambda item: item[1]))
            indexes = np.array(list(sorted_dict.keys()))
            sorted_sentences = indexes[:10]
        except ValueError as e:
            original_query = "Please provide meaningful query:"
            print(f"{original_query, {e}}")

        for i in range(len(sorted_sentences)):
            if i == 0:
                widen_sentences = self.widen_sentences(window_size=3, convergence_vector=sorted_sentences[i:i+1])
            elif i in range(1,4):
                widen_sentences = self.widen_sentences(window_size=2, convergence_vector=sorted_sentences[i:i+1])
            else:
                widen_sentences = self.widen_sentences(window_size=1, convergence_vector=sorted_sentences[i:i+1])
            all_widen_sentences.extend(widen_sentences)

        context = self.create_dynamic_context(sentences=all_widen_sentences)
        resources = self.extract_resources(convergence_vector=sorted_sentences)
        resources_text = "- References in " + globals.selected_domain + ":"
        for i, resource in enumerate(resources):
            resources_text += textwrap.dedent(f"""
                {i+1}
                - file Name: {resource["file_name"].split("/")[-1]}
                - Page Number: {resource["page"]}
            """)
        return self.cf.response_generation(query=original_query, context=context), resources_text

    def file_change_to_memory(self, change: Dict):
        # Create embeddings
        file_data = self.rf.read_file(file_path=change["file_path"])
        self.rf._extract_file_header(file_path=change["file_path"],file_data=file_data)
        file_embeddings = self.ef.create_vector_embeddings_from_sentences(sentences=file_data["sentences"])

        # Detect changed domain
        pattern = r'domain\d+'
        match = re.search(pattern, change["file_path"])
        if match:
            domain = match[0]
            if domain in self.change_dict.keys():
                self.change_dict[domain]["file_path"].append(change["file_path"])
                self.change_dict[domain]["file_sentence_amount"].append(file_data["page_sentence_amount"])
                self.change_dict[domain]["sentences"].extend(file_data["sentences"])
                self.change_dict[domain]["date"].extend(file_data["date"])
                self.change_dict[domain]["file_header"].extend(file_data["file_header"])
                self.change_dict[domain]["page_num"].extend(file_data["page_num"])
                self.change_dict[domain]["block_num"].extend(file_data["block_num"])
                self.change_dict[domain]["is_header"].extend(file_data["is_header"])
                self.change_dict[domain]["embeddings"] = np.vstack((self.change_dict[domain]["embeddings"], file_embeddings))
            else:
                self.change_dict[domain] = {
                    "file_path": [change["file_path"]],
                    "file_sentence_amount": [file_data["page_sentence_amount"]],
                    "sentences": file_data["sentences"],
                    "date" : file_data["date"],
                    "file_header" : file_data["file_header"],
                    "embeddings": file_embeddings,
                    "page_num" : file_data["page_num"],
                    "block_num" : file_data["block_num"],
                    "is_header" : file_data["is_header"],
                }

    # Boost most semanticaly similar headers sentences
    def search_index_header(self, query):
        boost = np.ones(len(globals.sentences))
        original_query = query.split('\n')[0]

        header_indexes = [index for index in range(len(globals.is_header)) if globals.is_header[index]]
        headers = [globals.sentences[header_index] for header_index in header_indexes]

        header_embeddings = self.ef.create_vector_embeddings_from_sentences(sentences=headers)
        index_header = self.create_index(embeddings=header_embeddings)

        D,I = index_header.search(self.ef.create_vector_embedding_from_query(original_query),10)
        filtered_header_indexes = [header_index for index, header_index in enumerate(I[0]) if D[0][index] < 0.40]
        for i,filtered_index in enumerate(filtered_header_indexes):
            try:
                start = header_indexes[filtered_index] + 1
                end = header_indexes[filtered_index + 1]
                if i == 0:
                    boost[start:end] *= 0.7
                elif i in range(1,3):
                    boost[start:end] *= 0.8
                else:
                    boost[start:end] *= 0.9
            except IndexError as e:
                print(f"List is out of range {e}")
        return boost

    # Search on file header function
    def search_file_header_index(self,query):
        boost = np.ones(len(globals.sentences))
        original_query = query.split('\n')[0]

        file_header_embeddings = self.ef.create_vector_embeddings_from_sentences(globals.file_headers)
        file_header_index = self.create_index(file_header_embeddings)

        D,I = file_header_index.search(self.ef.create_vector_embedding_from_query(query=original_query),len(globals.file_headers))
        if sum(D[0])/len(D[0]) < 0.45:
            file_indexes = [file_index for index, file_index in enumerate(I[0]) if D[0][index] < sum(D[0])/len(D[0])]
        else:
            file_indexes = [file_index for index, file_index in enumerate(I[0]) if D[0][index] < 0.45]

        if file_indexes:
            for i, index in enumerate(file_indexes):
                try:
                    start = sum(sum(page_sentence_amount) for page_sentence_amount in globals.file_sentence_amount[:index])
                    end = start + sum(globals.file_sentence_amount[index])
                    if i == 0:
                        boost[start:end] *= 0.7
                    elif i == 1:
                        boost[start:end] *= 0.8
                    else:
                        boost[start:end] *= 0.9
                except IndexError as e:
                    print(f"List is out of range {e}")
        return boost
    
    def query_preprocessing(self, user_query):
        clean_query_list = []
        splitted_queries = user_query.split('\n')
        for single_query in splitted_queries:
            if single_query[0] == "[" and single_query[-1] == "]":
                clean_query = single_query.split(":")[1]
                clean_query = clean_query[1:-1]
                clean_query_list.append(clean_query)
            else:
                clean_query_list.append(clean_query)
        return clean_query_list

    def create_dynamic_context(self, sentences):
        context = ""
        for i, sentence in enumerate(sentences, 1):
            context += f"Context{i}: {sentence} Confidence: {(len(sentences)-i+1)/len(sentences)} \n "
        return context

    def avg_resources(self, resources_dict):
        for key, value in resources_dict.items():
            value_mean = sum(value) / len(value)
            value_coefficient = value_mean - len(value) * 0.0025
            resources_dict[key] = value_coefficient
        return resources_dict

    def widen_sentences(self, window_size: int, convergence_vector: np.ndarray):  
        widen_sentences = []
        for index in convergence_vector:
            text = ""
            start = max(0, index - window_size)
            end = min(len(globals.sentences) - 1, index + window_size)
            for i in range(start, end+1):
                text += globals.sentences[i]
            widen_sentences.append(text)
        return widen_sentences

    def extract_resources(self, convergence_vector: np.ndarray):
        resources = []
        for index in convergence_vector:
            cumulative_file_sentence_sum = 0
            for i, sentence_amount in enumerate(globals.file_sentence_amount):
                cumulative_file_sentence_sum += sum(sentence_amount)
                if cumulative_file_sentence_sum > index:
                    cumulative_page_sentence_sum = 0
                    for j, page_sentence_amount in enumerate(sentence_amount):
                        cumulative_page_sentence_sum += page_sentence_amount
                        if sum(sum(page_sentence_amount) for page_sentence_amount in globals.file_sentence_amount[:i]) + cumulative_page_sentence_sum  > index:
                            resource = {"file_name": globals.files[i], "page": j + 1}
                            if resource not in resources:
                                resources.append(resource)
                            break
                    break            
        return resources

    def clean_processor(self):
        self.change_dict = {}

