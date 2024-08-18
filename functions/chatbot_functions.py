from openai import OpenAI
from dotenv import load_dotenv


class ChatbotFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def _prompt_with_context_builder(self, query, context):
        prompt = f"""You are an AI assistant specialized in extracting specific information from provided text.
        Your task is to analyze the given context windows and extract relevant data based on the user's query.

        Instructions:
        1. You will be provided with 5 context windows, each containing 3 sentences.
        2. Carefully read all context windows.
        3. Analyze the user's query to understand what specific information they are looking for.
        4. Search for and extract the relevant information from the context windows.
        5. If the requested information is not present in any of the context windows, state that clearly.
        6. Present the extracted information in a clear and concise manner.
        7. If appropriate, provide brief context or explanation for the extracted data.

        Respond in the following format:
        - Extracted Information: [Provide the extracted data here]
        - Confidence: [High/Medium/Low - based on how clearly the information was stated in the text]

        Remember to focus solely on the information present in the provided context windows. Do not include external knowledge or make assumptions beyond what is explicitly stated.

        Context Windows:
        {context}

        User Query: {query}
        """
        return prompt

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
