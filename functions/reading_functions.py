from tkinter import filedialog
from tkinter import *
from pathlib import Path
from typing import List
import globals
import PyPDF2


class ReadingFunctions:
    def read_pdf(self, pdf_path: str):
        # Open the PDF file
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

            # Extract text from each page
            pdf_sentences = []
            for page_num in range(num_pages):
                text = reader.pages[page_num].extract_text()
                text = text.replace("\n", "")
                sentences = text.split(".")
                for sentence in sentences:
                    if len(sentence) > 15:
                        pdf_sentences.append(sentence)
            return pdf_sentences

    def select_pdf_file(self):
        initial_dir = Path(__file__).resolve().parent.parent / "docs"
        pdf_path = filedialog.askopenfilename(
            title="Select PDF File",
            initialdir=initial_dir,
            filetypes=(
                ("PDF files", "*.pdf"),
                ("Text files", "*.txt"),
            )
        )
        if pdf_path:
            globals.pdf_path = pdf_path
        else:
            raise Exception("No file selected")
