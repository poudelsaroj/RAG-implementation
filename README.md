# RAG System with Interview Booking

A production RAG (Retrieval-Augmented Generation) backend with document processing and conversational interview booking capabilities.

## Features

- **Document Processing**: Upload PDF/TXT files with configurable chunking strategies
- **RAG Implementation**: Custom retrieval-augmented generation with Gemini LLM
- **Vector Search**: Qdrant integration with in-memory fallback
- **Conversational Memory**: Redis-based chat history with session management
- **Interview Booking**: Multiple booking methods (chat, API, document extraction)
- **SQL Storage**: SQLAlchemy with SQLite for metadata persistence

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

### Interview Booking
```bash
POST /book-interview
Content-Type: application/json

{
  "name": "Full Name",
  "email": "email@example.com", 
  "date": "2024-01-15",
  "time": "14:30"
}
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

## Interview Booking Methods

1. **Conversational**: Natural language booking through chat
2. **REST API**: Direct programmatic booking
3. **Document Extraction**: Automatic extraction from uploaded documents

Interactive API documentation: `http://localhost:8000/docs`