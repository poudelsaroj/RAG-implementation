# RAG Implementation with CV-Enhanced Interview Booking

A complete Retrieval-Augmented Generation (RAG) system with intelligent CV-based interview booking capabilities.

## Features

### Core RAG Functionality
- **Document Upload & Processing**: Support for PDF and TXT files with dual chunking strategies
- **Vector Database Integration**: Qdrant with fallback to in-memory storage
- **Embedding Generation**: Google Gemini API for text embeddings
- **Conversational AI**: Multi-turn chat with context memory using Redis
- **Custom RAG Pipeline**: No external chains, built from scratch

### CV-Enhanced Interview Booking 
- **Automatic CV Parsing**: AI-powered extraction of candidate information from uploaded documents
- **Smart Booking**: Automatically fill missing interview details from CV data
- **Multiple Interfaces**: Both REST API and chat-based booking with CV enhancement
- **Natural Language Processing**: "Book me an interview for him" - extracts name/email from CV
- **Data Persistence**: SQLite database for interview storage

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# Start Redis (optional)
docker run -d -p 6379:6379 redis:alpine

# Start server
python start_server.py
```

Server runs on `http://localhost:8000`

## API Endpoints

### Document Upload
```bash
POST /upload
Content-Type: multipart/form-data

file: PDF or TXT file
chunking_strategy: "fixed_size" or "semantic"
```

### Chat Interface
```bash
POST /chat
Content-Type: application/json

{
  "message": "Your question or booking request",
  "session_id": "optional-session-id"
}
```

### Interview Booking (CV-Enhanced)
```bash
POST /book-interview
Content-Type: application/json

# Complete booking
{
  "name": "Full Name",
  "email": "email@example.com", 
  "date": "2024-01-15",
  "time": "14:30"
}

# Partial booking (CV auto-fill)
{
  "date": "2024-01-15",
  "time": "14:30"
}
# System automatically extracts name/email from uploaded CV
```

### Get Interviews
```bash
GET /interviews
```

## Configuration

Environment variables (`.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
QDRANT_API_KEY=optional_qdrant_key
QDRANT_URL=optional_qdrant_url
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./app.db
```

## Testing

```bash
# Run system tests
python test_system.py
```

## Architecture

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM and database management
- **Qdrant** - Vector database (with fallback)
- **Redis** - Session storage (with fallback)
- **Gemini API** - LLM and embeddings
- **PyPDF2** - PDF processing

## CV-Enhanced Interview Booking Flow

### Complete Workflow Example

1. **Upload CV Document**
   ```bash
   curl -X POST "http://localhost:8000/upload" \
     -F "file=@candidate_resume.pdf" \
     -F "chunking_strategy=fixed_size"
   ```

2. **Book Interview with Minimal Data**
   ```bash
   # Via API (system auto-fills name/email from CV)
   curl -X POST "http://localhost:8000/book-interview" \
     -H "Content-Type: application/json" \
     -d '{"date": "2024-04-15", "time": "14:00"}'

   # Via Chat
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Book me an interview for him on April 15th at 2 PM"}'
   ```

3. **Result**: System extracts candidate name and email from uploaded CV and creates complete booking

## Interview Booking Methods

1. **CV-Enhanced Chat**: "Book me an interview for him" - AI extracts info from uploaded CV
2. **CV-Enhanced API**: Partial booking data auto-completed with CV information  
3. **Traditional API**: Complete booking with all required fields
4. **Document Extraction**: Automatic interview scheduling from document content

## System Architecture

```
CV Upload → AI Processing → Smart Booking
    ↓           ↓             ↓
/upload    Gemini API    Auto-Enhanced
endpoint   Extraction    Interview DB
```

## Troubleshooting

- **CV Enhancement Not Working**: Ensure CV document was recently uploaded and contains readable text
- **API Validation Errors**: Check if server is using latest `PartialInterviewBooking` model
- **Qdrant Timeout**: System automatically falls back to in-memory vector storage
- **Redis Connection**: System falls back to in-memory chat storage

Interactive API documentation: `http://localhost:8000/docs`