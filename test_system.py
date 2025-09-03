import requests
import time

def test_system():
    base_url = "http://localhost:8000"
    
    print("Testing RAG System...")
    
    # Wait for server to be ready
    time.sleep(2)
    
    # Test chat booking
    try:
        chat_response = requests.post(f"{base_url}/chat", json={
            "message": "Book me an interview for tomorrow at 2 PM",
            "session_id": "test_session"
        }, timeout=10)
        
        if chat_response.status_code == 200:
            print("Chat booking: OK")
        else:
            print("Chat booking: FAIL")
    except Exception as e:
        print("Chat booking: FAIL")
    
    # Test API booking
    try:
        api_response = requests.post(f"{base_url}/book-interview", json={
            "name": "API User",
            "email": "api@test.com",
            "date": "2024-02-10",
            "time": "16:00"
        }, timeout=10)
        
        if api_response.status_code == 200:
            print("API booking: OK")
        else:
            print("API booking: FAIL")
    except Exception as e:
        print("API booking: FAIL")
    
    # Check total interviews
    try:
        interviews_response = requests.get(f"{base_url}/interviews", timeout=10)
        if interviews_response.status_code == 200:
            interviews = interviews_response.json().get('interviews', [])
            print(f"Total interviews: {len(interviews)}")
        else:
            print("Total interviews: ERROR")
    except Exception as e:
        print("Total interviews: ERROR")
    
    print("Tests completed")

if __name__ == "__main__":
    test_system()