import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
from tkinter import font as tkfont
from PIL import Image, ImageTk

from pathlib import Path
from tkinter import messagebox
import json

from app.settings_window import Window
from app.data_pipeline import FileDetector
from app.data_pipeline import FileProcessor
import globals


class App(tk.Tk):
    def __init__(
            self,
        ):
        super().__init__()
        # Initialize necessary folders
        self.config_file_path = Path(__file__).resolve().parent.parent / "utils" / "config.json"
        self.db_folder_path = ""
        self.domain_folders = []
        self.memory_file_path = ""
        self.detector = None
        self.processor = None

        # Base window
        self.geometry("1280x720")
        self.title("App")
        self.resizable(False, False)
        self.configure(bg="#222222")
        self.title("ragchat - v0.1")
        self.wm_iconbitmap("assets/ragchat_icon.ico")

        # Button Ask
        self.button_ask_image = Image.open("assets/send.png")
        self.button_ask_image = self.button_ask_image.resize((36, 36), Image.LANCZOS)
        self.button_ask_pic = ImageTk.PhotoImage(self.button_ask_image)
        self.button_ask = tk.Button(
            self,
            image=self.button_ask_pic,
            command=lambda: [self.generate_response()],
            bd=0,
            bg="#222222",
            highlightthickness=0,
            activebackground="#222222"
        )
        self.button_ask.place(x=1116, y=620, width=36, height=36)
        self.button_ask.config(state="disabled")
        
        # Button settings
        self.button_resources_image = Image.open("assets/change_resource.png")
        self.button_resources_image = self.button_resources_image.resize((108, 108), Image.LANCZOS)
        self.resources_pic = ImageTk.PhotoImage(self.button_resources_image)
        self.button_resources = tk.Button(
            self,
            image=self.resources_pic,
            command=lambda: [self.open_settings()],
            bd=0,
            bg="#222222",
            highlightthickness=0,
            activebackground="#222222"
        )
        self.button_resources.place(x=1062, y=50, width=108, height=108)
        self.button_resources.config(state="disabled")

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
            font=("Roboto", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_slogan.place(x=248, y=124, width=300, height=20)

        # Chatboxes
        self.chatbox_response = scrolledtext.ScrolledText(self, wrap=WORD)
        self.chatbox_response.tag_configure("bold", font=("Arial", 16, "bold"))
        self.chatbox_response.config(fg="black",bg="white", font=("Arial", 12))
        self.chatbox_response.bindtags((str(self.chatbox_response), str(self), "all"))
        self.chatbox_response.place(x=128, y=160, width=1024, height=450)
        self.bind_all("<MouseWheel>", self.handle_mousewheel)

        self.chatbox_ask = Text(self, wrap=WORD)
        self.chatbox_ask.tag_configure("center", justify="center")
        self.chatbox_ask.config(font=("Arial", 12),fg="black",bg="white")
        self.chatbox_ask.place(x=128, y=620, width=983, height=36)
        self.chatbox_ask.bind("<Return>", self.handle_enter)
        self.chatbox_ask.insert(1.0, "Send Message")
        self.chatbox_ask.bind("<Shift-Return>", self.handle_shift_enter)

        # Funtion to call when started
        self.after(100, self.on_start)
    
    def check_necessary_paths(self):
        try:
            with open(self.config_file_path, "r") as file:
                config_data = json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error!", f"Memory file could not be found in {self.config_file_path}!")
            self.destroy()

        if config_data[0]["db_path"]:
            self.db_folder_path = Path(config_data[0]["db_path"])
            self.memory_file_path = self.db_folder_path / "memory.json"
        else:
            if config_data[0]["environment"] == "Windows":
                db_path = f"C:/Users/{config_data[0]["user_name"]}/Documents/ragchat_local/db"
                config_data[0]["db_path"] = db_path
                self.db_folder_path = Path(db_path)
                self.memory_file_path = self.db_folder_path / "memory.json"
                with open(self.config_json_path, "w") as file:
                    config_data = json.dump(config_data, file, indent=4)
            elif config_data[0]["environment"] == "MacOS":
                # :TODO: Add configuration for macos
                raise EnvironmentError("MacOS is not yet configured for RAG Chat Local!")
            else:
                raise EnvironmentError("Only Windows and MacOS is configured for RAG Chat Local!")

    def get_domain_folder_list(self,db_folder_path: str):
        domain_folder = Path(db_folder_path) / "domains"
        domains = [folder.name for folder in domain_folder.iterdir() if folder.is_dir()]
        return domains
    
    def open_settings(self):
        settings_window = Window(
            domain_folders=self.domain_folders,
            db_folder_path=self.db_folder_path,
            memory_file_path=self.memory_file_path,
            detector=self.detector,
            processor=self.processor
        )

    def generate_response(self):
        if globals.index:
            user_query = self.chatbox_ask.get("1.0", "end-1c")
            self.display_message(message=user_query, sender="user")
            self.clear_input()
            response, resource_text = self.processor.search_index(user_query=user_query)
            answer = f"{response}\n{resource_text}"
            self.display_message(message=answer, sender="system")
        else:
            messagebox.showerror("Error!", "Please first select your resource folder in the button on the top right!")

    def display_message(self, message: str, sender: str):
        if sender == "system":
            self.chatbox_response.insert(tk.END, "ragchat\n", "bold")
            self.chatbox_response.insert(tk.END, f"{message}\n\n")
        else:
            self.chatbox_response.insert(tk.END, "you\n", "bold")
            self.chatbox_response.insert(tk.END, f"{message}\n\n")

        self.chatbox_response.update()
        self.chatbox_response.see(tk.END)
    
    def clear_input(self):
        self.chatbox_ask.delete("1.0", tk.END)
        self.chatbox_response.update()
    
    def handle_enter(self, event):
        if globals.index:
            self.generate_response()  
            return "break"
        messagebox.showerror("Error!", "Please first select your resource folder in the button on the top right!")
        return "break"


    def handle_shift_enter(self, event):
        return
    
    def handle_mousewheel(self, event):
        self.chatbox_response.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_start(self):
        self.display_message(
            message="Welcome the ragchat! Please wait ragchat to checking it's memory for any change...",
            sender="system"
        )
        self.check_necessary_paths()
        self.domain_folders = self.get_domain_folder_list(db_folder_path=self.db_folder_path)
        self.detector = FileDetector(db_folder_path=self.db_folder_path, memory_file_path=self.memory_file_path)
        self.processor = FileProcessor()
        changes, updated_memory = self.detector.check_changes()
        if any(changes.values()):
            changed_file_message = f"""Changed files detected!
            --> {len(changes["insert"])} addition
            --> {len(changes["update"])} update
            --> {len(changes["delete"])} deletion\nPlease wait ragchat to synchronize it's memory..."""
            self.display_message(
                message=changed_file_message,
                sender="system"
            )
            if changes["insert"]:
                self.processor.index_insert(
                    changes=changes["insert"],
                    db_folder_path=self.db_folder_path,
                )
            if changes["update"]:
                self.processor.index_update(
                    changes=changes["update"],
                    db_folder_path=self.db_folder_path,
                )
            if changes["delete"]:
                self.processor.index_delete(
                    changes=changes["delete"],
                    db_folder_path=self.db_folder_path,
                )
            self.processor.update_memory(updated_memory=updated_memory, memory_json_path=self.memory_file_path)
            self.display_message(
                message="Memory updated! Now ragchat knows everything select your domain and start asking!",
                sender="system"
            )
        else:
            self.display_message(
                message="Memory is sync. You can start the use ragchat! Please select your domain first!",
                sender="system"
            )
        self.button_ask.config(state="normal")
        self.button_resources.config(state="normal")
