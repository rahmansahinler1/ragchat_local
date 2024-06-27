import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from langchain_community.vectorstores import DocArrayInMemorySearch
import globals


class MemoryFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_embeddings_from_pages(self):
        pdf_embeddings = []
        for page in globals.pdf_pages:
            page_sentences = page.page_content.split(".")
            for sentence in page_sentences:
                if len(sentence) > 5:
                    sentence_embedding = self.client.embeddings.create(
                        model="text-embedding-ada-002", input=sentence
                    )
                    pdf_embeddings.append(sentence_embedding)
        globals.pdf_embeddings = np.array(
            [x.data[0].embedding for x in pdf_embeddings], float
        )
