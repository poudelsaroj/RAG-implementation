import google.generativeai as genai
from typing import List
from ..config import settings

class EmbeddingService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
    
    async def generate_embedding(self, text: str) -> List[float]:
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"Error generating query embedding: {str(e)}")