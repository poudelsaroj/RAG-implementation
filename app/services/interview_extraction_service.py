import re
import google.generativeai as genai
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Interview
from .interview_service import InterviewService

class InterviewExtractionService:
    def __init__(self, db: Session):
        self.db = db
        self.interview_service = InterviewService(db)
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def extract_interview_requests(self, text_content: str, filename: str) -> List[Dict]:
        """Extract interview booking requests from document text"""
        
        # Use Gemini AI to extract interview information
        interview_data = await self._extract_with_ai(text_content)
        
        # Also use regex patterns as fallback
        regex_data = self._extract_with_regex(text_content)
        
        # Combine and validate results
        extracted_interviews = []
        
        if interview_data:
            extracted_interviews.extend(interview_data)
        
        if regex_data and not interview_data:  # Use regex as fallback
            extracted_interviews.extend(regex_data)
        
        # Process and book interviews
        booked_interviews = []
        for interview in extracted_interviews:
            if self._validate_interview_data(interview):
                try:
                    booking_result = await self.interview_service.book_interview_from_extraction(
                        interview, filename
                    )
                    booked_interviews.append(booking_result)
                except Exception as e:
                    print(f"Error booking interview: {e}")
        
        return booked_interviews
    
    async def _extract_with_ai(self, text_content: str) -> List[Dict]:
        """Use Gemini AI to extract interview information"""
        
        prompt = f"""
        Analyze the following document text and extract any interview booking requests or scheduling information.
        Look for:
        1. Names of people requesting interviews
        2. Email addresses
        3. Dates (in various formats)
        4. Times
        5. Interview requests or scheduling language
        
        Return ONLY valid JSON array format. If no interview information found, return empty array [].
        
        Example format:
        [
            {{
                "name": "John Doe",
                "email": "john@example.com",
                "date": "2024-01-25",
                "time": "14:30",
                "context": "brief context from document"
            }}
        ]
        
        Document text:
        {text_content}
        
        JSON Response:
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                import json
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            
            return []
            
        except Exception as e:
            print(f"AI extraction error: {e}")
            return []
    
    def _extract_with_regex(self, text_content: str) -> List[Dict]:
        """Fallback regex-based extraction"""
        
        interviews = []
        text_lower = text_content.lower()
        
        # Look for interview-related keywords
        interview_keywords = [
            'interview', 'schedule', 'appointment', 'meeting', 
            'available', 'book', 'slot', 'time'
        ]
        
        has_interview_context = any(keyword in text_lower for keyword in interview_keywords)
        
        if not has_interview_context:
            return []
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        
        # Extract names (common patterns)
        name_patterns = [
            r'(?:Name|Contact|From):\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)(?:\s+(?:would like|requests|wants))',
            r'(?:I am|My name is)\s+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        names = []
        for pattern in name_patterns:
            names.extend(re.findall(pattern, text_content))
        
        # Extract dates (various formats)
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*)?\d{4})'
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text_content, re.IGNORECASE))
        
        # Extract times
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}:\d{2})',
            r'(\d{1,2}\s*(?:AM|PM|am|pm))'
        ]
        
        times = []
        for pattern in time_patterns:
            times.extend(re.findall(pattern, text_content))
        
        # Combine extracted information
        if emails and (names or dates or times):
            interview = {
                "name": names[0] if names else "Unknown",
                "email": emails[0],
                "date": self._normalize_date(dates[0]) if dates else self._get_default_date(),
                "time": self._normalize_time(times[0]) if times else "10:00",
                "context": "Extracted from document content"
            }
            interviews.append(interview)
        
        return interviews
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        try:
            # Handle various date formats
            import dateutil.parser
            parsed_date = dateutil.parser.parse(date_str)
            return parsed_date.strftime("%Y-%m-%d")
        except:
            return self._get_default_date()
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time to HH:MM format"""
        try:
            import dateutil.parser
            parsed_time = dateutil.parser.parse(time_str)
            return parsed_time.strftime("%H:%M")
        except:
            return "10:00"
    
    def _get_default_date(self) -> str:
        """Get default date (next business day)"""
        today = datetime.now()
        next_day = today + timedelta(days=1)
        # Skip weekend
        while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
            next_day += timedelta(days=1)
        return next_day.strftime("%Y-%m-%d")
    
    def _validate_interview_data(self, interview: Dict) -> bool:
        """Validate extracted interview data"""
        required_fields = ['name', 'email', 'date', 'time']
        
        for field in required_fields:
            if field not in interview or not interview[field]:
                return False
        
        # Validate email format
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        if not re.match(email_pattern, interview['email']):
            return False
        
        return True