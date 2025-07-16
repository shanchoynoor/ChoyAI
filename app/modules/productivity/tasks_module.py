"""
Tasks & To-Do Module - ChoyAI Productivity Suite

Cost-effective task management with AI assistance
Local storage with optional cloud sync
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from app.modules.productivity import (
    BaseProductivityModule, ModuleRequest, ModuleResponse, ModuleConfig, ModuleType
)
from app.core.ai_providers import TaskType


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = None
    user_id: str = ""
    estimated_duration: Optional[int] = None  # minutes
    ai_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.ai_suggestions is None:
            self.ai_suggestions = []


class TasksModule(BaseProductivityModule):
    """AI-powered task management module"""
    
    def __init__(self, config: ModuleConfig, ai_provider_manager):
        super().__init__(config, ai_provider_manager)
        self.db_path = "data/databases/tasks.db"
        self.tasks_cache: Dict[str, Task] = {}
        
    async def initialize(self) -> bool:
        """Initialize tasks database and load tasks"""
        try:
            await self._init_database()
            await self._load_tasks()
            self.logger.info("✅ Tasks module initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize tasks module: {e}")
            return False
    
    async def _init_database(self):
        """Initialize SQLite database for tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                tags TEXT,
                user_id TEXT NOT NULL,
                estimated_duration INTEGER,
                ai_suggestions TEXT
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON tasks(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_due_date ON tasks(due_date)")
        
        conn.commit()
        conn.close()
    
    async def _load_tasks(self):
        """Load recent tasks into cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load tasks from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE created_at > ? OR status IN ('pending', 'in_progress')
            ORDER BY created_at DESC
            LIMIT 1000
        """, (thirty_days_ago,))
        
        rows = cursor.fetchall()
        for row in rows:
            task = self._row_to_task(row)
            self.tasks_cache[task.id] = task
        
        conn.close()
        self.logger.info(f"📚 Loaded {len(self.tasks_cache)} tasks into cache")
    
    def _row_to_task(self, row: tuple) -> Task:
        """Convert database row to Task object"""
        return Task(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            priority=TaskPriority(row[3]),
            status=TaskStatus(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            due_date=datetime.fromisoformat(row[6]) if row[6] else None,
            completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            tags=json.loads(row[8]) if row[8] else [],
            user_id=row[9],
            estimated_duration=row[10],
            ai_suggestions=json.loads(row[11]) if row[11] else []
        )
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process task management requests"""
        action = request.action.lower()
        
        # Route to appropriate handler
        handlers = {
            "create": self._create_task,
            "list": self._list_tasks,
            "update": self._update_task,
            "delete": self._delete_task,
            "complete": self._complete_task,
            "analyze": self._analyze_tasks,
            "suggest": self._suggest_tasks,
            "search": self._search_tasks,
            "prioritize": self._prioritize_tasks,
            "schedule": self._schedule_tasks
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
    
    async def _create_task(self, request: ModuleRequest) -> ModuleResponse:
        """Create a new task with AI enhancement"""
        data = request.data
        
        # Validate required fields
        if not data.get("title"):
            return ModuleResponse(
                success=False,
                data=None,
                message="Task title is required",
                error="MISSING_TITLE"
            )
        
        # Generate task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.tasks_cache)}"
        
        # Create task object
        task = Task(
            id=task_id,
            title=data["title"],
            description=data.get("description", ""),
            priority=TaskPriority(data.get("priority", "medium")),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            tags=data.get("tags", []),
            user_id=request.user_id,
            estimated_duration=data.get("estimated_duration")
        )
        
        # Get AI suggestions if enabled
        if data.get("ai_enhance", True):
            ai_response = await self._get_ai_suggestions(task)
            if ai_response.success:
                task.ai_suggestions = ai_response.data.get("suggestions", [])
                task.estimated_duration = ai_response.data.get("estimated_duration", task.estimated_duration)
        
        # Save to database
        await self._save_task(task)
        self.tasks_cache[task.id] = task
        
        return ModuleResponse(
            success=True,
            data=asdict(task),
            message="Task created successfully",
            cost_estimate=getattr(ai_response, 'cost_estimate', 0.0),
            ai_provider_used=getattr(ai_response, 'ai_provider_used', None)
        )
    
    async def _get_ai_suggestions(self, task: Task) -> ModuleResponse:
        """Get AI suggestions for task optimization"""
        messages = [
            {
                "role": "system",
                "content": """You are a productivity AI assistant. Analyze the task and provide:
1. 3-5 actionable suggestions to complete the task efficiently
2. Estimated duration in minutes
3. Potential sub-tasks if complex
4. Priority assessment

Respond in JSON format:
{
    "suggestions": ["suggestion1", "suggestion2", ...],
    "estimated_duration": 60,
    "sub_tasks": ["subtask1", "subtask2", ...],
    "priority_reasoning": "why this priority level"
}"""
            },
            {
                "role": "user",
                "content": f"""Task: {task.title}
Description: {task.description}
Current Priority: {task.priority.value}
Due Date: {task.due_date.isoformat() if task.due_date else 'Not set'}
Tags: {', '.join(task.tags) if task.tags else 'None'}

Please analyze this task and provide optimization suggestions."""
            }
        ]
        
        ai_response = await self._use_ai_provider(messages, TaskType.ANALYSIS)
        
        if ai_response.success:
            try:
                # Parse AI response
                suggestions_data = json.loads(ai_response.data)
                return ModuleResponse(
                    success=True,
                    data=suggestions_data,
                    message="AI suggestions generated",
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
    
    async def _list_tasks(self, request: ModuleRequest) -> ModuleResponse:
        """List tasks with filtering options"""
        filters = request.data
        user_tasks = [
            task for task in self.tasks_cache.values() 
            if task.user_id == request.user_id
        ]
        
        # Apply filters
        if filters.get("status"):
            status_filter = TaskStatus(filters["status"])
            user_tasks = [t for t in user_tasks if t.status == status_filter]
        
        if filters.get("priority"):
            priority_filter = TaskPriority(filters["priority"])
            user_tasks = [t for t in user_tasks if t.priority == priority_filter]
        
        if filters.get("tag"):
            tag_filter = filters["tag"]
            user_tasks = [t for t in user_tasks if tag_filter in t.tags]
        
        if filters.get("due_soon"):
            # Tasks due in next 7 days
            week_from_now = datetime.now() + timedelta(days=7)
            user_tasks = [
                t for t in user_tasks 
                if t.due_date and t.due_date <= week_from_now
            ]
        
        # Sort by priority and due date
        user_tasks.sort(key=lambda t: (
            t.status == TaskStatus.COMPLETED,  # Incomplete first
            t.priority != TaskPriority.URGENT,  # Urgent first
            t.priority != TaskPriority.HIGH,    # High second
            t.due_date or datetime.max          # Due soonest first
        ))
        
        # Limit results
        limit = filters.get("limit", 50)
        user_tasks = user_tasks[:limit]
        
        return ModuleResponse(
            success=True,
            data={
                "tasks": [asdict(task) for task in user_tasks],
                "total": len(user_tasks),
                "filters_applied": filters
            },
            message=f"Retrieved {len(user_tasks)} tasks"
        )
    
    async def _analyze_tasks(self, request: ModuleRequest) -> ModuleResponse:
        """Analyze tasks with AI insights"""
        user_tasks = [
            task for task in self.tasks_cache.values() 
            if task.user_id == request.user_id
        ]
        
        if not user_tasks:
            return ModuleResponse(
                success=True,
                data={"insights": "No tasks to analyze"},
                message="No tasks found for analysis"
            )
        
        # Prepare task summary for AI
        pending_tasks = [t for t in user_tasks if t.status == TaskStatus.PENDING]
        overdue_tasks = [
            t for t in pending_tasks 
            if t.due_date and t.due_date < datetime.now()
        ]
        
        task_summary = {
            "total_tasks": len(user_tasks),
            "pending": len(pending_tasks),
            "overdue": len(overdue_tasks),
            "urgent_tasks": len([t for t in pending_tasks if t.priority == TaskPriority.URGENT]),
            "recent_completions": len([
                t for t in user_tasks 
                if t.status == TaskStatus.COMPLETED and 
                t.completed_at and 
                t.completed_at > datetime.now() - timedelta(days=7)
            ])
        }
        
        messages = [
            {
                "role": "system", 
                "content": """You are a productivity analyst. Analyze the user's task patterns and provide:
1. Productivity insights
2. Workflow recommendations
3. Time management suggestions
4. Priority optimization tips

Respond in JSON format with actionable insights."""
            },
            {
                "role": "user",
                "content": f"""Analyze my task management patterns:

Task Summary:
- Total tasks: {task_summary['total_tasks']}
- Pending tasks: {task_summary['pending']}
- Overdue tasks: {task_summary['overdue']}
- Urgent tasks: {task_summary['urgent_tasks']}
- Completed this week: {task_summary['recent_completions']}

Recent tasks:
{json.dumps([{
    'title': t.title,
    'priority': t.priority.value,
    'status': t.status.value,
    'created_days_ago': (datetime.now() - t.created_at).days
} for t in user_tasks[:10]], indent=2)}

Provide productivity insights and recommendations."""
            }
        ]
        
        return await self._use_ai_provider(messages, TaskType.ANALYSIS)
    
    async def _save_task(self, task: Task):
        """Save task to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks 
            (id, title, description, priority, status, created_at, due_date, 
             completed_at, tags, user_id, estimated_duration, ai_suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id, task.title, task.description, task.priority.value,
            task.status.value, task.created_at.isoformat(),
            task.due_date.isoformat() if task.due_date else None,
            task.completed_at.isoformat() if task.completed_at else None,
            json.dumps(task.tags), task.user_id, task.estimated_duration,
            json.dumps(task.ai_suggestions)
        ))
        
        conn.commit()
        conn.close()
    
    async def _complete_task(self, request: ModuleRequest) -> ModuleResponse:
        """Mark task as completed"""
        task_id = request.data.get("task_id")
        if not task_id or task_id not in self.tasks_cache:
            return ModuleResponse(
                success=False,
                data=None,
                message="Task not found",
                error="TASK_NOT_FOUND"
            )
        
        task = self.tasks_cache[task_id]
        if task.user_id != request.user_id:
            return ModuleResponse(
                success=False,
                data=None,
                message="Access denied",
                error="ACCESS_DENIED"
            )
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        await self._save_task(task)
        
        return ModuleResponse(
            success=True,
            data=asdict(task),
            message="Task completed successfully"
        )
    
    async def get_capabilities(self) -> List[str]:
        """Get module capabilities"""
        return [
            "create_task", "list_tasks", "update_task", "delete_task",
            "complete_task", "analyze_tasks", "suggest_tasks", 
            "search_tasks", "prioritize_tasks", "schedule_tasks"
        ]
    
    async def _module_health_check(self) -> bool:
        """Check if tasks module is healthy"""
        try:
            # Test database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks LIMIT 1")
            conn.close()
            return True
        except Exception:
            return False


