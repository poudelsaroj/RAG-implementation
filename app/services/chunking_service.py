from typing import List
import re
from ..models import ChunkingStrategy

class ChunkingService:
    
    @staticmethod
    async def chunk_text(text: str, strategy: ChunkingStrategy) -> List[str]:
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return ChunkingService._fixed_size_chunking(text)
        elif strategy == ChunkingStrategy.SEMANTIC:
            return ChunkingService._semantic_chunking(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    @staticmethod
    def _fixed_size_chunking(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period != -1 and last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    @staticmethod
    def _semantic_chunking(text: str) -> List[str]:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        max_chunk_size = 1500
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) < max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        if not chunks:
            return ChunkingService._fixed_size_chunking(text)
        
        return chunks