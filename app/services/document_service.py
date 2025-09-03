from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Dict
import PyPDF2
import io

from ..models import Document, DocumentChunk, ChunkingStrategy
from .chunking_service import ChunkingService
from .singleton_services import get_embedding_service, get_vector_service
from .interview_extraction_service import InterviewExtractionService

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.chunking_service = ChunkingService()
        self.interview_extraction_service = InterviewExtractionService(db)
    
    async def process_document(
        self, 
        file: UploadFile, 
        chunking_strategy: ChunkingStrategy
    ) -> Dict:
        text_content = await self._extract_text(file)
        
        document = Document(
            filename=file.filename,
            file_type=file.content_type,
            chunking_strategy=chunking_strategy.value,
            text_content=text_content
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        chunks = await self.chunking_service.chunk_text(text_content, chunking_strategy)
        
        chunk_count = 0
        for i, chunk_text in enumerate(chunks):
            embedding = await self.embedding_service.generate_embedding(chunk_text)
            
            vector_id = await self.vector_service.store_embedding(
                embedding=embedding,
                text=chunk_text,
                metadata={
                    "document_id": document.id,
                    "chunk_index": i,
                    "filename": file.filename
                }
            )
            
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_text=chunk_text,
                chunk_index=i,
                vector_id=vector_id
            )
            
            self.db.add(chunk)
            chunk_count += 1
        
        self.db.commit()
        
        # Extract and book interviews automatically
        extracted_interviews = []
        try:
            extracted_interviews = await self.interview_extraction_service.extract_interview_requests(
                text_content, file.filename
            )
        except Exception as e:
            print(f"Interview extraction error: {e}")
        
        return {
            "document_id": document.id,
            "chunks_count": chunk_count,
            "extracted_interviews": extracted_interviews
        }
    
    async def _extract_text(self, file: UploadFile) -> str:
        content = await file.read()
        
        if file.content_type == "application/pdf":
            return self._extract_pdf_text(content)
        elif file.content_type == "text/plain":
            return content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file.content_type}")
    
    def _extract_pdf_text(self, content: bytes) -> str:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text