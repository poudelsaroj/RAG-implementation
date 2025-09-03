import re
import google.generativeai as genai
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..config import settings
from .interview_service import InterviewService
from ..models import Document

class ConversationalBookingService:
    def __init__(self, db: Session):
        self.db = db
        self.interview_service = InterviewService(db)
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def process_booking_request(self, message: str, session_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process a chat message to detect and handle interview booking requests
        Returns: (is_booking_request, response_message, booking_result)
        """
        
        # First, check if this looks like a booking request
        if not self._is_booking_request(message):
            return False, "", None
        
        # Extract booking information using AI
        booking_info = await self._extract_booking_info(message)
        
        if not booking_info:
            return True, self._get_info_request_response(), None
        
        # Try to fill missing information from uploaded CV documents
        if booking_info:
            booking_info = await self._enhance_with_cv_data(booking_info)
        
        # Validate and complete booking information
        validation_result = self._validate_booking_info(booking_info)
        
        if not validation_result["valid"]:
            missing_info = validation_result["missing"]
            return True, self._get_missing_info_response(missing_info), None
        
        # Attempt to book the interview
        try:
            booking_result = await self.interview_service.book_interview_from_chat(booking_info)
            success_message = self._generate_booking_confirmation(booking_result)
            return True, success_message, booking_result
            
        except Exception as e:
            error_message = f"I apologize, but I encountered an error while booking your interview: {str(e)}. Please try again or contact support."
            return True, error_message, None
    
    def _is_booking_request(self, message: str) -> bool:
        """Check if the message contains interview booking intent"""
        
        booking_keywords = [
            'book', 'schedule', 'interview', 'appointment', 'meeting',
            'available', 'slot', 'time', 'date', 'when can', 'would like to',
            'interested in', 'apply', 'position', 'role', 'job'
        ]
        
        message_lower = message.lower()
        
        # Check for booking keywords
        has_booking_keywords = any(keyword in message_lower for keyword in booking_keywords)
        
        # Check for typical booking patterns
        booking_patterns = [
            r'i would like to\s+(?:book|schedule)',
            r'can (?:i|we)\s+(?:book|schedule)',
            r'(?:book|schedule)\s+(?:an|the)?\s*interview',
            r'available\s+(?:for|on)',
            r'interview\s+(?:on|at|for)',
            r'meet\s+(?:on|at)',
            r'my name is.*(?:interview|meeting|appointment)',
            r'(?:i am|i\'m)\s+(?:interested|available)'
        ]
        
        has_patterns = any(re.search(pattern, message_lower) for pattern in booking_patterns)
        
        return has_booking_keywords or has_patterns
    
    async def _extract_booking_info(self, message: str) -> Optional[Dict]:
        """Use AI to extract booking information from the message"""
        
        prompt = f"""
        Analyze this message for interview booking information. Extract any available details.
        Return ONLY a JSON object with these fields (use null for missing information):
        
        {{
            "name": "full name of person or null",
            "email": "email address or null", 
            "date": "date in YYYY-MM-DD format or null",
            "time": "time in HH:MM format or null",
            "intent": "booking/inquiry/other"
        }}
        
        Message: "{message}"
        
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
            
            return None
            
        except Exception as e:
            print(f"AI booking extraction error: {e}")
            return None
    
    def _validate_booking_info(self, booking_info: Dict) -> Dict:
        """Validate extracted booking information"""
        
        required_fields = ['name', 'email', 'date', 'time']
        missing = []
        
        for field in required_fields:
            if not booking_info.get(field):
                missing.append(field)
        
        # Validate email format if provided
        if booking_info.get('email'):
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
            if not re.match(email_pattern, booking_info['email']):
                missing.append('valid_email')
        
        return {
            "valid": len(missing) == 0,
            "missing": missing
        }
    
    def _get_info_request_response(self) -> str:
        """Response when booking intent is detected but no clear info is provided"""
        
        return """I'd be happy to help you book an interview! To schedule your interview, I'll need the following information:

📝 **Required Information:**
- Your full name
- Email address  
- Preferred date (YYYY-MM-DD format)
- Preferred time (HH:MM format)

Please provide these details and I'll book your interview right away.

**Example:** "I'd like to book an interview. My name is John Smith, email john@example.com, for January 25th, 2024 at 2:30 PM."""
    
    def _get_missing_info_response(self, missing: list) -> str:
        """Response when some booking information is missing"""
        
        missing_map = {
            'name': 'your full name',
            'email': 'your email address',
            'date': 'your preferred date (YYYY-MM-DD)',
            'time': 'your preferred time (HH:MM)',
            'valid_email': 'a valid email address'
        }
        
        missing_items = [missing_map.get(item, item) for item in missing]
        
        if len(missing_items) == 1:
            missing_text = missing_items[0]
        elif len(missing_items) == 2:
            missing_text = f"{missing_items[0]} and {missing_items[1]}"
        else:
            missing_text = ", ".join(missing_items[:-1]) + f", and {missing_items[-1]}"
        
        return f"""I have some of your information, but I still need {missing_text} to complete your interview booking.\n\nPlease provide the missing information and I'll schedule your interview immediately."""
    
    def _generate_booking_confirmation(self, booking_result: Dict) -> str:
        """Generate a confirmation message for successful booking"""
        
        details = booking_result.get('details', {})
        status = booking_result.get('status', 'unknown')
        
        if status == 'already_exists':
            return f"""Interview already scheduled:
Name: {details.get('name')}
Email: {details.get('email')}
Date: {details.get('date')}
Time: {details.get('time')}"""
        
        else:
            return f"""Interview booked successfully:
Name: {details.get('name')}
Email: {details.get('email')}
Date: {details.get('date')}
Time: {details.get('time')}
Booking ID: {booking_result.get('booking_id')}"""
    
    async def _enhance_with_cv_data(self, booking_info: Dict) -> Dict:
        """Enhance booking info with data from uploaded CV documents"""
        
        # Get the most recent uploaded document
        recent_doc = self.db.query(Document).order_by(Document.upload_time.desc()).first()
        
        if not recent_doc:
            return booking_info
        
        # Extract CV information from the document
        cv_data = await self._extract_cv_info_from_document(recent_doc.text_content)
        
        # Fill missing fields with CV data
        if not booking_info.get('name') and cv_data.get('name'):
            booking_info['name'] = cv_data['name']
        
        if not booking_info.get('email') and cv_data.get('email'):
            booking_info['email'] = cv_data['email']
        
        return booking_info
    
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