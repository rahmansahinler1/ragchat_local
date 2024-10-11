import PyPDF2
from docx import Document
import spacy
from pathlib import Path
from datetime import datetime
import os 
import fitz
import re

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
            "date": [],
            "is_header": [],
            "page_num": [],
            "block_num": [],
            "boost" : [],
        }
        # Open file
        path = Path(file_path)
        file_extension = path.suffix.lower()
        try:
            if file_extension == '.pdf':
                with fitz.open(path) as file:
                    try:
                        pdf_date = f"{file.metadata["creationDate"][4:6]}-{file.metadata["creationDate"][6:8]}-{file.metadata["creationDate"][9:11]}"
                        file_data["date"].append(pdf_date)
                        previous_sentence_count = 0
                    except TypeError as e:
                        raise TypeError(f"PDF creation date could not extracted!: {e}")
                    try: 
                        for page_num in range(len(file)):
                            page = file.load_page(page_num)
                            block_text = page.get_text("blocks")
                            blocks = page.get_text("dict")["blocks"]
                            text_blocks = [block for block in blocks if block["type"] == 0]
                            for i,block in enumerate(text_blocks):
                                if "lines" in block and len(block["lines"]) >= 1 and len(block["lines"]) < 5:
                                    for line in block["lines"]:
                                        for span in line["spans"]:
                                            text = span["text"]
                                            if span["size"] > 10 and (span["font"].find("Medi") >0 or span["font"].find("Bold") >0 or span["font"].find("B") >0) and len(text) > 3 and text[0].isupper():
                                                file_data["sentences"].append(text)
                                                file_data["is_header"].append(1)
                                                file_data["page_num"].append(page_num+1)
                                                file_data["block_num"].append(i)
                                                file_data["boost"].append(0)
                                            elif len(text) > 15 and self._header_regex_check(text=text) == None :
                                                file_data["sentences"].append(text)
                                                file_data["is_header"].append(0)
                                                file_data["page_num"].append(page_num+1)
                                                file_data["block_num"].append(i)
                                                file_data["boost"].append(0)
                                elif "lines" in block:
                                    for sent_num in range(len(block_text[i][4].split('. '))):
                                            sentence = re.split(r'(?<=[.!?])\s+', block_text[i][4])[sent_num].strip()
                                            clean_sentence = self._process_regex(sentence)
                                            if len(clean_sentence) > 15:
                                                file_data["sentences"].append(clean_sentence)
                                                file_data["is_header"].append(0)
                                                file_data["page_num"].append(page_num + 1)
                                                file_data["block_num"].append(i)
                                                file_data["boost"].append(0)
                            current_sentence_count = len(file_data["sentences"])
                            sentences_in_this_page = current_sentence_count - previous_sentence_count
                            file_data["page_sentence_amount"].append(sentences_in_this_page)
                            previous_sentence_count = current_sentence_count
                    except TypeError as e:
                        raise TypeError(f"PDF text could not extracted!: {e}")
            elif file_extension == '.docx':
                doc = Document(path)
                try:
                    doc_date = f"{doc.core_properties.created.year%2000}-{doc.core_properties.created.month}-{doc.core_properties.created.day}"
                    file_data["date"].append(doc_date)
                except TypeError as e:
                    raise TypeError(f"Doc creation date could not extracted!: {e}")
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
    
    def _process_regex(self,text):
        clean_text = re.sub(r'(\b\w+)\s*\n\s*(\w+\b)',r'\1 \2',text)
        clean_text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', clean_text)
        clean_text = re.sub(r'[,()]\s*\n\s*(\w+)',r' \1',clean_text)
        clean_text = re.sub(r'(\b\w+)\s*-\s*(\w+\b)',r'\1 \2',clean_text)
        clean_text = re.sub(r'(\w+)\s*[-–]\s*(\w+)',r'\1\2',clean_text)
        clean_text = re.sub(r'(?:[\s!\"#$%&\'()*+,\-.:;<=>?@\[\\\]^_`{|}~]+)(?!\w)',r' ',clean_text)
        clean_text = clean_text.replace('\n','')
        clean_text = clean_text.replace(' \n','')
        return clean_text
    
    def _header_regex_check(self,text):
        url_pattern = r"""
            (?:https?:\/\/)?                        # Optional protocol (http:// or https://)
            (?:[\w-]+\.)*                           # Optional subdomains
            [\w-]+                                  # Domain name
            (?:\.[a-zA-Z]{2,})                      # Top-level domain (.com, .org, etc)
            (?:\/[^\s]*)?                           # Optional path and query parameters
        """
        date_pattern = r"""
            (?P<date>
                \d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]) |     # ISO date
                (?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4} |     # USA date
                (?:0[1-9]|[12]\d|3[01])[./](?:0[1-9]|1[0-2])[./]\d{4} # European date
            )
        """
        number_pattern = r"""
            (?P<number>
                -?\d*\.?\d+[eE][+-]?\d+ |          # Scientific notation
                -?\d*\.\d+ |                       # Decimal numbers
                -?\d+ |                            # Integers
                \d+% |                             # Percentages
                [\$€£¥]\s*\d+(?:\.\d{2})? |        # Currency
                (?:\+?1?\s*\(?(?:\d{3})\)?[-.\s]?\d{3}[-.\s]?\d{4}) # Phone
            )
        """
        regex_pattern = re.compile(f"{url_pattern}|{number_pattern}|{date_pattern}", re.VERBOSE)
        result = re.search(regex_pattern,text)
        return result
    
    def _process_text(self, text, file_data):
       docs = self.nlp(text)
       sentences = [sent.text.replace('\n', ' ').strip() for sent in docs.sents]
       valid_sentences = [sentence for sentence in sentences if len(sentence) > 15]
       file_data["page_sentence_amount"].append(len(valid_sentences))
       file_data["sentences"].extend(valid_sentences)