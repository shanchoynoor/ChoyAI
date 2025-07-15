"""
Vector Memory Manager using ChromaDB for semantic search

Provides vector-based memory storage and semantic similarity search
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    import numpy as np
    VECTOR_DEPS_AVAILABLE = True
except ImportError:
    VECTOR_DEPS_AVAILABLE = False

from app.config.settings import settings


class VectorMemoryManager:
    """Manages vector-based memory storage with semantic search capabilities"""
    
    def __init__(self, collection_name: str = "choyai_memories"):
        self.logger = logging.getLogger(__name__)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embeddings_model = None
        
        if not VECTOR_DEPS_AVAILABLE:
            self.logger.warning("Vector dependencies not available. Install chromadb and sentence-transformers")
            return
    
    async def initialize(self):
        """Initialize ChromaDB and embeddings model"""
        if not VECTOR_DEPS_AVAILABLE:
            self.logger.warning("Skipping vector memory initialization - dependencies not available")
            return False
            
        try:
            self.logger.info("🔮 Initializing Vector Memory Manager...")
            
            # Initialize ChromaDB client
            data_dir = settings.data_dir / "vector_db"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(data_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                self.logger.info(f"📚 Loaded existing collection: {self.collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "ChoyAI semantic memory storage"}
                )
                self.logger.info(f"📚 Created new collection: {self.collection_name}")
            
            # Initialize embeddings model
            await self._initialize_embeddings_model()
            
            self.logger.info("✅ Vector Memory Manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Vector Memory Manager: {e}")
            return False
    
    async def _initialize_embeddings_model(self):
        """Initialize the sentence transformer model"""
        try:
            # Use a lightweight but effective model
            model_name = "all-MiniLM-L6-v2"  # 384 dimensions, fast and good quality
            self.embeddings_model = SentenceTransformer(model_name)
            self.logger.info(f"🤖 Loaded embeddings model: {model_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load embeddings model: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embeddings_model:
            raise RuntimeError("Embeddings model not initialized")
        
        # Generate embedding
        embedding = self.embeddings_model.encode([text])
        return embedding[0].tolist()
    
    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        importance: int = 1
    ) -> str:
        """Add a memory with semantic embedding"""
        if not self.collection:
            raise RuntimeError("Vector memory not initialized")
        
        try:
            # Generate unique ID
            memory_id = f"{user_id}_{memory_type}_{uuid.uuid4().hex[:8]}"
            
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Prepare metadata
            memory_metadata = {
                "user_id": user_id,
                "memory_type": memory_type,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[memory_metadata],
                ids=[memory_id]
            )
            
            self.logger.debug(f"💾 Added vector memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add vector memory: {e}")
            raise
    
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search memories using semantic similarity"""
        if not self.collection:
            raise RuntimeError("Vector memory not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Prepare filters
            where_clause = {}
            if user_id:
                where_clause["user_id"] = user_id
            if memory_type:
                where_clause["memory_type"] = memory_type
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            memories = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity >= similarity_threshold:
                        memory = {
                            "id": results["ids"][0][i],
                            "content": doc,
                            "metadata": results["metadatas"][0][i],
                            "similarity": similarity,
                            "distance": distance
                        }
                        memories.append(memory)
            
            self.logger.debug(f"🔍 Found {len(memories)} similar memories for query: {query[:50]}...")
            return memories
            
        except Exception as e:
            self.logger.error(f"❌ Failed to search vector memories: {e}")
            return []
    
    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        if not self.collection:
            raise RuntimeError("Vector memory not initialized")
        
        try:
            where_clause = {"user_id": user_id}
            if memory_type:
                where_clause["memory_type"] = memory_type
            
            results = self.collection.get(
                where=where_clause,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    memory = {
                        "id": results["ids"][i],
                        "content": doc,
                        "metadata": results["metadatas"][i]
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get user memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        if not self.collection:
            raise RuntimeError("Vector memory not initialized")
        
        try:
            self.collection.delete(ids=[memory_id])
            self.logger.debug(f"🗑️ Deleted vector memory: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete vector memory: {e}")
            return False
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory"""
        if not self.collection:
            raise RuntimeError("Vector memory not initialized")
        
        try:
            # Get existing memory
            existing = self.collection.get(ids=[memory_id], include=["documents", "metadatas"])
            if not existing["documents"]:
                return False
            
            # Prepare updates
            new_content = content or existing["documents"][0]
            new_metadata = existing["metadatas"][0].copy()
            if metadata:
                new_metadata.update(metadata)
            new_metadata["updated_at"] = datetime.now().isoformat()
            
            # Generate new embedding if content changed
            new_embedding = None
            if content:
                new_embedding = self._generate_embedding(new_content)
            
            # Update in collection
            self.collection.update(
                ids=[memory_id],
                documents=[new_content],
                metadatas=[new_metadata],
                embeddings=[new_embedding] if new_embedding else None
            )
            
            self.logger.debug(f"📝 Updated vector memory: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update vector memory: {e}")
            return False
    
    async def get_similar_contexts(
        self,
        current_context: str,
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[str]:
        """Get similar conversation contexts for better AI responses"""
        memories = await self.search_memories(
            query=current_context,
            user_id=user_id,
            memory_type="conversation",
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Extract just the content for context injection
        contexts = [memory["content"] for memory in memories]
        return contexts
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        if not self.collection:
            return {"available": False}
        
        try:
            count = self.collection.count()
            return {
                "available": True,
                "total_memories": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to get collection stats: {e}")
            return {"available": False, "error": str(e)}
    
    async def close(self):
        """Clean up resources"""
        # ChromaDB handles cleanup automatically
        self.logger.info("🔮 Vector Memory Manager closed")


# Export the main class
__all__ = ["VectorMemoryManager"]
