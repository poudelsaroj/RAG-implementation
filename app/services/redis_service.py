import redis
import json
from typing import List, Dict, Optional
from ..config import settings

class RedisService:
    def __init__(self):
        self.use_redis = True
        self.memory_storage = {}  # Fallback in-memory storage
        
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Warning: Could not connect to Redis ({e}). Using in-memory storage.")
            self.use_redis = False
    
    async def store_chat_history(self, session_id: str, message: str, response: str):
        key = f"chat_session:{session_id}"
        chat_entry = {
            "message": message,
            "response": response,
            "timestamp": self._get_current_timestamp()
        }
        
        if self.use_redis:
            try:
                self.redis_client.lpush(key, json.dumps(chat_entry))
                self.redis_client.expire(key, 3600)  # 1 hour expiration
            except Exception as e:
                print(f"Error storing to Redis, using memory: {e}")
                self.use_redis = False
        
        if not self.use_redis:
            # Store in memory as fallback
            if key not in self.memory_storage:
                self.memory_storage[key] = []
            self.memory_storage[key].insert(0, chat_entry)
            # Keep only last 50 messages per session
            self.memory_storage[key] = self.memory_storage[key][:50]
    
    async def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        key = f"chat_session:{session_id}"
        
        if self.use_redis:
            try:
                history = self.redis_client.lrange(key, 0, limit - 1)
                return [json.loads(entry) for entry in history]
            except Exception as e:
                print(f"Error getting from Redis, using memory: {e}")
                self.use_redis = False
        
        # Fallback to memory
        return self.memory_storage.get(key, [])[:limit]
    
    async def get_context_for_query(self, session_id: str) -> str:
        history = await self.get_chat_history(session_id, limit=5)
        
        context = ""
        for entry in reversed(history):  # Reverse to get chronological order
            context += f"User: {entry['message']}\nAssistant: {entry['response']}\n\n"
        
        return context
    
    def _get_current_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()