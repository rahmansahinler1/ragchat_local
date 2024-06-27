from langchain_community.document_loaders import PyPDFLoader
from tkinter import filedialog
import tkinter as tk
from tkinter import *
import globals


class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, pdf_path: str):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        loader = PyPDFLoader(file_path=pdf_path)
        pages = loader.load_and_split()
        globals.pdf_pages = pages

    def select_pdf_file(self, label: Label):
        """
        The code is responsible for selecting a folder containing PDF files.
        """
        pdf_path = filedialog.askopenfilename(title="Select PDF File")
        if pdf_path:
            label.config(text="Selected PDF: " + pdf_path.split("/")[-1])
            globals.pdf_path = pdf_path
        else:
            raise Exception("No file selected")
