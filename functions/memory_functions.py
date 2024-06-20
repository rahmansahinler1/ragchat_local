import os
from dotenv import load_dotenv
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_openai.embeddings import OpenAIEmbeddings
import globals


class MemoryFunctions:
    def __init__(self):
        pass

    def create_vector_db_in_memory(self, pages: list):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        embeddings = self._create_embeddings()
        vector_db = DocArrayInMemorySearch.from_documents(pages, embeddings)
        globals.vector_db = vector_db

    def _create_embeddings(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(
            openai_api_key=api_key, model="text-embedding-ada-002"
        )
        return embeddings
