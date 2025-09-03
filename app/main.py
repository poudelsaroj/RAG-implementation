from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db, create_tables
from .models import ChatMessage, ChatResponse, InterviewBooking, PartialInterviewBooking, ChunkingStrategy
from .services.document_service import DocumentService
from .services.rag_service import RAGService
from .services.interview_service import InterviewService

app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = Form(ChunkingStrategy.FIXED_SIZE),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    service = DocumentService(db)
    result = await service.process_document(file, chunking_strategy)
    
    return {
        "document_id": result["document_id"],
        "chunks_created": result["chunks_count"],
        "extracted_interviews": result.get("extracted_interviews", [])
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage, db: Session = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    
    service = RAGService(db)
    return await service.process_query(request.message, request.session_id)

@app.post("/book-interview")
async def book_interview(booking: PartialInterviewBooking, db: Session = Depends(get_db)):
    service = InterviewService(db)
    booking_data = booking.dict(exclude_none=True)
    result = await service.book_interview_with_cv_enhancement(booking_data)
    return result

@app.get("/interviews")
async def get_interviews(db: Session = Depends(get_db)):
    service = InterviewService(db)
    interviews = await service.get_all_interviews()
    return {"interviews": interviews}