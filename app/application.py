import tkinter as tk
from tkinter import *
from tkinter import font as tkfont
from PIL import Image, ImageTk

from pathlib import Path
import json

from app.settings_window import Window
from functions.embedding_functions import EmbeddingFunctions
from functions.chatbot_functions import ChatbotFunctions
import globals


class App(tk.Tk):
    def __init__(
            self,
        ):
        super().__init__()
        # Initialize funtion calls
        self.ef = EmbeddingFunctions()
        self.cf = ChatbotFunctions()

        # Initialize necessary folders
        self.config_file_path = Path(__file__).resolve().parent.parent / "utils" / "config.json"
        self.db_folder_path = self.get_db_folder_path(self.config_file_path)
        self.domain_folders = self.get_domain_folder_list(db_folder_path=self.db_folder_path)

        # Base window
        self.geometry("1280x720")
        self.title("App")
        self.resizable(False, False)
        self.configure(bg="#222222")
        self.title("ragchat - v0.1")
        self.wm_iconbitmap("assets/ragchat_icon.ico")

        # Buttons
        self.button_ask = tk.Button(
            self,
            text=">",
            command=lambda: [
                self.generate_response(),
            ],
        )
        self.button_ask.place(x=1070, y=620, width=36, height=36)

        self.button_select_domain = tk.Button(
            self,
            text="S",
            command=lambda: [
                self.open_settings(),
            ],
        )
        self.button_select_domain.place(x=1116, y=620, width=36, height=36)

        # Labels and images
        image = Image.open("assets/ragchat_logo.png")
        logo_pic = ImageTk.PhotoImage(image)
        label = Label(self, image=logo_pic)
        label.image = logo_pic
        label.place(x=128, y=35, width=115, height=118)

        self.label_ragchat = Label(self, text="ragchat")
        roboto_font = tkfont.Font(
            family="Roboto",
            size=30,
            weight="bold",
            slant="roman"
            )
        self.label_ragchat.config(
            font=roboto_font,
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_ragchat.place(x=248, y=74, width=300, height=45)

        self.label_slogan = Label(self, text="What do you want to know?")
        self.label_slogan.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_slogan.place(x=248, y=124, width=300, height=20)

        # Chatboxes
        self.chatbox_response = Text(self, wrap=WORD)
        self.chatbox_response.tag_configure("center", justify="center")
        self.chatbox_response.config(
            font=("Times New Roman", 14),
            fg="black",
            bg="white"
        )
        self.chatbox_response.place(x=128, y=160, width=1024, height=450)

        self.chatbox_ask = Text(self, wrap=WORD)
        self.chatbox_ask.tag_configure("center", justify="center")
        self.chatbox_ask.insert(1.0, "Send Message")
        self.chatbox_ask.config(
            font=("Arial", 12),
            fg="black",
            bg="white"
        )
        self.chatbox_ask.place(x=128, y=620, width=932, height=36)
    
    def get_db_folder_path(self,
                           config_file_path: Path
        ):
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return config[0]["db_path"]

    def get_domain_folder_list(self,
                               db_folder_path: str
        ):
        domain_folder = Path(db_folder_path) / "domains"
        domains = [folder.name for folder in domain_folder.iterdir() if folder.is_dir()]
        return domains
    
    def open_settings(self):
        settings_window = Window(
            domain_folders=self.domain_folders,
            config_file_path=self.config_file_path
        )

    def _take_input(self):
        input = self.chatbox_ask.get("1.0", "end-1c")
        return input

    def _create_query_vector(self):
        query = self._take_input()
        return self.ef.create_vector_embedding_from_query(query=query)

    def generate_response(self):
        query = self._take_input()
        query_vector = self._create_query_vector()
        _, I = globals.index.search(query_vector, 5)

        # Create context
        context = ""
        for i, index in enumerate(I[0]):
            answer = globals.sentences[index]
            context += f"Context {i + 1}: {answer}\n"
        
        # Generate response
        response = self.cf.response_generation(query=self._take_input(), context=context)

        # Display response
        self.display_message(message=query, sender="user")
        self.display_message(message=response, sender="system")

    def display_message(self, message: str, sender: str):
        if sender == "system":
            message = f"RAG Chat --> {message}"
        else:
            message = f"You --> {message}"

        self.chatbox_response.insert(tk.END, message + "\n")
