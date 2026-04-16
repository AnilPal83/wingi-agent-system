import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in .env file.")
        self.client = OpenAI(api_key=self.api_key)

    def query(self, system_prompt: str, user_prompt: str, response_format="text"):
        """Queries the LLM and returns the response."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # You can change this to any model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"} if response_format == "json" else {"type": "text"}
            )
            content = response.choices[0].message.content
            return json.loads(content) if response_format == "json" else content
        except Exception as e:
            print(f"⚠️ LLM Error: {e}")
            return None