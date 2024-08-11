import faiss
import globals
import pickle
from tkinter import filedialog


class IndexingFunctions:
    def __init__(self):
        pass

    def create_index(self):
        dimension = len(globals.pdf_embeddings[0])
        vector = globals.pdf_embeddings
        index = faiss.IndexFlatL2(dimension)
        index.add(vector)
        globals.index = index
        index_bytes = faiss.serialize_index(index=index)
        self.save_index(index_bytes=index_bytes)

    def load_index(self, index_path):
        with open(index_path, "rb") as f:
            index_object = pickle.load(f)
        return index_object

    def save_index(self, index_bytes, sentences, save_path):
        index_object = {"index": index_bytes, "sentences": sentences}
        with open(save_path, "wb") as f:
            pickle.dump(index_object, f)
