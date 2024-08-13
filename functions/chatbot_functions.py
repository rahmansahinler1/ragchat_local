from openai import OpenAI
from dotenv import load_dotenv


class ChatbotFunctions:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def _prompt_with_context_builder(self, query, context):
        prompt = (
            f"""
            
            You are an AI assistant skilled at generating detailed, accurate, and contextually relevant responses.
            Your goal is to assist users by providing clear and insightful answers to their questions.
            Below are some examples of how to answer different types of questions.”

            Example 1:

            User: “How does photosynthesis work?”

            AI: “Photosynthesis is a process used by plants, algae, and certain bacteria to convert light energy into chemical energy. 
            In this process, chlorophyll in the chloroplasts captures light energy, which is then used to convert carbon dioxide from the air and water from the soil into glucose and oxygen.
            The glucose provides energy for the plant, while the oxygen is released into the atmosphere as a byproduct. 
            Photosynthesis can be summarized by the equation: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.”

            Use given context below to answer question accordingly.

            """
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
