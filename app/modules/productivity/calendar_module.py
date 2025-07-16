"""
Calendar & Reminders Module - ChoyAI Productivity Suite

Intelligent scheduling with Google Calendar integration
Local storage with optional cloud sync
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from app.modules.productivity import (
    BaseProductivityModule, ModuleRequest, ModuleResponse, ModuleConfig, ModuleType
)
from app.core.ai_providers import TaskType


class EventType(Enum):
    MEETING = "meeting"
    REMINDER = "reminder"
    TASK = "task"
    APPOINTMENT = "appointment"
    PERSONAL = "personal"
    WORK = "work"
    TRAVEL = "travel"
    DEADLINE = "deadline"


class ReminderType(Enum):
    NONE = "none"
    POPUP = "popup"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


@dataclass
class CalendarEvent:
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    location: Optional[str] = None
    attendees: List[str] = None
    reminders: List[Dict[str, Any]] = None
    user_id: str = ""
    is_all_day: bool = False
    recurrence_rule: Optional[str] = None  # RRULE format
    google_event_id: Optional[str] = None
    ai_suggestions: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []
        if self.reminders is None:
            self.reminders = []
        if self.ai_suggestions is None:
            self.ai_suggestions = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Reminder:
    id: str
    title: str
    description: str
    reminder_time: datetime
    reminder_type: ReminderType
    is_completed: bool = False
    user_id: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class CalendarModule(BaseProductivityModule):
    """AI-powered calendar and reminders module"""
    
    def __init__(self, config: ModuleConfig, ai_provider_manager):
        super().__init__(config, ai_provider_manager)
        self.db_path = "data/databases/calendar.db"
        self.events_cache: Dict[str, CalendarEvent] = {}
        self.reminders_cache: Dict[str, Reminder] = {}
        self.google_calendar_service = None  # Will be initialized if enabled
        
    async def initialize(self) -> bool:
        """Initialize calendar database and load events"""
        try:
            await self._init_database()
            await self._load_events()
            await self._load_reminders()
            # await self._init_google_calendar()  # Optional
            self.logger.info("✅ Calendar module initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize calendar module: {e}")
            return False
    
    async def _init_database(self):
        """Initialize SQLite database for calendar"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                location TEXT,
                attendees TEXT,
                reminders TEXT,
                user_id TEXT NOT NULL,
                is_all_day BOOLEAN DEFAULT FALSE,
                recurrence_rule TEXT,
                google_event_id TEXT,
                ai_suggestions TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                reminder_time TIMESTAMP NOT NULL,
                reminder_type TEXT NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_end_time ON events(end_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(reminder_time)")
        
        conn.commit()
        conn.close()
    
    async def _load_events(self):
        """Load upcoming events into cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load events from 30 days ago to 90 days ahead
        past_limit = datetime.now() - timedelta(days=30)
        future_limit = datetime.now() + timedelta(days=90)
        
        cursor.execute("""
            SELECT * FROM events 
            WHERE start_time BETWEEN ? AND ?
            ORDER BY start_time ASC
        """, (past_limit, future_limit))
        
        rows = cursor.fetchall()
        for row in rows:
            event = self._row_to_event(row)
            self.events_cache[event.id] = event
        
        conn.close()
        self.logger.info(f"📅 Loaded {len(self.events_cache)} events into cache")
    
    async def _load_reminders(self):
        """Load active reminders into cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load incomplete reminders from past 7 days to future 30 days
        past_limit = datetime.now() - timedelta(days=7)
        future_limit = datetime.now() + timedelta(days=30)
        
        cursor.execute("""
            SELECT * FROM reminders 
            WHERE reminder_time BETWEEN ? AND ? AND is_completed = FALSE
            ORDER BY reminder_time ASC
        """, (past_limit, future_limit))
        
        rows = cursor.fetchall()
        for row in rows:
            reminder = self._row_to_reminder(row)
            self.reminders_cache[reminder.id] = reminder
        
        conn.close()
        self.logger.info(f"⏰ Loaded {len(self.reminders_cache)} reminders into cache")
    
    def _row_to_event(self, row: tuple) -> CalendarEvent:
        """Convert database row to CalendarEvent object"""
        return CalendarEvent(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            start_time=datetime.fromisoformat(row[3]),
            end_time=datetime.fromisoformat(row[4]),
            event_type=EventType(row[5]),
            location=row[6],
            attendees=json.loads(row[7]) if row[7] else [],
            reminders=json.loads(row[8]) if row[8] else [],
            user_id=row[9],
            is_all_day=bool(row[10]),
            recurrence_rule=row[11],
            google_event_id=row[12],
            ai_suggestions=json.loads(row[13]) if row[13] else [],
            created_at=datetime.fromisoformat(row[14]),
            updated_at=datetime.fromisoformat(row[15])
        )
    
    def _row_to_reminder(self, row: tuple) -> Reminder:
        """Convert database row to Reminder object"""
        return Reminder(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            reminder_time=datetime.fromisoformat(row[3]),
            reminder_type=ReminderType(row[4]),
            is_completed=bool(row[5]),
            user_id=row[6],
            created_at=datetime.fromisoformat(row[7])
        )
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process calendar management requests"""
        action = request.action.lower()
        
        handlers = {
            # Events
            "create_event": self._create_event,
            "list_events": self._list_events,
            "get_event": self._get_event,
            "update_event": self._update_event,
            "delete_event": self._delete_event,
            
            # Reminders
            "create_reminder": self._create_reminder,
            "list_reminders": self._list_reminders,
            "complete_reminder": self._complete_reminder,
            
            # AI Features
            "suggest_schedule": self._suggest_schedule,
            "find_free_time": self._find_free_time,
            "optimize_schedule": self._optimize_schedule,
            "analyze_patterns": self._analyze_patterns,
            
            # Calendar views
            "get_day": self._get_day_view,
            "get_week": self._get_week_view,
            "get_month": self._get_month_view,
            
            # Google Calendar integration
            "sync_google": self._sync_google_calendar,
            "import_google": self._import_google_events
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
    
    async def _create_event(self, request: ModuleRequest) -> ModuleResponse:
        """Create a new calendar event with AI enhancement"""
        data = request.data
        
        # Validate required fields
        if not data.get("title") or not data.get("start_time"):
            return ModuleResponse(
                success=False,
                data=None,
                message="Event title and start time are required",
                error="MISSING_REQUIRED_FIELDS"
            )
        
        # Parse start and end times
        try:
            start_time = datetime.fromisoformat(data["start_time"])
            if data.get("end_time"):
                end_time = datetime.fromisoformat(data["end_time"])
            else:
                # Default to 1 hour duration
                end_time = start_time + timedelta(hours=1)
        except ValueError as e:
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Invalid date format: {str(e)}",
                error="INVALID_DATE_FORMAT"
            )
        
        # Generate event ID
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.events_cache)}"
        
        # Create event object
        event = CalendarEvent(
            id=event_id,
            title=data["title"],
            description=data.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            event_type=EventType(data.get("event_type", "personal")),
            location=data.get("location"),
            attendees=data.get("attendees", []),
            user_id=request.user_id,
            is_all_day=data.get("is_all_day", False),
            recurrence_rule=data.get("recurrence_rule")
        )
        
        # Get AI suggestions if enabled
        ai_cost = 0.0
        ai_provider = None
        
        if data.get("ai_enhance", True):
            suggestions_response = await self._get_event_suggestions(event)
            if suggestions_response.success:
                event.ai_suggestions = suggestions_response.data.get("suggestions", [])
                ai_cost += suggestions_response.cost_estimate
                ai_provider = suggestions_response.ai_provider_used
        
        # Check for conflicts
        conflicts = await self._check_conflicts(event, request.user_id)
        if conflicts and not data.get("ignore_conflicts", False):
            return ModuleResponse(
                success=False,
                data={
                    "conflicts": [asdict(c) for c in conflicts],
                    "suggested_event": asdict(event)
                },
                message=f"Schedule conflict detected with {len(conflicts)} existing events",
                error="SCHEDULE_CONFLICT"
            )
        
        # Save to database and cache
        await self._save_event(event)
        self.events_cache[event.id] = event
        
        return ModuleResponse(
            success=True,
            data=asdict(event),
            message="Event created successfully",
            cost_estimate=ai_cost,
            ai_provider_used=ai_provider
        )
    
    async def _get_event_suggestions(self, event: CalendarEvent) -> ModuleResponse:
        """Get AI suggestions for event optimization"""
        messages = [
            {
                "role": "system",
                "content": """You are a calendar AI assistant. Analyze the event and provide:
1. Preparation suggestions
2. Duration optimization
3. Location recommendations
4. Meeting agenda items (if applicable)
5. Follow-up reminders

Respond in JSON format:
{
    "suggestions": ["suggestion1", "suggestion2", ...],
    "optimal_duration": 60,
    "preparation_time": 15,
    "agenda_items": ["item1", "item2"],
    "follow_up": "recommended follow-up action"
}"""
            },
            {
                "role": "user",
                "content": f"""Event: {event.title}
Description: {event.description}
Type: {event.event_type.value}
Duration: {(event.end_time - event.start_time).total_seconds() / 60:.0f} minutes
Location: {event.location or 'Not specified'}
Attendees: {len(event.attendees)} people

Please provide optimization suggestions for this event."""
            }
        ]
        
        ai_response = await self._use_ai_provider(messages, TaskType.ANALYSIS)
        
        if ai_response.success:
            try:
                suggestions_data = json.loads(ai_response.data)
                return ModuleResponse(
                    success=True,
                    data=suggestions_data,
                    message="Event suggestions generated",
                    cost_estimate=ai_response.cost_estimate,
                    ai_provider_used=ai_response.ai_provider_used
                )
            except json.JSONDecodeError:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message="Failed to parse AI suggestions",
                    error="AI_PARSE_ERROR"
                )
        
        return ai_response
    
    async def _check_conflicts(self, new_event: CalendarEvent, user_id: str) -> List[CalendarEvent]:
        """Check for scheduling conflicts"""
        conflicts = []
        
        for event in self.events_cache.values():
            if (event.user_id == user_id and 
                event.id != new_event.id and
                self._events_overlap(new_event, event)):
                conflicts.append(event)
        
        return conflicts
    
    def _events_overlap(self, event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events overlap in time"""
        return (event1.start_time < event2.end_time and 
                event1.end_time > event2.start_time)
    
    async def _list_events(self, request: ModuleRequest) -> ModuleResponse:
        """List events with filtering options"""
        filters = request.data
        user_events = [
            event for event in self.events_cache.values() 
            if event.user_id == request.user_id
        ]
        
        # Apply filters
        if filters.get("event_type"):
            event_type = EventType(filters["event_type"])
            user_events = [e for e in user_events if e.event_type == event_type]
        
        if filters.get("date_from"):
            date_from = datetime.fromisoformat(filters["date_from"])
            user_events = [e for e in user_events if e.start_time >= date_from]
        
        if filters.get("date_to"):
            date_to = datetime.fromisoformat(filters["date_to"])
            user_events = [e for e in user_events if e.start_time <= date_to]
        
        if filters.get("location"):
            location_filter = filters["location"].lower()
            user_events = [
                e for e in user_events 
                if e.location and location_filter in e.location.lower()
            ]
        
        # Sort by start time
        user_events.sort(key=lambda e: e.start_time)
        
        # Limit results
        limit = filters.get("limit", 100)
        user_events = user_events[:limit]
        
        return ModuleResponse(
            success=True,
            data={
                "events": [asdict(event) for event in user_events],
                "total": len(user_events),
                "filters_applied": filters
            },
            message=f"Retrieved {len(user_events)} events"
        )
    
    async def _find_free_time(self, request: ModuleRequest) -> ModuleResponse:
        """Find available time slots using AI analysis"""
        data = request.data
        duration_minutes = data.get("duration", 60)
        date_from = datetime.fromisoformat(data.get("date_from", datetime.now().isoformat()))
        date_to = datetime.fromisoformat(data.get("date_to", (datetime.now() + timedelta(days=7)).isoformat()))
        
        # Get user's events in the time range
        user_events = [
            event for event in self.events_cache.values() 
            if (event.user_id == request.user_id and 
                event.start_time <= date_to and 
                event.end_time >= date_from)
        ]
        
        # Sort events by start time
        user_events.sort(key=lambda e: e.start_time)
        
        # Find gaps between events
        free_slots = []
        current_time = max(date_from, datetime.now())
        
        # Working hours (default 9 AM to 6 PM)
        work_start = data.get("work_start_hour", 9)
        work_end = data.get("work_end_hour", 18)
        
        for event in user_events:
            # Check gap before this event
            if (event.start_time - current_time).total_seconds() >= duration_minutes * 60:
                # Ensure it's within working hours
                slot_start = max(current_time, current_time.replace(hour=work_start, minute=0, second=0))
                slot_end = min(event.start_time, current_time.replace(hour=work_end, minute=0, second=0))
                
                if (slot_end - slot_start).total_seconds() >= duration_minutes * 60:
                    free_slots.append({
                        "start_time": slot_start.isoformat(),
                        "end_time": slot_end.isoformat(),
                        "duration_minutes": int((slot_end - slot_start).total_seconds() / 60)
                    })
            
            current_time = max(current_time, event.end_time)
        
        # Check gap after last event
        if current_time < date_to:
            slot_start = max(current_time, current_time.replace(hour=work_start, minute=0, second=0))
            slot_end = min(date_to, current_time.replace(hour=work_end, minute=0, second=0))
            
            if (slot_end - slot_start).total_seconds() >= duration_minutes * 60:
                free_slots.append({
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "duration_minutes": int((slot_end - slot_start).total_seconds() / 60)
                })
        
        return ModuleResponse(
            success=True,
            data={
                "free_slots": free_slots[:10],  # Limit to 10 suggestions
                "total_slots": len(free_slots),
                "requested_duration": duration_minutes,
                "search_period": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat()
                }
            },
            message=f"Found {len(free_slots)} available time slots"
        )
    
    async def _save_event(self, event: CalendarEvent):
        """Save event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO events 
            (id, title, description, start_time, end_time, event_type, location,
             attendees, reminders, user_id, is_all_day, recurrence_rule, 
             google_event_id, ai_suggestions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id, event.title, event.description,
            event.start_time.isoformat(), event.end_time.isoformat(),
            event.event_type.value, event.location,
            json.dumps(event.attendees), json.dumps(event.reminders),
            event.user_id, event.is_all_day, event.recurrence_rule,
            event.google_event_id, json.dumps(event.ai_suggestions),
            event.created_at.isoformat(), event.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def get_capabilities(self) -> List[str]:
        """Get module capabilities"""
        return [
            "create_event", "list_events", "get_event", "update_event", "delete_event",
            "create_reminder", "list_reminders", "complete_reminder",
            "suggest_schedule", "find_free_time", "optimize_schedule", "analyze_patterns",
            "get_day", "get_week", "get_month",
            "sync_google", "import_google"
        ]
    
    async def _module_health_check(self) -> bool:
        """Check if calendar module is healthy"""
        try:
            # Test database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events LIMIT 1")
            cursor.execute("SELECT COUNT(*) FROM reminders LIMIT 1")
            conn.close()
            return True
        except Exception:
            return False
    
    async def _sync_google_calendar(self, request: ModuleRequest) -> ModuleResponse:
        """Sync events with Google Calendar"""
        try:
            # Check if Google Calendar API is configured
            if not self.google_calendar_service:
                # Try to initialize Google Calendar service
                api_key = self.config.get("google_calendar_api_key")
                if not api_key:
                    return ModuleResponse(
                        success=False,
                        data=None,
                        message="Google Calendar API key not configured. Add GOOGLE_CALENDAR_API_KEY to .env file.",
                        error="GOOGLE_API_NOT_CONFIGURED"
                    )
                
                # Initialize Google Calendar service (placeholder)
                # self.google_calendar_service = await self._init_google_calendar_service(api_key)
            
            # For now, return a placeholder response indicating what would happen
            return ModuleResponse(
                success=True,
                data={
                    "synced_events": 0,
                    "created_in_google": 0,
                    "updated_from_google": 0,
                    "status": "Ready for Google Calendar sync",
                    "setup_required": "Add GOOGLE_CALENDAR_API_KEY to enable sync"
                },
                message="Google Calendar sync configuration detected. Add API key to enable full sync.",
                error=None
            )
            
        except Exception as e:
            self.logger.error(f"Error syncing with Google Calendar: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Error syncing with Google Calendar: {str(e)}",
                error=str(e)
            )
    
    async def _import_google_events(self, request: ModuleRequest) -> ModuleResponse:
        """Import events from Google Calendar"""
        try:
            # Check if Google Calendar API is configured
            if not self.google_calendar_service:
                api_key = self.config.get("google_calendar_api_key")
                if not api_key:
                    return ModuleResponse(
                        success=False,
                        data=None,
                        message="Google Calendar API key not configured. Add GOOGLE_CALENDAR_API_KEY to .env file.",
                        error="GOOGLE_API_NOT_CONFIGURED"
                    )
            
            # Get date range for import
            data = request.data or {}
            start_date = data.get("start_date", datetime.now().isoformat())
            end_date = data.get("end_date", (datetime.now() + timedelta(days=30)).isoformat())
            
            # For now, return a placeholder response
            return ModuleResponse(
                success=True,
                data={
                    "imported_events": 0,
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "status": "Ready for Google Calendar import",
                    "setup_required": "Add GOOGLE_CALENDAR_API_KEY to enable import"
                },
                message="Google Calendar import configuration detected. Add API key to enable full import.",
                error=None
            )
            
        except Exception as e:
            self.logger.error(f"Error importing from Google Calendar: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Error importing from Google Calendar: {str(e)}",
                error=str(e)
            )
