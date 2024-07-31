import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import globals


class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_vector_embeddings_from_pdf(self,batch_size=100):
        pdf_embeddings = []
        sentences = globals.pdf_sentences
        #for sentence in globals.pdf_sentences
        batches = [sentences[i:i+batch_size] for i in range(0,len(sentences),batch_size)]

        #embedding cümle başına ne kadar süre harcıyor
        #batch size'a göre bu süre nasıl değişiyor
        #avg embedding time per sentence when batch size = 500
        #avg indexing time per sentence when batch size = 500
        
        for batch in batches:
            sentence_embedding = self.client.embeddings.create(
                model="text-embedding-ada-002", input=batch
            )
            #[0] = 70 X 25'Lik
            pdf_embeddings.extend(sentence_embedding.data) #batchlerin sadece ilkini aldığı için hızlanıyor 

        globals.pdf_embeddings = np.array(
            [x.embedding for x in pdf_embeddings], float
        )

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)
