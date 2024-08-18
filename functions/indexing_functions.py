import faiss
import pickle
import numpy as np
from typing import Dict
from pathlib import Path


class IndexingFunctions:
    def __init__(self):
        pass

    def create_flat_index(self,
                    embeddings:np.ndarray,
        ):
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index

    def load_index(self,
                   index_path: Path
        ):
        with open(index_path, "rb") as f:
            index_object = pickle.load(f)
        return index_object

    def save_index(self,
                   index_object: Dict,
                   save_path: Path
        ):
        with open(save_path, "wb") as f:
            pickle.dump(index_object, f)
