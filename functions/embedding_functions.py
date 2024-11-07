import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
import io

class EmbeddingFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

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

    def create_vector_embedding_from_query(self, query):
        query_embedding = self.client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        return np.array(query_embedding.data[0].embedding, float).reshape(1, -1)
    
    def create_image_embeddings_from_bytes(self, image_bytes: list):
        image_embeddings = []
        for image in image_bytes:
            process_ready_image = Image.open(io.BytesIO(image))
            inputs = self.processor(images=process_ready_image, return_tensors="pt", padding=True)
            image_features = self.model.get_image_features(**inputs)
            image_embeddings.extend(image_features.detach().numpy())

        return np.array(image_embeddings, float)
    
    def create_embedding_from_query_image(self, query):
        inputs = self.processor(text=query, return_tensors="pt", padding=True)
        text_features = self.model.get_text_features(**inputs)

        return np.array(text_features.detach().numpy(), float).reshape(1, -1)
