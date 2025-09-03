from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import uuid
import numpy as np
from ..config import settings

class VectorService:
    def __init__(self):
        self.use_qdrant = True
        self.memory_storage = {}  # Fallback in-memory storage
        self.collection_name = "documents"
        
        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
            self._ensure_collection()
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant ({e}). Using in-memory storage.")
            self.use_qdrant = False
    
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
        except Exception as e:
            print(f"Error creating collection: {e}")
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def store_embedding(
        self, 
        embedding: List[float], 
        text: str, 
        metadata: Dict
    ) -> str:
        vector_id = str(uuid.uuid4())
        
        if self.use_qdrant:
            try:
                point = PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        "document_id": metadata.get("document_id"),
                        "chunk_index": metadata.get("chunk_index"),
                        "filename": metadata.get("filename")
                    }
                )
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            except Exception as e:
                print(f"Error storing in Qdrant, using memory: {e}")
                self.use_qdrant = False
        
        if not self.use_qdrant:
            # Store in memory as fallback
            self.memory_storage[vector_id] = {
                "vector": embedding,
                "text": text,
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index"),
                "filename": metadata.get("filename")
            }
        
        return vector_id
    
    async def search_similar(
        self, 
        query_embedding: List[float], 
        limit: int = 5
    ) -> List[Dict]:
        
        if self.use_qdrant:
            try:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit
                )
                
                results = []
                for result in search_results:
                    results.append({
                        "text": result.payload["text"],
                        "score": result.score,
                        "document_id": result.payload.get("document_id"),
                        "filename": result.payload.get("filename"),
                        "chunk_index": result.payload.get("chunk_index")
                    })
                
                return results
            except Exception as e:
                print(f"Error searching Qdrant, using memory: {e}")
                self.use_qdrant = False
        
        # Fallback to in-memory search
        results = []
        for vector_id, data in self.memory_storage.items():
            similarity = self._cosine_similarity(query_embedding, data["vector"])
            results.append({
                "text": data["text"],
                "score": similarity,
                "document_id": data.get("document_id"),
                "filename": data.get("filename"),
                "chunk_index": data.get("chunk_index")
            })
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]