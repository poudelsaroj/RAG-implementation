# RAG Implementation with CV-Enhanced Interview Booking

A complete Retrieval-Augmented Generation (RAG) system with intelligent CV-based interview booking capabilities.

## Live Demo

**Production API**: [https://interview-booking-rag-production.up.railway.app/docs](https://interview-booking-rag-production.up.railway.app/docs)

Try the live API with interactive documentation and test the CV-enhanced booking features.

## Features

### Core RAG Functionality
- **Document Upload & Processing**: Support for PDF and TXT files with dual chunking strategies
- **Vector Database Integration**: Qdrant with fallback to in-memory storage
- **Embedding Generation**: Google Gemini API for text embeddings
- **Conversational AI**: Multi-turn chat with context memory using Redis
- **Custom RAG Pipeline**: No external chains, built from scratch

### CV-Enhanced Interview Booking
- **Smart CV Parsing**: Upload any CV/resume and AI extracts candidate information automatically
- **Multiple Booking Methods**: 
  - **Natural Language**: "Book me an interview for him on March 15th at 2 PM"
  - **REST API**: `{"date": "2024-03-15", "time": "14:00"}` with auto-fill from CV
  - **Document-Based**: Direct extraction from uploaded documents
- **Intelligent Auto-Fill**: Missing booking details completed using uploaded CV data
- **Multi-Interface Support**: Chat, API, and document processing with CV enhancement
- **Persistent Storage**: All interviews saved with complete candidate information

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

## How CV-Enhanced Booking Works

### Step-by-Step Process

1. **Upload Candidate's CV/Resume**
   - Support for PDF and TXT formats
   - AI processes and extracts candidate information
   - Document stored for future reference

2. **Book Interview Using Multiple Methods**

   **Method 1: Natural Language Chat**
   ```
   "Book me an interview for him on April 15th at 2 PM"
   ```
   System automatically finds candidate name and email from uploaded CV

   **Method 2: Partial API Booking**
   ```json
   {"date": "2024-04-15", "time": "14:00"}
   ```
   Missing name/email auto-filled from CV data

   **Method 3: Complete API Booking**
   ```json
   {"name": "John Doe", "email": "john@example.com", "date": "2024-04-15", "time": "14:00"}
   ```
   Traditional booking with all details provided

3. **Automatic Interview Creation**
   - Complete booking record with all candidate details
   - Stored in database with timestamp and source tracking
   - Available via `/interviews` endpoint

### Smart Booking Features

- **AI-Powered**: Understands natural language booking requests
- **Auto-Complete**: Fills missing information from uploaded CVs
- **Multiple Sources**: Chat, API, or document-based booking
- **Persistent**: All bookings saved with full candidate information
- **Searchable**: Query candidate qualifications from uploaded documents

## System Architecture

```
CV Upload → AI Processing → Smart Booking
    ↓           ↓             ↓
/upload    Gemini API    Auto-Enhanced
endpoint   Extraction    Interview DB
```

## Production Deployment

### Live System on Railway
This project is deployed on Railway and accessible at:
**[https://interview-booking-rag-production.up.railway.app/docs](https://interview-booking-rag-production.up.railway.app/docs)**

### Railway Deployment Steps
1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push origin main
   ```

2. **Create Railway Service**
   - Go to [Railway.app](https://railway.app)
   - Connect your GitHub repository
   - Railway automatically detects Python project

3. **Set Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Deploy**
   - Railway automatically builds and deploys
   - Your API will be live with CV-enhanced booking features


### Production Notes

- System uses fallbacks for external services (Qdrant → Memory, Redis → Memory)
- SQLite database persists on Railway's disk storage
- For high-traffic, consider upgrading to PostgreSQL database

## Troubleshooting

- **CV Enhancement Not Working**: Ensure CV document was recently uploaded and contains readable text
- **API Validation Errors**: Check if server is using latest `PartialInterviewBooking` model
- **Qdrant Timeout**: System automatically falls back to in-memory vector storage
- **Redis Connection**: System falls back to in-memory chat storage

## API Documentation

Interactive API documentation available at:
- **Production**: [https://interview-booking-rag-production.up.railway.app/docs](https://interview-booking-rag-production.up.railway.app/docs)
- **Local**: `http://localhost:8000/docs`

### Live API Base URL
```
https://interview-booking-rag-production.up.railway.app
```

### Example Production Usage
```bash
# Upload CV to production
curl -X POST "https://interview-booking-rag-production.up.railway.app/upload" \
  -F "file=@resume.pdf" -F "chunking_strategy=fixed_size"

# Book interview with CV enhancement
curl -X POST "https://interview-booking-rag-production.up.railway.app/book-interview" \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-04-20", "time": "14:00"}'

# Chat with CV-enhanced booking
curl -X POST "https://interview-booking-rag-production.up.railway.app/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Book me an interview for him on April 25th at 2 PM"}'
```