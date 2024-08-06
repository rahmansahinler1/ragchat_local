import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import globals
import time 

class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def create_vector_embeddings_from_pdf(self,batch_size=500):
        pdf_embeddings = []
        total_time = 0
        globals.batch_size = batch_size
        sentences = globals.pdf_sentences
        #for sentence in globals.pdf_sentences
        batches = [sentences[i:i+batch_size] for i in range(0,len(sentences),batch_size)]
        
        start_time = time.time()
        for batch in batches:
            sentence_embedding = self.client.embeddings.create(
                model="text-embedding-ada-002", input=batch
            )
        end_time = time.time()
        total_time = end_time-start_time

        pdf_embeddings.extend(sentence_embedding.data) 

        globals.kpi_dict["total_time"] = total_time #
        globals.sentence_number = len(pdf_embeddings)
        globals.avg_emd_time = total_time/len(pdf_embeddings)

        
        globals.pdf_embeddings = np.array(
            [x.embedding for x in pdf_embeddings], float
        )
        #self.avg_embedding_time_per_sentence = round(total_time/len(pdf_embeddings),4)
        #self.total_time_of_embedding = round(total_time,2) 
    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)