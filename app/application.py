import tkinter as tk
from tkinter import *
from functions.reading_functions import ReadingFunctions
from functions.embedding_functions import EmbeddingFunctions
from functions.indexing_functions import IndexingFunctions
from functions.chatbot_functions import ChatbotFunctions
from functions.documentation_functions import DocumentationFunctions
import globals
from datetime import datetime

ef = EmbeddingFunctions()
cf = ChatbotFunctions()
rf = ReadingFunctions()
indf = IndexingFunctions()
lg = DocumentationFunctions()

globals.kpi_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Base window
        self.geometry("960x720")
        self.title("RAG Chat")
        self.resizable(False, False)
        self.configure(bg="gray26")

        # Button: Select PDF File
        self.button_select_pdf = tk.Button(
            self,
            text="Select PDF",
            command=lambda: [
                rf.select_pdf_file(),
                rf.read_pdf(pdf_path=globals.pdf_path),
                self.display_message(
                    message="Selected PDF: " + globals.pdf_path.split("/")[-1],
                    sender="system",
                ),
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
                lg.performance_logger(globals.kpi_dict),
                self.display_message(
                    message= "Index Created",
                    sender="system",
                ),
            ],
        )
        self.button_create_index.place(x=5, y=87, width=175, height=30)

        # Button: Load Index
        self.button_load_index = tk.Button(
            self,
            text="Load Index",
            command=lambda: [
                indf.load_index(),
                self.display_message(
                    message="Index Loaded ",
                    sender="system",
                ),
            ],
        )
        self.button_load_index.place(x=5, y=127, width=175, height=30)

        # Button: Search
        self.button_ask = tk.Button(
            self,
            text=">",
            command=lambda: [
                self.generate_response(),
            ],
        )
        self.button_ask.place(x=923, y=683, width=37, height=37)

        # Labels
        self.label_manage = Label(self, text="Manage")
        self.label_manage.config(
            font=("Helvetica", 16),
            background="gray14",
            foreground="white",
            anchor="center",
        )
        self.label_manage.place(x=0, y=0, width=187, height=39)

        self.label_chat = Label(self, text="Chat")
        self.label_chat.config(
            font=("Helvetica", 16),
            background="gray14",
            foreground="white",
            anchor="center",
        )
        self.label_chat.place(x=187, y=0, width=773, height=39)

        # Response Chatbox
        self.chatbox_response = Text(self, wrap=WORD)
        self.chatbox_response.tag_configure("center", justify="center")
        self.chatbox_response.config(
            font=("Times New Roman", 14),
            fg="black",
            bg="gray85"
        )
        self.chatbox_response.place(x=187, y=39, width=773, height=642)

        # Message Send Chatbox
        self.chatbox_ask = Text(self, wrap=WORD)
        self.chatbox_ask.tag_configure("center", justify="center")
        self.chatbox_ask.insert(1.0, "Send Message")
        self.chatbox_ask.config(
            font=("Arial", 12),
            fg="black",
            bg="gray85"
        )
        self.chatbox_ask.place(x=187, y=683, width=734, height=37)
        
    def _take_input(self):
        input = self.chatbox_ask.get("1.0", "end-1c")
        return input

    def _create_query_vector(self):
        query = self._take_input()
        return ef.create_vector_embedding_from_query(query=query)

    def generate_response(self):
        query = self._take_input()
        query_vector = self._create_query_vector()
        _, I = globals.index.search(query_vector, 5) # to do context cümlelerini genişletme 

        # Create context
        context = ""
        for i, index in enumerate(I[0]):
            answer = globals.pdf_sentences[index]
            context += f"Context {i + 1}: {answer}\n"
        
        # Generate response
        response = cf.response_generation(query=self._take_input(), context=context)

        # Display response
        self.display_message(message=query, sender="user")
        self.display_message(message=response, sender="system")

    def display_message(self, message: str, sender: str):
        current_time = datetime.now().strftime("%H:%M:%S")
        if sender == "system":
            message = f"RAG Chat --> {message} at {current_time}"
        else:
            message = f"You --> {message} at {current_time}"

        self.chatbox_response.insert(tk.END, message + "\n")
