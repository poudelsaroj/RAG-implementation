from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from enum import Enum

Base = declarative_base()

class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    chunking_strategy = Column(String, nullable=False)
    text_content = Column(Text, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    vector_id = Column(String, nullable=False)

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentUpload(BaseModel):
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class InterviewBooking(BaseModel):
    name: str
    email: EmailStr
    date: str
    time: str

class PartialInterviewBooking(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    
    class Config:
        extra = "forbid"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []
    booking_result: Optional[Dict] = None