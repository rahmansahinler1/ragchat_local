from tkinter import *
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
from tkcalendar import *
from PIL import Image, ImageTk
from typing import List
from pathlib import Path
import globals
from datetime import datetime


class Window(tk.Toplevel):
    def __init__(
            self,
            domain_folders: List[str],
            db_folder_path: Path,
            memory_file_path: Path,
            detector,
            processor
        ):
        super().__init__()
        self.domain_folders = domain_folders
        self.db_folder_path = db_folder_path
        self.memory_file_path = memory_file_path
        self.detector = detector
        self.processor = processor
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Base window
        self.geometry("640x720+100+100")
        self.title("App")
        self.resizable(False, False)
        self.configure(bg="#222222")
        self.title("settings")
        self.wm_iconbitmap("assets/ragchat_icon.ico")
        self.cal = Calendar(self, selectmode="day", foreground='white')
        # Button run file change detection
        self.run_file_change_image = Image.open("assets/run_file_detection.png")
        self.run_file_change_image = self.run_file_change_image.resize((38, 25), Image.LANCZOS)
        self.run_file_change_pic = ImageTk.PhotoImage(self.run_file_change_image)
        self.button_run_file_change = tk.Button(
            self,
            image=self.run_file_change_pic,
            command=lambda: [
                self.detect_changes(),
            ],
            bd=0,
            bg="#222222",
            highlightthickness=0,
            activebackground="#222222"
        )
        self.button_run_file_change.place(x=230, y=300, width=38, height=25)

        # Labels and images
        self.image_settings = Image.open("assets/settings.png")
        self.settings_pic = ImageTk.PhotoImage(self.image_settings)
        self.label_settings_pic = Label(self, image=self.settings_pic)
        self.label_settings_pic.image = self.settings_pic
        self.label_settings_pic.place(x=25, y=27, width=75, height=75)

        self.image_logs = Image.open("assets/logs.png")
        self.logs_pic = ImageTk.PhotoImage(self.image_logs)
        self.label_logs_pic = Label(self, image=self.logs_pic)
        self.label_logs_pic.image = self.logs_pic
        self.label_logs_pic.place(x=25, y=332, width=75, height=77)

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
        self.label_settings.place(x=105, y=43, width=175, height=45)

        self.label_logs = Label(self, text="logs")
        roboto_font = tkfont.Font(
            family="Roboto",
            size=30,
            weight="bold",
            slant="roman"
            )
        self.label_logs.config(
            font=roboto_font,
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_logs.place(x=105, y=340, width=175, height=45)

        self.label_select_folder = Label(self, text="Select Resource Folder")
        self.label_select_folder.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_select_folder.place(x=30, y=107, width=300, height=20)


        self.label_run_file_detection = Label(self, text="Run file detection")
        self.label_run_file_detection.config(
            font=("Helvetica", 16, "bold"),
            background="#222222",
            foreground="white",
            anchor="w",
        )
        self.label_run_file_detection.place(x=38, y=302, width=180, height=20)

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

        #Calendar
        self.cal.place(x=350, y=137, height=150)
        self.cal.lift()
        self.label_calendar = tk.Label(self, text="Date Selection", font=("Helvetica", 16, "bold"), bg="#222222", fg="white")
        self.label_date = tk.Label(self, text="", font=("Helvetica", 16, "bold"), bg="#222222", fg="white")
        self.label_date.place(x=380, y=330)
        self.label_calendar.place(x=340, y=107)

        # Chatbox
        self.chatbox_log = Text(self, wrap=WORD)
        self.chatbox_log.tag_configure("center", justify="center")
        self.chatbox_log.config(
            font=("Times New Roman", 11),
            fg="black",
            bg="white"
        )
        self.chatbox_log.place(x=30, y=407, width=580, height=283)
        self.chatbox_log.insert(tk.END, f"Resources folder path: {self.db_folder_path}" + "\n")
    
    def get_selected_domain(self, event=None):
        selected_indices = self.listbox_domains.curselection()
        if selected_indices:
            selected_item = self.listbox_domains.get(selected_indices[0])
            globals.selected_domain = selected_item.replace('--> ', '')
    
    def display_message(self, message: str):
        self.chatbox_log.update()
        self.chatbox_log.insert(tk.END, "- " + message + "\n")
        self.chatbox_log.update()
    
    def detect_changes(self):
        self.display_message(message="Checking the memory...",)
        changes, updated_memory = self.detector.check_changes()
        if any(changes.values()):
            changed_file_message = f"""Changed files detected!
            --> {len(changes["insert"])} addition
            --> {len(changes["update"])} update
            --> {len(changes["delete"])} deletion\nPlease wait ragchat to synchronize it's memory..."""
            self.display_message(message=changed_file_message)
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
            self.display_message(message="Memory updated!")
        else:
            self.display_message(message="Memory is sync.")

    def filter_date(self):
        selected_date = self.cal.get_date()
        today = datetime.today()
        if datetime.strptime(selected_date,"%m/%d/%y").date() >= today.date():
            return ""
        else:
            return selected_date

    def on_close(self):
        if globals.selected_domain:
            index_path = self.db_folder_path  / "indexes" / (globals.selected_domain + ".pickle")
            try:
                index_object = self.processor.indf.load_index(index_path=index_path)
                index_object_filtered = self.processor.index_filter(index_object,date = self.filter_date())
                globals.index_list.append(self.processor.create_index(embeddings=index_object_filtered["embeddings"]))
                globals.files = index_object_filtered["file_path"]
                globals.file_sentence_amount = index_object_filtered["file_sentence_amount"]
                globals.sentences = index_object_filtered["sentences"]
                globals.headers_dict = self.processor.header_extract_index(index_object_filtered)
            except FileNotFoundError:
                messagebox.showerror("Error!", "No file registered database under this domain. Please insert one and click <run file detection> or run the ragchat again!")
        else:
            messagebox.showinfo("Information", "You did not select any resource folder!")
        self.destroy()
