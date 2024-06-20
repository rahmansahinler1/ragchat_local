import tkinter as tk
from tkinter import *
from functions.reading_functions import ReadingFunctions

rf = ReadingFunctions()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Base window
        self.geometry("625x700")
        self.title("RagBot")
        self.resizable(False, False)
        self.configure(bg="#D3D3D3")

        # Buttons
        self.button_select_folder = tk.Button(
            self,
            text="Select Folder",
            command=lambda: rf.select_pdf_folder(label=self.label_selected_folder),
        )
        self.button_select_folder.place(x=10, y=50, width=250, height=30)

        self.button_start_rag = tk.Button(self, text="Start RAG Pipeline", command=None)
        self.button_start_rag.place(x=365, y=50, width=250, height=30)

        self.button_ask = tk.Button(self, text="Send Message", command=None)
        self.button_ask.place(x=10, y=660, width=250, height=30)

        self.button_copy_answer = tk.Button(self, text="Copy Answer", command=None)
        self.button_copy_answer.place(x=365, y=660, width=250, height=30)

        # Labels
        self.label_welcome = Label(
            self, text="Welcome to RAGBot! Your personal PDF assistant!"
        )
        self.label_welcome.config(font=("Arial", 12))
        self.label_welcome.place(x=10, y=10, width=605, height=30)

        self.label_selected_folder = Label(self, text="Selected Folder: None Selected")
        self.label_selected_folder.config(font=("Arial", 12), anchor="w")
        self.label_selected_folder.place(x=10, y=90, width=605, height=30)

        self.label_status = Label(self, text="Status")
        self.label_status.config(font=("Arial", 12), anchor="center")
        self.label_status.place(x=10, y=130, width=605, height=30)

        self.label_chat = Label(self, text="Chat with RAGBot")
        self.label_chat.config(font=("Arial", 12))
        self.label_chat.place(x=10, y=350, width=605, height=30)

        # Status Chatbox
        self.chatbox_answer = Text(self, wrap=WORD)
        self.chatbox_answer.tag_configure("center", justify="center")
        self.chatbox_answer.insert(1.0, "Not Started")
        self.chatbox_answer.config(font=("Arial", 8), fg="black", bg="white")
        self.chatbox_answer.place(x=10, y=170, width=605, height=150)

        # Response Chatbox
        self.chatbox_answer = Text(self, wrap=WORD)
        self.chatbox_answer.tag_configure("center", justify="center")
        self.chatbox_answer.insert(1.0, "Answer will appear here")
        self.chatbox_answer.config(font=("Arial", 8), fg="black", bg="white")
        self.chatbox_answer.place(x=10, y=390, width=605, height=200)

        # Answer Chatbox
        self.chat_box_ask = Text(self, wrap=WORD)
        self.chat_box_ask.tag_configure("center", justify="center")
        self.chat_box_ask.insert(1.0, "Message RAGBot here!")
        self.chat_box_ask.config(font=("Arial", 8), fg="black", bg="white")
        self.chat_box_ask.place(x=10, y=600, width=605, height=50)
