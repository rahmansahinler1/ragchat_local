from openai import OpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate,FewShotPromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

class ChatbotFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def _prompt_with_context_builder(self, query, context):

        examples = [
            {
             "query": "Can you explain how photosynthesis works in plants?",
             "context": "Photosynthesis is a process by which plants convert light energy into chemical energy. It occurs in the chloroplasts of plant cells, where light energy is used to convert carbon dioxide and water into glucose and oxygen.",
             "answer" : "Photosynthesis is the process by which plants use sunlight to convert water and carbon dioxide into glucose and oxygen. This process occurs in the chloroplasts and is essential for the production of energy in plants."
             },{
             "query": "How does blockchain technology ensure the security of transactions?",
             "context": "Blockchain technology uses a decentralized ledger to record transactions. Each transaction is grouped into blocks, which are cryptographically linked to the previous block, ensuring that they cannot be altered without changing all subsequent blocks.",
             "answer" : "Blockchain secures transactions by using a decentralized, immutable ledger where each block is linked to the previous one using cryptography. This makes it nearly impossible to alter any transaction without being detected."
             },{
            "query": "What were the key factors leading to the fall of the Roman Empire?",
            "context": "The Roman Empire's fall was influenced by various internal and external factors, including economic decline, military overextension, political instability, and invasions by barbarian tribes.",
             "answer" : "The fall of the Roman Empire was primarily caused by a combination of economic troubles, military losses to invading tribes, and political corruption. The division of the empire and the weakening of its military also played significant roles."
            } 
        ]
        
        example_template = """
                User: {query}
                Context: {context}
                AI: {answer}
            """

        example_prompt = PromptTemplate(
                input_variables = ["query","context","answer"],
                template = example_template
        )

        prefix = """
            You are an AI assistant skilled at generating generalized, accurate, and contextually relevant responses.
            Your goal is to assist users by providing clear and insightful answers to their questions.
            Do not rephrase the answer while giving the answer.
            Below are some examples of how to answer different types of questions.
            Use given context below to answer the question in a summarized fashion without using saying any word about the context.
        """

        suffix = """
            User: {query} 
            Context: {context}
            AI:
        """

        example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples = examples,
            embeddings = OpenAIEmbeddings(),
            vectorstore_cls= Chroma,
            k=2
        )

        few_shot_prompt = FewShotPromptTemplate(
                example_prompt = example_prompt,
               # examples = examples,
                example_selector=example_selector,
                prefix=prefix,
                suffix=suffix,
                input_variables = ["query","context"],
                example_separator = "\n"
            )
        
        template = """ 
        You are an AI assistant specialized in extracting specific information from provided text.
        Your task is to analyze the given context windows and extract relevant data based on the user's query.

        Instructions:
        
        You will be provided with 5 context windows, each containing 3 sentences.
        Carefully read all context windows.
        Analyze the user's query to understand what specific information they are looking for.
        Search for and extract the relevant information from the context windows.
        If the requested information is not present in any of the context windows, state that clearly.
        Present the extracted information in a clear and concise manner.
        If appropriate, provide brief context or explanation for the extracted data.
        Use given context below to answer the question in a summarized fashion.

        Respond in the following format:
                
        Extracted Information: [Provide the extracted data here]
        Confidence: [High/Medium/Low - based on how clearly the information was stated in the text]
        Additional Context: [If necessary, provide a brief explanation or context]

        Remember to focus solely on the information present in the provided context windows. Do not include external knowledge or make assumptions beyond what is explicitly stated.

        Context Windows:
        {context}

        Answer: {query}
                    """
        
        prompt = PromptTemplate(
                input_variables=["query","context"],
                template=template
        )

        return prompt.format(query=query,context=context)

    def response_generation(self, query, context):
        # Load chat model
        prompt = self._prompt_with_context_builder(query, context)
        
        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            temperature=0
        )

        # Extract response
        answer = response.choices[0].message.content.strip()
        return answer
