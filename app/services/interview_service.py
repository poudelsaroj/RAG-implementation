from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel
import google.generativeai as genai

from ..models import Interview, InterviewBooking, Document
from ..config import settings

class ExtractedInterview(BaseModel):
    name: str
    email: str
    date: str
    time: str
    context: str = ""

class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def book_interview(self, booking: InterviewBooking) -> Dict:
        interview = Interview(
            name=booking.name,
            email=booking.email,
            date=booking.date,
            time=booking.time
        )
        
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        
        return {
            "booking_id": interview.id,
            "details": {
                "name": interview.name,
                "email": interview.email,
                "date": interview.date,
                "time": interview.time,
                "created_at": interview.created_at.isoformat()
            }
        }
    
    async def book_interview_with_cv_enhancement(self, booking_data: Dict) -> Dict:
        """Book interview with CV data enhancement for missing fields"""
        
        # Enhance with CV data if available
        enhanced_data = await self._enhance_with_cv_data(booking_data)
        
        # Validate required fields
        required_fields = ['name', 'email', 'date', 'time']
        missing = []
        
        for field in required_fields:
            if not enhanced_data.get(field):
                missing.append(field)
        
        if missing:
            return {
                "error": "Missing required information",
                "missing_fields": missing,
                "message": f"Please provide: {', '.join(missing)}"
            }
        
        # Create InterviewBooking object and book
        from ..models import InterviewBooking
        booking = InterviewBooking(
            name=enhanced_data['name'],
            email=enhanced_data['email'], 
            date=enhanced_data['date'],
            time=enhanced_data['time']
        )
        
        return await self.book_interview(booking)
    
    async def _enhance_with_cv_data(self, booking_data: Dict) -> Dict:
        """Enhance booking data with CV information from uploaded documents"""
        
        # Get the most recent uploaded document
        recent_doc = self.db.query(Document).order_by(Document.upload_time.desc()).first()
        
        if not recent_doc:
            return booking_data
        
        # Extract CV information from the document
        cv_data = await self._extract_cv_info_from_document(recent_doc.text_content)
        
        # Fill missing fields with CV data
        enhanced_data = booking_data.copy()
        
        if not enhanced_data.get('name') and cv_data.get('name'):
            enhanced_data['name'] = cv_data['name']
        
        if not enhanced_data.get('email') and cv_data.get('email'):
            enhanced_data['email'] = cv_data['email']
        
        return enhanced_data
    
    async def _extract_cv_info_from_document(self, document_text: str) -> Dict:
        """Extract name and email from CV document using AI"""
        
        prompt = f"""
        Extract personal information from this CV/resume document.
        Return ONLY a JSON object with these fields (use null for missing information):
        
        {{
            "name": "full name or null",
            "email": "email address or null"
        }}
        
        Document text: "{document_text[:2000]}..."
        
        JSON:
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                import json
                json_text = response_text[start:end]
                return json.loads(json_text)
            
            return {}
            
        except Exception as e:
            print(f"CV extraction error: {e}")
            return {}
    
    async def get_all_interviews(self) -> List[Dict]:
        interviews = self.db.query(Interview).all()
        
        return [
            {
                "id": interview.id,
                "name": interview.name,
                "email": interview.email,
                "date": interview.date,
                "time": interview.time,
                "created_at": interview.created_at.isoformat()
            }
            for interview in interviews
        ]
    
    async def get_interview_by_id(self, interview_id: int) -> Dict:
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        
        if not interview:
            raise ValueError("Interview not found")
        
        return {
            "id": interview.id,
            "name": interview.name,
            "email": interview.email,
            "date": interview.date,
            "time": interview.time,
            "created_at": interview.created_at.isoformat()
        }
    
    async def book_interview_from_extraction(self, extracted_data: Dict, source_filename: str) -> Dict:
        """Book interview from extracted document data"""
        
        # Check if interview already exists for this email and date
        existing = self.db.query(Interview).filter(
            Interview.email == extracted_data['email'],
            Interview.date == extracted_data['date']
        ).first()
        
        if existing:
            return {
                "booking_id": existing.id,
                "status": "already_exists",
                "details": {
                    "name": existing.name,
                    "email": existing.email,
                    "date": existing.date,
                    "time": existing.time,
                    "source": "document_extraction",
                    "filename": source_filename
                }
            }
        
        # Create new interview
        interview = Interview(
            name=extracted_data['name'],
            email=extracted_data['email'],
            date=extracted_data['date'],
            time=extracted_data['time']
        )
        
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        
        return {
            "booking_id": interview.id,
            "status": "newly_booked",
            "details": {
                "name": interview.name,
                "email": interview.email,
                "date": interview.date,
                "time": interview.time,
                "source": "document_extraction",
                "filename": source_filename,
                "context": extracted_data.get('context', ''),
                "created_at": interview.created_at.isoformat()
            }
        }
    
    async def book_interview_from_chat(self, chat_data: Dict) -> Dict:
        """Book interview from chat conversation data"""
        
        # Check if interview already exists for this email and date
        existing = self.db.query(Interview).filter(
            Interview.email == chat_data['email'],
            Interview.date == chat_data['date']
        ).first()
        
        if existing:
            return {
                "booking_id": existing.id,
                "status": "already_exists",
                "details": {
                    "name": existing.name,
                    "email": existing.email,
                    "date": existing.date,
                    "time": existing.time,
                    "source": "chat_booking",
                    "created_at": existing.created_at.isoformat()
                }
            }
        
        # Create new interview
        interview = Interview(
            name=chat_data['name'],
            email=chat_data['email'],
            date=chat_data['date'],
            time=chat_data['time']
        )
        
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        
        return {
            "booking_id": interview.id,
            "status": "newly_booked",
            "details": {
                "name": interview.name,
                "email": interview.email,
                "date": interview.date,
                "time": interview.time,
                "source": "chat_booking",
                "created_at": interview.created_at.isoformat()
            }
        }