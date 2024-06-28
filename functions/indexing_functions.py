import os
import numpy as np
import faiss

# from dotenv import load_dotenv
import globals
from tkinter import filedialog


class IndexingFunctions:
    def __init__(self):
        pass

    def create_index(self, nlist=50, k=5, nprobe=10):
        """
        This function will create the index from given vector.
        It uses facebook's faiss library to index.
        """
        dimension = len(globals.pdf_embeddings[0])
        vector = globals.pdf_embeddings
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        index.train(vector)
        index.add(vector)
        index.nprobe = nprobe

        globals.index = index

    def read_index(self):
        index_path = filedialog.askopenfilename(title="Select Index")
        globals.index = faiss.read_index(index_path)

    def _save_index(self, index, name):
        faiss.write_index(index, f"/indexes/{name}.index")
