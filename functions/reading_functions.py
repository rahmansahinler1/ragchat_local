from tkinter import filedialog
from tkinter import *
from pathlib import Path
import globals
import PyPDF2


class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, pdf_path: str):
        # Open the PDF file
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

            # Extract text from each page
            for page_num in range(num_pages):
                text = reader.pages[page_num].extract_text()
                text = text.replace("\n", "")
                sentences = text.split(".")
                for sentence in sentences:
                    if len(sentence) > 15:
                        globals.pdf_sentences.append(sentence)

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
