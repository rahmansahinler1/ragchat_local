import tkinter as tk
from tkinter import *
from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.prompting_functions import PromptingFunctions
from functions.indexing_functions import IndexingFunctions
import globals

rf = ReadingFunctions()
ef = EmbeddingFunctions()
pf = PromptingFunctions()
indf = IndexingFunctions()


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Base window
        self.geometry("960x720")
        self.title("RagBot")
        self.resizable(False, False)
        self.configure(bg="#D3D3D3")

        # Button: Select PDF File
        self.button_select_pdf = tk.Button(
            self,
            text="Select PDF",
            command=lambda: [
                rf.select_pdf_file(label=self.label_selected_pdf),
                rf.read_pdf(pdf_path=globals.pdf_path),
            ],
        )
        self.button_select_pdf.place(x=5, y=47, width=175, height=30)

        # Button: Create Index
        self.button_create_index = tk.Button(
            self,
            text="Create Index",
            command=lambda: [
                ef.create_vector_embeddings_from_pdf(),
                indf.create_index(),
            ],
        )
        self.button_create_index.place(x=5, y=87, width=175, height=30)

        # Button: Load Index
        self.button_load_index = tk.Button(
            self,
            text="Load Index",
            command=lambda: [
                indf.load_index(),
            ],
        )
        self.button_load_index.place(x=5, y=127, width=175, height=30)

        # Button: Search
        self.button_search = tk.Button(
            self,
            text=">",
            command=lambda: [self._update_query_vector(), self.display_response()],
        )
        self.button_search.place(x=923, y=683, width=35, height=35)

        # Labels
        self.label_settings = Label(self, text="Settings")
        self.label_settings.config(
            font=("Times New Roman", 12),
            background="white",
            anchor="w",
        )
        self.label_settings.place(x=0, y=2, width=185, height=35)

        self.label_chat = Label(self, text="Chat")
        self.label_chat.config(
            font=("Times New Roman", 12),
            background="white",
            anchor="w",
        )
        self.label_chat.place(x=187, y=2, width=771, height=35)

        # Response Chatbox
        self.chatbox_response = Text(self, wrap=WORD)
        self.chatbox_response.tag_configure("center", justify="center")
        self.chatbox_response.config(
            font=("Times New Roman", 14), fg="black", bg="white"
        )
        self.chatbox_response.place(x=187, y=39, width=771, height=642)

        # Answer Chatbox
        self.chat_box_ask = Text(self, wrap=WORD)
        self.chat_box_ask.tag_configure("center", justify="center")
        self.chat_box_ask.insert(1.0, "Message RAGBot here!")
        self.chat_box_ask.config(font=("Arial", 8), fg="black", bg="white")
        self.chat_box_ask.place(x=187, y=683, width=734, height=35)

    def _take_input(self):
        input = self.chat_box_ask.get("1.0", "end-1c")
        return input

    def _update_query_vector(self):
        query = self._take_input()
        globals.query_vector = ef.create_vector_embedding_from_query(query=query)

    def _take_response(self):
        query_vector = globals.query_vector
        D, I = globals.index.search(query_vector, 5)
        return I

    def display_response(self):
        self.chatbox_answer.delete(1.0, "end")
        sentence_indexes = self._take_response()
        for i in sentence_indexes[0]:
            answer = globals.pdf_sentences[i]
            self.chatbox_answer.insert(1.0, f"Answer:{i} --> {answer}\n\n")
