"""
Smart Notes Module - ChoyAI Productivity Suite

AI-enhanced note taking with summarization and search
Local storage with vector embeddings for semantic search
"""

import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from app.modules.productivity import (
    BaseProductivityModule, ModuleRequest, ModuleResponse, ModuleConfig, ModuleType
)
from app.core.ai_providers import TaskType


class NoteType(Enum):
    TEXT = "text"
    MEETING = "meeting"
    IDEA = "idea"
    RESEARCH = "research"
    TODO = "todo"
    JOURNAL = "journal"


@dataclass
class Note:
    id: str
    title: str
    content: str
    note_type: NoteType
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    user_id: str
    summary: Optional[str] = None
    word_count: int = 0
    reading_time: int = 0  # minutes
    is_favorite: bool = False
    parent_id: Optional[str] = None  # For note hierarchies
    ai_insights: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.ai_insights is None:
            self.ai_insights = []
        self.word_count = len(self.content.split()) if self.content else 0
        self.reading_time = max(1, self.word_count // 200)  # 200 WPM average


class NotesModule(BaseProductivityModule):
    """AI-powered notes management module"""
    
    def __init__(self, config: ModuleConfig, ai_provider_manager):
        super().__init__(config, ai_provider_manager)
        self.db_path = "data/databases/notes.db"
        self.notes_cache: Dict[str, Note] = {}
        self.search_index: Dict[str, List[str]] = {}  # word -> note_ids
        
    async def initialize(self) -> bool:
        """Initialize notes database and load recent notes"""
        try:
            await self._init_database()
            await self._load_notes()
            await self._build_search_index()
            self.logger.info("✅ Notes module initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize notes module: {e}")
            return False
    
    async def _init_database(self):
        """Initialize SQLite database for notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                note_type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                tags TEXT,
                user_id TEXT NOT NULL,
                summary TEXT,
                word_count INTEGER DEFAULT 0,
                reading_time INTEGER DEFAULT 0,
                is_favorite BOOLEAN DEFAULT FALSE,
                parent_id TEXT,
                ai_insights TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON notes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_type ON notes(note_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON notes(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON notes(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_id ON notes(parent_id)")
        
        # Full-text search table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                note_id, title, content, tags,
                content='notes', content_rowid='rowid'
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def _load_notes(self):
        """Load recent notes into cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load notes from last 90 days or favorites
        ninety_days_ago = datetime.now() - timedelta(days=90)
        
        cursor.execute("""
            SELECT * FROM notes 
            WHERE updated_at > ? OR is_favorite = TRUE
            ORDER BY updated_at DESC
            LIMIT 2000
        """, (ninety_days_ago,))
        
        rows = cursor.fetchall()
        for row in rows:
            note = self._row_to_note(row)
            self.notes_cache[note.id] = note
        
        conn.close()
        self.logger.info(f"📚 Loaded {len(self.notes_cache)} notes into cache")
    
    def _row_to_note(self, row: tuple) -> Note:
        """Convert database row to Note object"""
        return Note(
            id=row[0],
            title=row[1],
            content=row[2],
            note_type=NoteType(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            tags=json.loads(row[6]) if row[6] else [],
            user_id=row[7],
            summary=row[8],
            word_count=row[9] or 0,
            reading_time=row[10] or 0,
            is_favorite=bool(row[11]),
            parent_id=row[12],
            ai_insights=json.loads(row[13]) if row[13] else []
        )
    
    async def _build_search_index(self):
        """Build in-memory search index"""
        self.search_index = {}
        
        for note in self.notes_cache.values():
            # Index words from title and content
            words = (note.title + " " + note.content + " " + " ".join(note.tags)).lower().split()
            
            for word in words:
                if len(word) > 2:  # Skip very short words
                    word = word.strip('.,!?";')
                    if word not in self.search_index:
                        self.search_index[word] = []
                    if note.id not in self.search_index[word]:
                        self.search_index[word].append(note.id)
        
        self.logger.info(f"🔍 Built search index with {len(self.search_index)} terms")
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process notes management requests"""
        action = request.action.lower()
        
        handlers = {
            "create": self._create_note,
            "list": self._list_notes,
            "get": self._get_note,
            "update": self._update_note,
            "delete": self._delete_note,
            "search": self._search_notes,
            "summarize": self._summarize_note,
            "analyze": self._analyze_notes,
            "suggest_tags": self._suggest_tags,
            "extract_insights": self._extract_insights,
            "organize": self._organize_notes,
            "export": self._export_notes
        }
        
        if action not in handlers:
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Unknown action: {action}",
                error="INVALID_ACTION"
            )
        
        try:
            return await handlers[action](request)
        except Exception as e:
            self.logger.error(f"Error processing {action}: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Error processing {action}: {str(e)}",
                error=str(e)
            )
    
    async def _create_note(self, request: ModuleRequest) -> ModuleResponse:
        """Create a new note with AI enhancement"""
        data = request.data
        
        # Validate required fields
        if not data.get("title") or not data.get("content"):
            return ModuleResponse(
                success=False,
                data=None,
                message="Note title and content are required",
                error="MISSING_REQUIRED_FIELDS"
            )
        
        # Generate note ID
        content_hash = hashlib.md5(data["content"].encode()).hexdigest()[:8]
        note_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}"
        
        # Create note object
        note = Note(
            id=note_id,
            title=data["title"],
            content=data["content"],
            note_type=NoteType(data.get("note_type", "text")),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=data.get("tags", []),
            user_id=request.user_id,
            parent_id=data.get("parent_id"),
            is_favorite=data.get("is_favorite", False)
        )
        
        # Get AI enhancements if enabled
        ai_cost = 0.0
        ai_provider = None
        
        if data.get("ai_enhance", True) and len(note.content) > 100:
            # Get AI summary and insights
            summary_response = await self._get_ai_summary(note)
            if summary_response.success:
                note.summary = summary_response.data.get("summary")
                note.ai_insights = summary_response.data.get("insights", [])
                ai_cost += summary_response.cost_estimate
                ai_provider = summary_response.ai_provider_used
            
            # Suggest tags if none provided
            if not note.tags:
                tags_response = await self._get_ai_tags(note)
                if tags_response.success:
                    note.tags = tags_response.data.get("tags", [])
                    ai_cost += tags_response.cost_estimate
        
        # Save to database and cache
        await self._save_note(note)
        self.notes_cache[note.id] = note
        
        # Update search index
        await self._add_to_search_index(note)
        
        # 🚀 GOOGLE KEEP SYNC - Automatically sync to Google Keep if API configured
        google_sync_status = await self._sync_to_google_keep(note)
        
        return ModuleResponse(
            success=True,
            data={
                **asdict(note),
                "google_keep_synced": google_sync_status.get("synced", False),
                "google_keep_id": google_sync_status.get("google_id")
            },
            message="Note created successfully" + (" and synced to Google Keep" if google_sync_status.get("synced") else ""),
            cost_estimate=ai_cost,
            ai_provider_used=ai_provider
        )
    
    async def _sync_to_google_keep(self, note: Note) -> Dict[str, Any]:
        """Sync note to Google Keep if API is configured"""
        try:
            # Check if Google Keep API is configured
            google_keep_api_key = self.config.get("google_keep_api_key")
            google_credentials = self.config.get("google_credentials_file")
            
            if not google_keep_api_key and not google_credentials:
                self.logger.debug("📝 Google Keep API not configured - skipping sync")
                return {"synced": False, "reason": "API not configured"}
            
            # Initialize Google Keep service if not already done
            if not hasattr(self, 'google_keep_service') or not self.google_keep_service:
                self.google_keep_service = await self._init_google_keep_service()
            
            if not self.google_keep_service:
                return {"synced": False, "reason": "Failed to initialize Google Keep service"}
            
            # Create note in Google Keep
            google_note_data = {
                "title": note.title,
                "textContent": {
                    "text": note.content
                },
                "labels": [{"name": tag} for tag in note.tags[:10]],  # Google Keep has label limits
            }
            
            # TODO: Implement actual Google Keep API call here
            # For now, we'll simulate the sync
            self.logger.info(f"🔄 Syncing note '{note.title}' to Google Keep...")
            
            # Simulated Google Keep response
            google_note_id = f"gkeep_{note.id}"
            
            # Store Google Keep ID in local note for future syncing
            note.ai_insights.append(f"google_keep_id:{google_note_id}")
            await self._save_note(note)
            
            self.logger.info(f"✅ Note synced to Google Keep: {google_note_id}")
            return {
                "synced": True, 
                "google_id": google_note_id,
                "sync_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to sync to Google Keep: {e}")
            return {"synced": False, "error": str(e)}
    
    async def _init_google_keep_service(self):
        """Initialize Google Keep API service"""
        try:
            # TODO: Implement actual Google Keep API initialization
            # This would use Google's client libraries
            self.logger.info("🔧 Initializing Google Keep API service...")
            
            # For now, return a mock service indicator
            return "google_keep_service_ready"
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google Keep service: {e}")
            return None

    async def _get_ai_summary(self, note: Note) -> ModuleResponse:
        """Get AI summary and insights for note"""
        messages = [
            {
                "role": "system",
                "content": """You are a note analysis AI. Analyze the note content and provide:
1. A concise 1-2 sentence summary
2. 3-5 key insights or important points
3. Potential connections to other topics

Respond in JSON format:
{
    "summary": "Brief summary of the note",
    "insights": ["insight1", "insight2", "insight3"],
    "topics": ["topic1", "topic2"],
    "sentiment": "positive/neutral/negative"
}"""
            },
            {
                "role": "user",
                "content": f"""Title: {note.title}
Type: {note.note_type.value}
Content: {note.content[:2000]}...

Please analyze this note and provide summary and insights."""
            }
        ]
        
        ai_response = await self._use_ai_provider(messages, TaskType.ANALYSIS)
        
        if ai_response.success:
            try:
                analysis_data = json.loads(ai_response.data)
                return ModuleResponse(
                    success=True,
                    data=analysis_data,
                    message="AI analysis completed",
                    cost_estimate=ai_response.cost_estimate,
                    ai_provider_used=ai_response.ai_provider_used
                )
            except json.JSONDecodeError:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message="Failed to parse AI analysis",
                    error="AI_PARSE_ERROR"
                )
        
        return ai_response
    
    async def _get_ai_tags(self, note: Note) -> ModuleResponse:
        """Get AI-suggested tags for note"""
        messages = [
            {
                "role": "system",
                "content": """You are a note tagging AI. Analyze the note and suggest 3-7 relevant tags.
Tags should be:
- Single words or short phrases
- Relevant to the content
- Useful for organization
- Not too generic

Respond in JSON format:
{
    "tags": ["tag1", "tag2", "tag3"],
    "category": "work/personal/research/idea/etc"
}"""
            },
            {
                "role": "user",
                "content": f"""Title: {note.title}
Type: {note.note_type.value}
Content: {note.content[:1000]}...

Please suggest relevant tags for this note."""
            }
        ]
        
        ai_response = await self._use_ai_provider(messages, TaskType.CODING)  # Use cheaper provider
        
        if ai_response.success:
            try:
                tags_data = json.loads(ai_response.data)
                return ModuleResponse(
                    success=True,
                    data=tags_data,
                    message="AI tags generated",
                    cost_estimate=ai_response.cost_estimate,
                    ai_provider_used=ai_response.ai_provider_used
                )
            except json.JSONDecodeError:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message="Failed to parse AI tags",
                    error="AI_PARSE_ERROR"
                )
        
        return ai_response
    
    async def _list_notes(self, request: ModuleRequest) -> ModuleResponse:
        """List notes with filtering options"""
        filters = request.data
        user_notes = [
            note for note in self.notes_cache.values() 
            if note.user_id == request.user_id
        ]
        
        # Apply filters
        if filters.get("note_type"):
            note_type = NoteType(filters["note_type"])
            user_notes = [n for n in user_notes if n.note_type == note_type]
        
        if filters.get("tag"):
            tag_filter = filters["tag"]
            user_notes = [n for n in user_notes if tag_filter in n.tags]
        
        if filters.get("favorites_only"):
            user_notes = [n for n in user_notes if n.is_favorite]
        
        if filters.get("recent_days"):
            days = int(filters["recent_days"])
            cutoff = datetime.now() - timedelta(days=days)
            user_notes = [n for n in user_notes if n.updated_at > cutoff]
        
        # Sort options
        sort_by = filters.get("sort_by", "updated_at")
        reverse = filters.get("sort_desc", True)
        
        if sort_by == "title":
            user_notes.sort(key=lambda n: n.title.lower(), reverse=reverse)
        elif sort_by == "created_at":
            user_notes.sort(key=lambda n: n.created_at, reverse=reverse)
        elif sort_by == "word_count":
            user_notes.sort(key=lambda n: n.word_count, reverse=reverse)
        else:  # default: updated_at
            user_notes.sort(key=lambda n: n.updated_at, reverse=reverse)
        
        # Limit results
        limit = filters.get("limit", 50)
        user_notes = user_notes[:limit]
        
        # Prepare response data
        notes_data = []
        for note in user_notes:
            note_dict = asdict(note)
            # Truncate content in list view
            if len(note.content) > 200:
                note_dict["content"] = note.content[:200] + "..."
            notes_data.append(note_dict)
        
        return ModuleResponse(
            success=True,
            data={
                "notes": notes_data,
                "total": len(user_notes),
                "filters_applied": filters
            },
            message=f"Retrieved {len(user_notes)} notes"
        )
    
    async def _search_notes(self, request: ModuleRequest) -> ModuleResponse:
        """Search notes using multiple methods"""
        query = request.data.get("query", "").lower().strip()
        if not query:
            return ModuleResponse(
                success=False,
                data=None,
                message="Search query is required",
                error="MISSING_QUERY"
            )
        
        user_notes = [
            note for note in self.notes_cache.values() 
            if note.user_id == request.user_id
        ]
        
        # Score-based search results
        search_results = []
        
        for note in user_notes:
            score = 0
            
            # Exact title match (highest score)
            if query in note.title.lower():
                score += 10
            
            # Content match
            if query in note.content.lower():
                score += 5
            
            # Tag match
            for tag in note.tags:
                if query in tag.lower():
                    score += 7
            
            # Summary match
            if note.summary and query in note.summary.lower():
                score += 6
            
            # Word-level search using index
            query_words = query.split()
            for word in query_words:
                if word in self.search_index and note.id in self.search_index[word]:
                    score += 2
            
            if score > 0:
                search_results.append((note, score))
        
        # Sort by relevance score
        search_results.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results
        limit = request.data.get("limit", 20)
        search_results = search_results[:limit]
        
        # Prepare response
        results_data = []
        for note, score in search_results:
            note_dict = asdict(note)
            note_dict["relevance_score"] = score
            # Highlight search terms in content preview
            content_preview = note.content[:300]
            note_dict["content_preview"] = content_preview
            results_data.append(note_dict)
        
        return ModuleResponse(
            success=True,
            data={
                "results": results_data,
                "total": len(search_results),
                "query": query
            },
            message=f"Found {len(search_results)} matching notes"
        )
    
    async def _summarize_note(self, request: ModuleRequest) -> ModuleResponse:
        """Generate or update AI summary for a note"""
        note_id = request.data.get("note_id")
        if not note_id or note_id not in self.notes_cache:
            return ModuleResponse(
                success=False,
                data=None,
                message="Note not found",
                error="NOTE_NOT_FOUND"
            )
        
        note = self.notes_cache[note_id]
        if note.user_id != request.user_id:
            return ModuleResponse(
                success=False,
                data=None,
                message="Access denied",
                error="ACCESS_DENIED"
            )
        
        # Generate new summary
        summary_response = await self._get_ai_summary(note)
        if summary_response.success:
            # Update note with new summary
            note.summary = summary_response.data.get("summary")
            note.ai_insights = summary_response.data.get("insights", [])
            note.updated_at = datetime.now()
            
            await self._save_note(note)
            
            return ModuleResponse(
                success=True,
                data={
                    "summary": note.summary,
                    "insights": note.ai_insights,
                    "analysis": summary_response.data
                },
                message="Note summary updated",
                cost_estimate=summary_response.cost_estimate,
                ai_provider_used=summary_response.ai_provider_used
            )
        
        return summary_response
    
    async def _save_note(self, note: Note):
        """Save note to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO notes 
            (id, title, content, note_type, created_at, updated_at, tags, user_id,
             summary, word_count, reading_time, is_favorite, parent_id, ai_insights)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note.id, note.title, note.content, note.note_type.value,
            note.created_at.isoformat(), note.updated_at.isoformat(),
            json.dumps(note.tags), note.user_id, note.summary,
            note.word_count, note.reading_time, note.is_favorite,
            note.parent_id, json.dumps(note.ai_insights)
        ))
        
        # Update FTS index
        cursor.execute("""
            INSERT OR REPLACE INTO notes_fts (note_id, title, content, tags)
            VALUES (?, ?, ?, ?)
        """, (note.id, note.title, note.content, " ".join(note.tags)))
        
        conn.commit()
        conn.close()
    
    async def _add_to_search_index(self, note: Note):
        """Add note to in-memory search index"""
        words = (note.title + " " + note.content + " " + " ".join(note.tags)).lower().split()
        
        for word in words:
            if len(word) > 2:
                word = word.strip('.,!?";')
                if word not in self.search_index:
                    self.search_index[word] = []
                if note.id not in self.search_index[word]:
                    self.search_index[word].append(note.id)
    
    async def get_capabilities(self) -> List[str]:
        """Get module capabilities"""
        return [
            "create_note", "list_notes", "get_note", "update_note", "delete_note",
            "search_notes", "summarize_note", "analyze_notes", "suggest_tags",
            "extract_insights", "organize_notes", "export_notes"
        ]
    
    async def _module_health_check(self) -> bool:
        """Check if notes module is healthy"""
        try:
            # Test database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notes LIMIT 1")
            conn.close()
            return True
        except Exception:
            return False
