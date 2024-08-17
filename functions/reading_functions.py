from tkinter import filedialog
from tkinter import *
from pathlib import Path
import globals
import PyPDF2
import spacy


class ReadingFunctions:
    def __init__(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            disable=[ "tagger", "attribute_ruler", "lemmatizer", "ner","textcat","custom "]
        )

    def read_pdf(self, pdf_path: str):
        pdf_data = {
            "page_sentence_amount": [],
            "sentences": []
        }
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            # Extract text from each page
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                docs = self.nlp(page_text)
                sentences = [sent.text.replace('\n', ' ').strip() for sent in docs.sents]
                valid_sentences = [sentence for sentence in sentences if len(sentence) > 15]
                pdf_data["page_sentence_amount"].append(len(valid_sentences))
                pdf_data["sentences"].extend(valid_sentences)  
        
        return pdf_data

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
