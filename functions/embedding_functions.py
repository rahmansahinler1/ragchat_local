import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import globals


class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_vector_embeddings_from_pages(self):
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

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)