# Additional helper functions for other actions
    async def _update_task(self, request: ModuleRequest) -> ModuleResponse:
        """Update existing task"""
        task_id = request.data.get("task_id")
        if not task_id or task_id not in self.tasks_cache:
            return ModuleResponse(
                success=False,
                data=None,
                message="Task not found",
                error="TASK_NOT_FOUND"
            )
        
        task = self.tasks_cache[task_id]
        if task.user_id != request.user_id:
            return ModuleResponse(
                success=False,
                data=None,
                message="Access denied",
                error="ACCESS_DENIED"
            )
        
        # Update fields
        updates = request.data.get("updates", {})
        if "title" in updates:
            task.title = updates["title"]
        if "description" in updates:
            task.description = updates["description"]
        if "priority" in updates:
            task.priority = TaskPriority(updates["priority"])
        if "status" in updates:
            task.status = TaskStatus(updates["status"])
        if "due_date" in updates:
            task.due_date = datetime.fromisoformat(updates["due_date"]) if updates["due_date"] else None
        if "tags" in updates:
            task.tags = updates["tags"]
        
        await self._save_task(task)
        
        return ModuleResponse(
            success=True,
            data=asdict(task),
            message="Task updated successfully"
        )
    
    async def _search_tasks(self, request: ModuleRequest) -> ModuleResponse:
        """Search tasks by keyword"""
        query = request.data.get("query", "").lower()
        if not query:
            return ModuleResponse(
                success=False,
                data=None,
                message="Search query is required",
                error="MISSING_QUERY"
            )
        
        user_tasks = [
            task for task in self.tasks_cache.values() 
            if task.user_id == request.user_id
        ]
        
        # Search in title, description, and tags
        matching_tasks = []
        for task in user_tasks:
            if (query in task.title.lower() or 
                query in task.description.lower() or 
                any(query in tag.lower() for tag in task.tags)):
                matching_tasks.append(task)
        
        return ModuleResponse(
            success=True,
            data={
                "tasks": [asdict(task) for task in matching_tasks],
                "total": len(matching_tasks),
                "query": query
            },
            message=f"Found {len(matching_tasks)} matching tasks"
        )
