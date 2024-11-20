import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import List


class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_vector_embeddings_from_sentences(
            self,
            sentences: List[str],
            batch_size: int = 2000
        ):
        file_embeddings = []
        batches = [sentences[i:i+batch_size] for i in range(0,len(sentences), batch_size)]
        
        for batch in batches:
            sentence_embedding = self.client.embeddings.create(
                model="text-embedding-3-small", input=batch
            )
            file_embeddings.extend(sentence_embedding.data)

        embeddings = np.array([x.embedding for x in file_embeddings], float)
        normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1)[:, np.newaxis]
        
        return normalized_embeddings

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-3-small", input=query
        )
        embedding = np.array(query_embedding.data[0].embedding, float).reshape(1, -1)
        normalized_embedding = embedding / np.linalg.norm(embedding, axis=1)[:, np.newaxis]

        return normalized_embedding