import requests

def test_system():
    base_url = "http://localhost:8000"
    
    print("Testing RAG System...")
    
    # Test conversational booking
    booking_request = {
        "message": "Book interview for John Doe, john@test.com, 2024-01-30 at 15:00",
        "session_id": "test"
    }
    
    response = requests.post(f"{base_url}/chat", json=booking_request, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"Chat booking: {'OK' if result.get('booking_result') else 'FAIL'}")
    
    # Test API booking
    api_booking = {
        "name": "API User",
        "email": "api@test.com",
        "date": "2024-02-10", 
        "time": "16:00"
    }
    
    response = requests.post(f"{base_url}/book-interview", json=api_booking, timeout=10)
    if response.status_code == 200:
        print("API booking: OK")
    
    # Test interviews list
    response = requests.get(f"{base_url}/interviews", timeout=10)
    if response.status_code == 200:
        interviews = response.json().get('interviews', [])
        print(f"Total interviews: {len(interviews)}")
    
    print("Tests completed")

if __name__ == "__main__":
    test_system()