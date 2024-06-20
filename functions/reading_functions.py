from langchain_community.document_loaders import PyPDFLoader
from tkinter import filedialog
import tkinter as tk
from tkinter import *
import globals


class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, path: str):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        loader = PyPDFLoader(
            file_path=path + "/20230923_ELECO_Data-Driven-PHEV-Model.pdf"
        )
        pages = loader.load_and_split()
        globals.pdf_pages = pages

    def select_pdf_folder(self, label: Label):
        """
        The code is responsible for selecting a folder containing PDF files.
        """
        pdf_path = filedialog.askdirectory(title="Select the pdf folder")
        # Writing folder names into text boxes
        if pdf_path:
            label.config(text="Selected Folder: " + pdf_path)
            globals.input_folder = pdf_path
        else:
            raise Exception("No folder selected")
