import pandas as pd
import faiss
import globals
from tkinter import filedialog


class IndexingFunctions:
    def __init__(self):
        pass

    def create_index(self):
        """
        This function will create the index from given vector.
        It uses facebook's faiss library to index.
        """
        dimension = len(globals.pdf_embeddings[0])
        vector = globals.pdf_embeddings
        index = faiss.IndexFlatL2(dimension)
        index.add(vector)
        globals.index = index
        self._save_index()

    def load_index(self):
        index_path = filedialog.askopenfilename(title="Select Index")
        globals.index = faiss.read_index(index_path)
        sentences_path = index_path.split(".")[0] + ".csv"
        globals.pdf_sentences = pd.read_csv(sentences_path)

    def _save_index(self):
        name = globals.pdf_path.split("/")[-1].split(".")[0]
        faiss.write_index(globals.index, f"indexes/index_{name}.index")
        globals.pdf_sentences.to_csv(f"indexes/sentences_{name}.csv", index=False)
