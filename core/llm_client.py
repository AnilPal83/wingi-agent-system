import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from dotenv import load_dotenv
from .logger import setup_logger

logger = setup_logger("LLM")
load_dotenv()

class LLMClient:
    def __init__(self):
        self.project_id = os.getenv("VERTEX_PROJECT_ID")
        self.location = os.getenv("VERTEX_LOCATION", "us-central1")
        
        if not self.project_id:
            logger.error("VERTEX_PROJECT_ID not found in .env file.")
            raise ValueError("❌ VERTEX_PROJECT_ID not found in .env file.")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # We use gemini-1.5-pro for better quota stability compared to 2.0-flash
        self.model_name = os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-pro")
        self.model = GenerativeModel(self.model_name)
        logger.info(f"Vertex AI initialized with model: {self.model_name}")

    def query(self, system_prompt: str, user_prompt: str, response_format="text"):
        """Queries the Vertex AI Gemini model and returns the response."""
        logger.info(f"Sending query to Vertex AI (Format: {response_format})")
        
        try:
            # Vertex AI uses System Instructions as a separate parameter
            model = GenerativeModel(
                self.model_name,
                system_instruction=[system_prompt]
            )
            
            config = GenerationConfig(
                response_mime_type="application/json" if response_format == "json" else "text/plain"
            )
            
            response = model.generate_content(
                user_prompt,
                generation_config=config
            )
            
            content = response.text
            logger.debug(f"Received Response (Truncated): {content[:100]}...")
            return json.loads(content) if response_format == "json" else content
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.error("🛑 QUOTA EXCEEDED (429): You have hit your Vertex AI rate limits.")
            else:
                logger.error(f"Vertex AI API Error: {str(e)}")
            return None