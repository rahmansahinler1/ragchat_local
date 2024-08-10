import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import globals


class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_vector_embeddings_from_pdf(self, batch_size=100):
        pdf_embeddings = []
        sentences = globals.pdf_sentences
        batches = [sentences[i:i+batch_size] for i in range(0,len(sentences), batch_size)]
        
        for batch in batches:
            sentence_embedding = self.client.embeddings.create(
                model="text-embedding-ada-002", input=batch
            )
            pdf_embeddings.extend(sentence_embedding.data)

        globals.pdf_embeddings = np.array(
            [x.embedding for x in pdf_embeddings], float
        )

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)
