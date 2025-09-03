from sqlalchemy.orm import Session
from typing import Dict
import uuid

from ..models import ChatResponse
from .singleton_services import get_embedding_service, get_vector_service
from .redis_service import RedisService
from .llm_service import LLMService
from .conversational_booking_service import ConversationalBookingService

class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.redis_service = RedisService()
        self.llm_service = LLMService()
        self.booking_service = ConversationalBookingService(db)
    
    async def process_query(self, query: str, session_id: str = None) -> ChatResponse:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # First, check if this is a booking request
        is_booking, booking_response, booking_result = await self.booking_service.process_booking_request(
            query, session_id
        )
        
        if is_booking:
            # Store booking conversation in chat history
            await self.redis_service.store_chat_history(session_id, query, booking_response)
            
            return ChatResponse(
                response=booking_response,
                session_id=session_id,
                sources=[],
                booking_result=booking_result
            )
        
        # Regular RAG processing for non-booking queries
        query_embedding = await self.embedding_service.generate_query_embedding(query)
        
        retrieved_docs = await self.vector_service.search_similar(
            query_embedding, 
            limit=5
        )
        
        chat_history = await self.redis_service.get_context_for_query(session_id)
        
        response = await self.llm_service.generate_response(
            query=query,
            context="",
            retrieved_docs=retrieved_docs,
            chat_history=chat_history
        )
        
        await self.redis_service.store_chat_history(session_id, query, response)
        
        sources = [doc["filename"] for doc in retrieved_docs if doc.get("filename")]
        unique_sources = list(set(sources))
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            sources=unique_sources
        )