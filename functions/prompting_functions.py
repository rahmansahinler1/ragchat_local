import os
from dotenv import load_dotenv
from operator import itemgetter

# from langchain_community.vectorstores import DocArrayInMemorySearch
# from langchain_openai.embeddings import OpenAIEmbeddings
# from langchain_core.output_parsers import StrOutputParser
# from langchain.prompts import ChatPromptTemplate
import globals


class PromptingFunctions:
    def __init__(self):
        pass

    def generate_chain(self, vector_db, openai_model):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        retriever = vector_db.as_retriever()
        context_question_dict = {
            "context": itemgetter("question") | retriever,
            "question": itemgetter("question"),
        }
        chain = (
            context_question_dict
            | self._generate_prompt()
            | openai_model
            | self._generate_parser()
        )
        globals.chain = chain

    def _generate_prompt(self):
        prompt_template = """
        Give a brief answer to the question below based on the given context.
        Answer will be just one sentence.
        Answer of the question will just include the information asked in the question not the whole context.
        If you don't know the answer or don't have any information for the question, answer with "I don't know".

        Context: {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        return prompt

    def _generate_parser(self):
        parser = StrOutputParser()
        return parser
