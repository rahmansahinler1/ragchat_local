import faiss
import globals
import pickle
from tkinter import filedialog
import time 


class IndexingFunctions:
    def __init__(self):
        pass

    def create_index(self):
        """
        This function will create the index from given vector.
        It uses facebook's faiss library to index.
        """
        total_time = 0
        start_time = time.time()
        dimension = len(globals.pdf_embeddings[0])
        vector = globals.pdf_embeddings
        index = faiss.IndexFlatL2(dimension)
        index.add(vector)
        globals.index = index
        index_bytes = faiss.serialize_index(index=index)
        self._save_index(index_bytes=index_bytes)
        end_time = time.time()
        total_time = end_time-start_time
        globals.total_ind_time = total_time
        globals.avg_ind_time = total_time/len(globals.pdf_embeddings)
        globals.update_kpi_dict()

    def load_index(self):
        index_object_path = filedialog.askopenfilename(title="Select Index")
        with open(index_object_path, "rb") as f:
            index_object = pickle.load(f)
        globals.index = faiss.deserialize_index(index_object["index"])
        globals.pdf_sentences = index_object["sentences"]

    def _save_index(self, index_bytes):
        index_object = {"index": index_bytes, "sentences": globals.pdf_sentences}
        name = globals.pdf_path.split("/")[-1].split(".")[0]
        path = "db/" + name
        with open(path + ".pickle", "wb") as f:
            pickle.dump(index_object, f)
