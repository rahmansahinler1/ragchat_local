from langchain_community.document_loaders import PyPDFLoader
import PyPDF2
from tkinter import filedialog
from tkinter import *
import globals


class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, pdf_path: str):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
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
