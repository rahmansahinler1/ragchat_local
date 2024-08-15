from tkinter import *
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
from typing import List
from PIL import Image, ImageTk
from pathlib import Path
import json
import globals
from functions.indexing_functions import IndexingFunctions
import faiss


class Window(tk.Toplevel):
    def __init__(
            self,
            domain_folders: List[str],
            config_file_path: Path,
        ):
        super().__init__()
        self.main_folder_path = Path(__file__).resolve().parent.parent
        self.domain_folders = domain_folders
        self.config_file_path = config_file_path
        self.resources_folder_path = self.get_resources_folder_path()
        self.indf = IndexingFunctions()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Base window
        self.geometry("640x720+100+100")
        self.title("App")
        self.resizable(False, False)
        self.configure(bg="#222222")
        self.title("settings")
        self.wm_iconbitmap("assets/ragchat_icon.ico")

        # Buttons
        self.button_change_resource = tk.Button(
            self,
            text="Reset",
            command=lambda: [
                None,
            ],
        )
        self.button_change_resource.place(x=380, y=317, width=70, height=20)

        self.button_run_file_change = tk.Button(
            self,
            text="Run",
            command=lambda: [
                None,
            ],
        )
        self.button_run_file_change.place(x=380, y=357, width=70, height=20)

        # Labels and images
        image = Image.open("assets/resources.png")
        resources_pic = ImageTk.PhotoImage(image)
        label = Label(self, image=resources_pic)
        label.image = resources_pic
        label.place(x=25, y=25, width=75, height=77)

        self.label_settings = Label(self, text="settings")
        roboto_font = tkfont.Font(
            family="Roboto",
            size=30,
            weight="bold",
            slant="roman"
            )
        self.label_settings.config(
            font=roboto_font,
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_settings.place(x=107, y=40, width=175, height=45)

        self.label_select_folder = Label(self, text="Select Resource Folder")
        self.label_select_folder.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_select_folder.place(x=30, y=107, width=300, height=20)

        self.label_reset_resource_folder = Label(self, text="Reset your resources folder -->")
        self.label_reset_resource_folder.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_reset_resource_folder.place(x=40, y=317, width=320, height=20)

        self.label_run_file_detection = Label(self, text="Run file detection                  -->")
        self.label_run_file_detection.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_run_file_detection.place(x=40, y=357, width=320, height=20)

        # Listbox
        self.listbox_domains = Listbox(self)
        self.listbox_domains.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
        )
        self.listbox_domains.place(x=40, y=137, width=290, height=150)
        for domain_name in self.domain_folders:
            listbox_entry = f"--> {domain_name}"
            self.listbox_domains.insert(END, listbox_entry)
        self.listbox_domains.bind('<<ListboxSelect>>', self.get_selected_domain)
        if globals.selected_domain:
            for i, domain in enumerate(self.domain_folders):
                if domain == globals.selected_domain:
                    self.listbox_domains.selection_set(i)
                    self.listbox_domains.see(i)
                    break

        # Chatbox
        self.chatbox_log = Text(self, wrap=WORD)
        self.chatbox_log.tag_configure("center", justify="center")
        self.chatbox_log.config(
            font=("Times New Roman", 14),
            fg="black",
            bg="white"
        )
        self.chatbox_log.place(x=30, y=407, width=580, height=283)
        self.chatbox_log.insert(tk.END, f"Resources folder path: {self.resources_folder_path}" + "\n")
    
    def get_selected_domain(self, event=None):
        selected_indices = self.listbox_domains.curselection()
        if selected_indices:
            selected_item = self.listbox_domains.get(selected_indices[0])
            globals.selected_domain = selected_item.replace('--> ', '')
            print(f"Selected domain: {globals.selected_domain}")

    def on_close(self):
        index_path = self.main_folder_path / "db"  / "indexes" / (globals.selected_domain + ".pickle")
        try:
            index_object = self.indf.load_index(index_path=index_path)
            globals.index = faiss.deserialize_index(index_object["index"])
            globals.sentences = index_object["sentences"]
        except FileNotFoundError:
            messagebox.showerror("Error!", "Index could not be found with your domain!")
        self.destroy()

    def get_resources_folder_path(self):
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)
        return config[0]["db_path"]
