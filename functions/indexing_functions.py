import faiss
import pickle
import numpy as np
from typing import List
from pathlib import Path


class IndexingFunctions:
    def __init__(self):
        pass

    def create_index_bytes(self,
                    embeddings:np.ndarray,
        ):
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return faiss.serialize_index(index=index)

    def load_index(self,
                   index_path: Path
        ):
        with open(index_path, "rb") as f:
            index_object = pickle.load(f)
        return index_object

    def save_index(self,
                   index_bytes,
                   sentences,
                   save_path
        ):
        index_object = {"index": index_bytes, "sentences": sentences}
        with open(save_path, "wb") as f:
            pickle.dump(index_object, f)
