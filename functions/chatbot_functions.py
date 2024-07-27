from openai import OpenAI
from dotenv import load_dotenv
import globals


class ChatbotFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def _prompt_with_context_builder(self, query, context):
        prompt = (
            f"Answer the question based on the context below.\n"
            f"Context: {context}\n"
            f"Question: {query}\n"
        )
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
