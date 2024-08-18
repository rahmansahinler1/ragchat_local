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
