import PyPDF2
from docx import Document
import spacy
from pathlib import Path
from datetime import datetime
import os 
import fitz
import re
import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter

class ReadingFunctions:
    def __init__(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            disable=[ "tagger", "attribute_ruler", "lemmatizer", "ner","textcat","custom "]
        )
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4")
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(self.headers_to_split_on,strip_headers=False,return_each_line=True)
    def read_file(self, file_path: str):
        file_data = {
            "page_sentence_amount": [],
            "sentences": [],
            "date": [],
            "is_header": [],
            "page_num": [],
            "file_header" : [],
            "is_table" : [],
        }
        # Open file
        path = Path(file_path)
        file_extension = path.suffix.lower()
        try:
            if file_extension == '.pdf':
                markdown_pages = pymupdf4llm.to_markdown(path, page_chunks=True)
                with fitz.open(path) as file:
                    try:
                        pdf_date = f"{file.metadata["creationDate"][4:6]}-{file.metadata["creationDate"][6:8]}-{file.metadata["creationDate"][9:11]}"
                        file_data["date"].append(pdf_date)
                        previous_sentence_count = 0
                    except TypeError as e:
                        raise TypeError(f"PDF creation date could not extracted!: {e}")
                    try: 
                        for i,page in enumerate(markdown_pages):
                            splits = self.markdown_splitter.split_text(page['text'])
                            for split in splits:
                                if not len(split.page_content) > 5 or re.match(r'^[^\w]*$',split.page_content) or re.match(r'E\/ECE\/(?:\d+|TRANS)\/Rev\.\d+\/Add\.\d+\/Rev\.\d+',split.page_content):
                                    continue
                                elif split.metadata and split.page_content[0] == '#' : #header
                                    file_data['sentences'].append(split.page_content)
                                    file_data['is_header'].append(1)
                                    file_data['is_table'].append(0)
                                    file_data['page_num'].append(i+1)
                                elif split.page_content[0] == '|' and split.page_content[-1] == '|': #table
                                    file_data['sentences'].append(split.page_content)
                                    file_data['is_header'].append(0)
                                    file_data['is_table'].append(1)
                                    file_data['page_num'].append(i+1)
                                else:
                                    file_data['sentences'].append(split.page_content)
                                    file_data['is_header'].append(0)
                                    file_data['is_table'].append(0)
                                    file_data['page_num'].append(i+1)
                            current_sentence_count = len(file_data["sentences"])
                            sentences_in_this_page = current_sentence_count - previous_sentence_count
                            file_data["page_sentence_amount"].append(sentences_in_this_page)
                            previous_sentence_count = current_sentence_count
                    except TypeError as e:
                        raise TypeError(f"PDF info could not extracted!: {e}")
            elif file_extension == '.docx':
                doc = Document(path)
                try:
                    previous_sentence_count = 0
                    doc_date = f"{doc.core_properties.created.year%2000}-{doc.core_properties.created.month}-{doc.core_properties.created.day}"
                    file_data["date"].append(doc_date)
                except TypeError as e:
                    raise TypeError(f"Doc creation date could not extracted!: {e}")
                finally:
                    file_data["date"].append('')
                    try:
                        for para in doc.paragraphs:
                            if para.style.name.startswith('Heading') or para.style.name.startswith('Title'):
                                file_data["sentences"].append(para.text)
                                file_data["is_header"].append(1)
                                file_data["is_table"].append(0)
                            elif len(para.text) > 15:
                                file_data["sentences"].append(para.text)
                                file_data["is_header"].append(0)
                                file_data["is_table"].append(0)
                        current_sentence_count = len(file_data["sentences"])
                        sentences_in_this_page = current_sentence_count - previous_sentence_count
                        file_data["page_sentence_amount"].append(sentences_in_this_page)
                        previous_sentence_count = current_sentence_count
                    except TypeError as e:
                            raise TypeError(f"PDF text could not extracted!: {e}")
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
        punct_pattern = r"\b[A-Z0-9]+(?:\/[A-Z0-9]+)+(?:\.[A-Z0-9]+)?\b"
        regex_pattern = re.compile(f"{punct_pattern}", re.VERBOSE)
        result = re.search(regex_pattern,text)
        return result

    def _process_text(self, text, file_data):
       docs = self.nlp(text)
       sentences = [sent.text.replace('\n', ' ').strip() for sent in docs.sents]
       valid_sentences = [sentence for sentence in sentences if len(sentence) > 15]
       file_data["page_sentence_amount"].append(len(valid_sentences))
       file_data["sentences"].extend(valid_sentences)

        # Extract files first page header  
    def _extract_file_header(self, file_path, file_data):
        path = Path(file_path)
        file_extension = path.suffix.lower()
        full_text = ''
        try:
            if file_extension == '.pdf':
                doc = fitz.open(path)
                page = doc.load_page(0)
                blocks = page.get_text("dict")["blocks"]
                text_blocks = [block for block in blocks if block["type"] == 0]
                for block in text_blocks:
                    if "lines" in block and len(block["lines"]) >= 1 and len(block["lines"]) < 4:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"]
                                if span["size"] > 3 and (span["font"].find("Medi") >0 or span["font"].find("Bold") >0 or span["font"].find("B") >0) and len(text) > 3:
                                    full_text += text + ' '
                file_data["file_header"].append(full_text)
            elif file_extension == '.docx':
                doc = Document(path)
                for para in doc.paragraphs:
                    if para.style.name.startswith('Heading'):
                        full_text += text + ' '
                file_data["file_header"].append(full_text)
        except Exception as e:
            print(f"Error reading file: {path}. Error: {str(e)}")
    
    # Table extraction from pdfs
    def _extract_pdf_tables(self,page,file_data,tables):
        blocks = page.get_text("blocks")
        blocks_dict = page.get_text("dict")["blocks"]
        text_blocks = [block for block in blocks_dict if block["type"] == 0]
        table_texts = self._extract_table_text(tabs=tables)
        table_bboxes = [(tab.bbox[0], tab.bbox[1], tab.bbox[2], tab.bbox[3]) for tab in tables.tables]
        counter = 0
        for i,block in enumerate(blocks):
            match_index,check = self._table_bbox_checker(block=block,bboxes=table_bboxes)
            if check == 1 and counter == 0:
                file_data["sentences"].append(table_texts[match_index])
                file_data["is_header"].append(0)
                file_data["page_num"].append(int(page.number)+1)
                file_data["block_num"].append(i)
                file_data["is_table"].append(1)
                counter += 1
            elif check == 1 and counter > 0 and i == len(blocks)-1:
                file_data["is_table"][-2] = 1
            elif check == 1 and counter > 0:
                continue
            elif check == 0 and counter > 0:
                file_data["is_table"][-2] = 1
                counter = 0
                if "lines" in text_blocks[i] and len(text_blocks[i]["lines"]) >= 1 and len(text_blocks[i]["lines"]) < 3 and len(text_blocks[i]["lines"][0]["spans"]) < 2:
                    for line in text_blocks[i]["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            if span["size"] > 3 and (span["font"].find("Medi") >0 or span["font"].find("Bold") >0 or span["font"].find("B") >0) and len(text) > 3 and text[0].isalpha() and self._header_regex_check(text) == None:
                                file_data["sentences"].append(text)
                                file_data["is_header"].append(1)
                                file_data["page_num"].append(int(page.number)+1)
                                file_data["block_num"].append(i)
                                file_data["is_table"].append(0)
                            elif len(text) >= 5 and re.search(r'^[^\w\s]+$|^[_]+$',text) == None and re.search(r'\d+(?:\.\d+)+\.',text) == None:
                                file_data["sentences"].append(text)
                                file_data["is_header"].append(0)
                                file_data["page_num"].append(int(page.number)+1)
                                file_data["block_num"].append(i)
                                file_data["is_table"].append(0)
                elif "lines" in text_blocks[i]:
                    for sent_num in range(len(block[4].split('. '))):
                        sentence = re.split(r'(?<=[.!?])\s+', block[4])[sent_num].strip()
                        clean_sentence = self._process_regex(sentence)
                        if len(clean_sentence) > 15:
                            file_data["sentences"].append(clean_sentence)
                            file_data["is_header"].append(0)
                            file_data["page_num"].append(int(page.number)+1)
                            file_data["block_num"].append(i)
                            file_data["is_table"].append(0)
            else:
                if "lines" in text_blocks[i] and len(text_blocks[i]["lines"]) >= 1 and len(text_blocks[i]["lines"]) < 3 and len(text_blocks[i]["lines"][0]["spans"]) < 2:
                    for line in text_blocks[i]["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            if span["size"] > 3 and (span["font"].find("Medi") >0 or span["font"].find("Bold") >0 or span["font"].find("B") >0) and len(text) > 3 and text[0].isalpha() and self._header_regex_check(text) == None:
                                file_data["sentences"].append(text)
                                file_data["is_header"].append(1)
                                file_data["page_num"].append(int(page.number)+1)
                                file_data["block_num"].append(i)
                                file_data["is_table"].append(0)
                            elif len(text) >= 5 and re.search(r'^[^\w\s]+$|^[_]+$',text) == None and re.search(r'\d+(?:\.\d+)+\.',text) == None:
                                file_data["sentences"].append(text)
                                file_data["is_header"].append(0)
                                file_data["page_num"].append(int(page.number)+1)
                                file_data["block_num"].append(i)
                                file_data["is_table"].append(0)
                elif "lines" in text_blocks[i]:
                    for sent_num in range(len(block[4].split('. '))):
                        sentence = re.split(r'(?<=[.!?])\s+', block[4])[sent_num].strip()
                        clean_sentence = self._process_regex(sentence)
                        if len(clean_sentence) > 15:
                            file_data["sentences"].append(clean_sentence)
                            file_data["is_header"].append(0)
                            file_data["page_num"].append(int(page.number)+1)
                            file_data["block_num"].append(i)
                            file_data["is_table"].append(0)

    def _extract_table_text(self,tabs):
        table_list =  []
        for table in tabs.tables:
            reconsracted_table = ""
            table_extract = table.extract()
            for sublist in table_extract:
                filtered = [str(item).replace('\n', ' ').strip() for item in sublist if item is not None]
                filtered = [re.sub(r'(?<!\w)([A-Za-z])\s+(\d+)(?!\w)', r'\1\2', item) for item in filtered]
                combined_string = ' '.join(filtered) + '\n'
                reconsracted_table += combined_string
            table_list.append(reconsracted_table)
        return table_list
    
    def _table_bbox_checker(self,block,bboxes):
        for j, table_bbox in enumerate(bboxes):
            if table_bbox[1] <= block[1] <= table_bbox[3] and table_bbox[0] <= block[0] <= table_bbox[2]:
                return j, 1
        return -1, 0
