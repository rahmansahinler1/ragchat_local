import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()
        self.retriver = SentenceTransformer("deepset/all-mpnet-base-v2-table")

    def create_vector_embeddings_from_sentences(
            self,
            sentences: List[str],
            batch_size: int = 2000
        ):
        file_embeddings = []
        batches = [sentences[i:i+batch_size] for i in range(0,len(sentences), batch_size)]
        
        for batch in batches:
            sentence_embedding = self.client.embeddings.create(
                model="text-embedding-ada-002", input=batch
            )
            file_embeddings.extend(sentence_embedding.data)

        return np.array(
            [x.embedding for x in file_embeddings], float
        )

    def create_table_embeddings_from_file_tables(
      self,
      tables: List[str],
      batch_size: int = 64   
    ):
     table_embeddings = []
     batches =[tables[i:i+batch_size] for i in range(0,len(tables),batch_size)]

     for batch in batches:
        table_embeddings.extend(self.retriver.encode(batch).tolist())

     return np.array(table_embeddings,float)

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)

    def create_table_embeddings_from_query(self,query):
        query_embedding = self.retriver.encode(query).tolist()
        return np.array(query_embedding,float)
