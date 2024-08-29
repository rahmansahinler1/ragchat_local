import PyPDF2
from docx import Document
import spacy
from pathlib import Path
from datetime import datetime
import os 


class ReadingFunctions:
    def __init__(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            disable=[ "tagger", "attribute_ruler", "lemmatizer", "ner","textcat","custom "]
        )

    def read_file(self, file_path: str):
        file_data = {
            "page_sentence_amount": [],
            "sentences": [],
            "date" : []
        }
        # Open file
        path = Path(file_path)
        file_extension = path.suffix.lower()
        try:
            if file_extension == '.pdf':
                with path.open('rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pdf_date = datetime.date(pdf_reader.metadata.creation_date).strftime("%Y-%m-%d")
                    file_data["date"].append(pdf_date)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        self._process_text(page_text, file_data)
            
            elif file_extension == '.docx':
                doc = Document(path)
                doc_date = datetime.date(doc.core_properties.created).strftime("%Y-%m-%d")
                file_data["date"].append(doc_date)
                for para in doc.paragraphs:
                    self._process_text(para.text, file_data)
            
            elif file_extension in ['.txt', '.rtf']:
                txt_date = os.path.getctime(path)
                file_data["date"].append(txt_date)
                text = path.read_text(encoding='utf-8')
                self._process_text(text, file_data)
            
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        
        except PyPDF2.errors.PdfReadError:
            print(f"Error reading PDF file: {path}. The file might be corrupted or incompatible.")
        except Exception as e:
            print(f"Error reading file: {path}. Error: {str(e)}")
    
        return file_data

    def _process_text(self, text, file_data):
        docs = self.nlp(text)
        sentences = [sent.text.replace('\n', ' ').strip() for sent in docs.sents]
        valid_sentences = [sentence for sentence in sentences if len(sentence) > 15]
        file_data["page_sentence_amount"].append(len(valid_sentences))
        file_data["sentences"].extend(valid_sentences)