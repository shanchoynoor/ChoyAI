"""
RAG (Retrieval-Augmented Generation) Engine

Implements vector-based context retrieval for enhanced AI responses
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    RAG_DEPS_AVAILABLE = True
except ImportError:
    RAG_DEPS_AVAILABLE = False

from app.modules.memory.vector_memory import VectorMemoryManager
from app.modules.memory.core_memory import CoreMemoryManager
from app.modules.memory.user_memory import UserMemoryManager
from app.config.settings import settings


class RAGEngine:
    """Retrieval-Augmented Generation engine for context-aware responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vector_memory = VectorMemoryManager(collection_name="choyai_rag")
        self.core_memory = CoreMemoryManager()
        self.user_memory = UserMemoryManager()
        self.text_splitter = None
        
        if not RAG_DEPS_AVAILABLE:
            self.logger.warning("RAG dependencies not available. Install langchain")
    
    async def initialize(self):
        """Initialize RAG engine components"""
        try:
            self.logger.info("🧠 Initializing RAG Engine...")
            
            # Initialize memory managers
            await self.vector_memory.initialize()
            await self.core_memory.initialize()
            await self.user_memory.initialize()
            
            # Initialize text splitter for document processing
            if RAG_DEPS_AVAILABLE:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
            
            self.logger.info("✅ RAG Engine initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize RAG Engine: {e}")
            return False
    
    async def index_conversation(
        self,
        user_id: str,
        conversation_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Index a conversation for later retrieval"""
        try:
            # Split conversation into chunks if too long
            chunks = self._split_text(conversation_text)
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": datetime.now().isoformat(),
                    **(metadata or {})
                }
                
                await self.vector_memory.add_memory(
                    user_id=user_id,
                    content=chunk,
                    memory_type="conversation_rag",
                    metadata=chunk_metadata,
                    importance=2
                )
            
            self.logger.debug(f"📚 Indexed conversation for user {user_id}: {len(chunks)} chunks")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to index conversation: {e}")
            return False
    
    async def index_knowledge_document(
        self,
        content: str,
        doc_id: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Index a knowledge document for global retrieval"""
        try:
            # Split document into chunks
            chunks = self._split_text(content)
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "doc_id": doc_id,
                    "title": title or doc_id,
                    "source": source or "unknown",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": datetime.now().isoformat(),
                    **(metadata or {})
                }
                
                await self.vector_memory.add_memory(
                    user_id="global",  # Global knowledge
                    content=chunk,
                    memory_type="knowledge",
                    metadata=chunk_metadata,
                    importance=3
                )
            
            self.logger.info(f"📖 Indexed knowledge document: {doc_id} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to index knowledge document: {e}")
            return False
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for indexing"""
        if not self.text_splitter:
            # Fallback simple splitting
            words = text.split()
            chunks = []
            chunk_size = 200  # words
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append(chunk)
            
            return chunks
        
        # Use LangChain text splitter
        return self.text_splitter.split_text(text)
    
    async def retrieve_context(
        self,
        query: str,
        user_id: str,
        context_types: List[str] = None,
        max_context_length: int = 2000
    ) -> Dict[str, Any]:
        """Retrieve relevant context for a query"""
        try:
            context_types = context_types or ["conversation_rag", "knowledge", "core_facts", "user_memory"]
            
            retrieved_context = {
                "query": query,
                "user_id": user_id,
                "contexts": {},
                "total_chunks": 0,
                "relevance_scores": {}
            }
            
            total_length = 0
            
            # 1. Retrieve conversation context
            if "conversation_rag" in context_types and total_length < max_context_length:
                conv_contexts = await self.vector_memory.search_memories(
                    query=query,
                    user_id=user_id,
                    memory_type="conversation_rag",
                    limit=5,
                    similarity_threshold=0.3
                )
                
                if conv_contexts:
                    context_text = self._format_contexts(conv_contexts, max_context_length - total_length)
                    retrieved_context["contexts"]["conversation"] = context_text
                    retrieved_context["relevance_scores"]["conversation"] = [c["similarity"] for c in conv_contexts]
                    total_length += len(context_text)
            
            # 2. Retrieve global knowledge
            if "knowledge" in context_types and total_length < max_context_length:
                knowledge_contexts = await self.vector_memory.search_memories(
                    query=query,
                    user_id="global",
                    memory_type="knowledge",
                    limit=3,
                    similarity_threshold=0.4
                )
                
                if knowledge_contexts:
                    context_text = self._format_contexts(knowledge_contexts, max_context_length - total_length)
                    retrieved_context["contexts"]["knowledge"] = context_text
                    retrieved_context["relevance_scores"]["knowledge"] = [c["similarity"] for c in knowledge_contexts]
                    total_length += len(context_text)
            
            # 3. Retrieve core memory facts
            if "core_facts" in context_types and total_length < max_context_length:
                core_facts = await self._get_relevant_core_facts(query)
                if core_facts:
                    retrieved_context["contexts"]["core_facts"] = core_facts[:max_context_length - total_length]
                    total_length += len(core_facts)
            
            # 4. Retrieve user memory
            if "user_memory" in context_types and total_length < max_context_length:
                user_memories = await self._get_relevant_user_memories(user_id, query)
                if user_memories:
                    retrieved_context["contexts"]["user_memory"] = user_memories[:max_context_length - total_length]
                    total_length += len(user_memories)
            
            retrieved_context["total_chunks"] = sum(len(contexts) for contexts in retrieved_context["contexts"].values() if isinstance(contexts, list))
            
            self.logger.debug(f"🔍 Retrieved context for query: {query[:50]}... ({total_length} chars)")
            return retrieved_context
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve context: {e}")
            return {"query": query, "user_id": user_id, "contexts": {}, "error": str(e)}
    
    def _format_contexts(self, contexts: List[Dict[str, Any]], max_length: int) -> str:
        """Format retrieved contexts into readable text"""
        formatted_parts = []
        current_length = 0
        
        for context in contexts:
            content = context["content"]
            similarity = context.get("similarity", 0)
            
            # Add similarity score and content
            formatted = f"[Relevance: {similarity:.2f}] {content}"
            
            if current_length + len(formatted) <= max_length:
                formatted_parts.append(formatted)
                current_length += len(formatted)
            else:
                # Add truncated version
                remaining = max_length - current_length
                if remaining > 50:  # Only add if meaningful space left
                    truncated = formatted[:remaining-3] + "..."
                    formatted_parts.append(truncated)
                break
        
        return "\n\n".join(formatted_parts)
    
    async def _get_relevant_core_facts(self, query: str) -> str:
        """Get relevant core facts for the query"""
        try:
            # Get all core facts and filter relevant ones
            core_facts = await self.core_memory.get_core_facts()
            relevant_facts = []
            
            # Simple keyword matching for core facts
            query_words = set(query.lower().split())
            
            for category, facts in core_facts.items():
                for fact in facts:
                    fact_words = set(fact["content"].lower().split())
                    if query_words.intersection(fact_words):
                        relevant_facts.append(f"{category}: {fact['content']}")
            
            return "\n".join(relevant_facts[:5])  # Limit to top 5
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get relevant core facts: {e}")
            return ""
    
    async def _get_relevant_user_memories(self, user_id: str, query: str) -> str:
        """Get relevant user memories for the query"""
        try:
            # Get recent user memories
            memories = await self.user_memory.get_user_memories(user_id, limit=20)
            relevant_memories = []
            
            # Simple keyword matching for user memories
            query_words = set(query.lower().split())
            
            for memory in memories:
                content = memory.get("content", "")
                memory_words = set(content.lower().split())
                if query_words.intersection(memory_words):
                    relevant_memories.append(content)
            
            return "\n".join(relevant_memories[:3])  # Limit to top 3
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get relevant user memories: {e}")
            return ""
    
    async def enhance_prompt_with_context(
        self,
        original_prompt: str,
        user_id: str,
        context_types: List[str] = None,
        max_context_length: int = 1500
    ) -> Tuple[str, Dict[str, Any]]:
        """Enhance a prompt with retrieved context"""
        try:
            # Retrieve relevant context
            context_data = await self.retrieve_context(
                query=original_prompt,
                user_id=user_id,
                context_types=context_types,
                max_context_length=max_context_length
            )
            
            # Build enhanced prompt
            enhanced_parts = []
            
            # Add context sections if available
            contexts = context_data.get("contexts", {})
            
            if contexts.get("core_facts"):
                enhanced_parts.append(f"<core_knowledge>\n{contexts['core_facts']}\n</core_knowledge>")
            
            if contexts.get("user_memory"):
                enhanced_parts.append(f"<user_context>\n{contexts['user_memory']}\n</user_context>")
            
            if contexts.get("conversation"):
                enhanced_parts.append(f"<conversation_history>\n{contexts['conversation']}\n</conversation_history>")
            
            if contexts.get("knowledge"):
                enhanced_parts.append(f"<relevant_knowledge>\n{contexts['knowledge']}\n</relevant_knowledge>")
            
            # Add original prompt
            enhanced_parts.append(f"<current_query>\n{original_prompt}\n</current_query>")
            
            enhanced_prompt = "\n\n".join(enhanced_parts)
            
            self.logger.debug(f"📝 Enhanced prompt with {len(contexts)} context types")
            return enhanced_prompt, context_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to enhance prompt: {e}")
            return original_prompt, {"error": str(e)}
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG engine statistics"""
        try:
            vector_stats = await self.vector_memory.get_collection_stats()
            
            return {
                "vector_memory": vector_stats,
                "rag_available": RAG_DEPS_AVAILABLE,
                "text_splitter_available": self.text_splitter is not None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get RAG stats: {e}")
            return {"error": str(e)}


# Export the main class
__all__ = ["RAGEngine"]
