import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .logger import setup_logger

logger = setup_logger("LLM")
load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in .env file.")
            raise ValueError("❌ GOOGLE_API_KEY not found in .env file.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("Gemini 1.5 Pro client initialized.")

    def query(self, system_prompt: str, user_prompt: str, response_format="text"):
        """Queries the Gemini LLM and returns the response."""
        logger.info(f"Sending query to Gemini (Format: {response_format})")
        logger.debug(f"User Prompt (Truncated): {user_prompt[:100]}...")
        
        try:
            combined_prompt = f"SYSTEM INSTRUCTION:\n{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
            
            generation_config = {}
            if response_format == "json":
                generation_config = {"response_mime_type": "application/json"}
            
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config
            )
            
            content = response.text
            logger.debug(f"Received Response (Truncated): {content[:100]}...")
            return json.loads(content) if response_format == "json" else content
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return None