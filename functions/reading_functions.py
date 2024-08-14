from tkinter import filedialog
from tkinter import *
from pathlib import Path
import globals
import fitz
import spacy

nlp = spacy.load("en_core_web_sm",disable=[ "tagger", "attribute_ruler", "lemmatizer", "ner","textcat","custom "]) #Initialize spaCy model

class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, pdf_path: str):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        # Open the PDF file
        pdf = fitz.open(pdf_path)
        sentences = []
        page_texts = []

        # Extract text from each page
        for page in range(pdf.page_count):
            page = pdf.load_page(page)
            page_texts.append(page.get_text())

        # Append extract text to a single list 
        full_text = ' '.join(page_texts)

        #Create text splitting with spaCy
        docs = nlp(full_text)

        #Create sentences from the input text,strip white space and replace \n with space
        page_sentences = [sent.text.replace('\n',' ').strip() for sent in docs.sents]

        #Append created sentences to the list
        sentences.extend(page_sentences)

        #Sorting sentences according to length
        sorted_sentences = sorted(sentences,key=len)

        #Removing sentences that are shorter than 15
        i=0
        while i<len(sorted_sentences):
            if len(sorted_sentences[i]) < 15:
                sorted_sentences.pop(i)
            else:
                break
        #Adding the sentences to global variable
        globals.pdf_sentences.extend(sorted_sentences)

    def select_pdf_file(self):
        """
        The code is responsible for selecting a folder containing PDF files.
        """
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
