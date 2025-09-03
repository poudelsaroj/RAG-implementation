import google.generativeai as genai
from typing import List, Dict
from ..config import settings

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate_response(
        self, 
        query: str, 
        context: str, 
        retrieved_docs: List[Dict],
        chat_history: str = ""
    ) -> str:
        prompt = self._build_prompt(query, context, retrieved_docs, chat_history)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
    
    def _build_prompt(
        self, 
        query: str, 
        context: str, 
        retrieved_docs: List[Dict],
        chat_history: str
    ) -> str:
        docs_context = ""
        for i, doc in enumerate(retrieved_docs, 1):
            docs_context += f"Document {i}:\n{doc['text']}\n\n"
        
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided context and documents.

Chat History:
{chat_history}

Retrieved Documents:
{docs_context}

User Query: {query}

Instructions:
- Answer the user's query using the information from the retrieved documents
- If the information is not available in the documents, say so clearly
- Be conversational and helpful
- Take into account the chat history for context
- If the user is asking about interview booking, help them with that process

Answer:"""
        
        return prompt