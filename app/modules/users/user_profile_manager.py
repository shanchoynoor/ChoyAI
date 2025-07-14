"""
User Profile Manager for Choy AI Brain

Automatically builds comprehensive user profiles from conversations including:
- Personal information (name, age, city, profession, background)
- Preferences and interests
- Conversation patterns and history
- Behavioral insights
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.sqlite import insert

from app.config.settings import settings
from app.utils.logger import log_system_activity

Base = declarative_base()


@dataclass
class UserPersona:
    """User persona data structure"""
    user_id: str
    platform: str
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    education: Optional[str] = None
    background: Optional[str] = None
    interests: List[str] = None
    personality_traits: List[str] = None
    communication_style: Optional[str] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None
    relationship_status: Optional[str] = None
    family: Optional[str] = None
    goals: List[str] = None
    preferences: Dict[str, Any] = None
    confidence_scores: Dict[str, float] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.personality_traits is None:
            self.personality_traits = []
        if self.goals is None:
            self.goals = []
        if self.preferences is None:
            self.preferences = {}
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat() if value else None
            elif isinstance(value, (list, dict)):
                result[key] = value if value else ([] if isinstance(value, list) else {})
            else:
                result[key] = value
        return result


class UserProfile(Base):
    """SQLAlchemy model for user profiles"""
    __tablename__ = 'user_profiles'
    
    user_id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    
    # Basic Information
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    country = Column(String)
    profession = Column(String)
    education = Column(String)
    background = Column(Text)
    
    # Lists stored as JSON
    interests = Column(JSON, default=list)
    personality_traits = Column(JSON, default=list)
    goals = Column(JSON, default=list)
    
    # Communication & Preferences
    communication_style = Column(String)
    language_preference = Column(String)
    timezone = Column(String)
    
    # Personal Details
    relationship_status = Column(String)
    family = Column(String)
    
    # Metadata
    preferences = Column(JSON, default=dict)
    confidence_scores = Column(JSON, default=dict)
    
    # Platform-specific data
    telegram_username = Column(String)
    telegram_first_name = Column(String)
    telegram_last_name = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_interaction = Column(DateTime)
    
    # Relationships
    conversations = relationship("UserConversation", back_populates="profile", cascade="all, delete-orphan")


class UserConversation(Base):
    """SQLAlchemy model for user conversation history"""
    __tablename__ = 'user_conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('user_profiles.user_id'), nullable=False)
    platform = Column(String, nullable=False)
    
    # Message Content
    message_type = Column(String)  # user_message, ai_response, system
    content = Column(Text, nullable=False)
    message_id = Column(String)  # Platform-specific message ID
    
    # Context
    persona_used = Column(String)
    ai_provider = Column(String)
    task_type = Column(String)
    
    # Extracted Insights
    extracted_info = Column(JSON, default=dict)  # Information extracted from this message
    sentiment = Column(String)  # positive, negative, neutral
    topics = Column(JSON, default=list)  # Topics discussed
    intent = Column(String)  # User intent (question, request, chat, etc.)
    
    # Metadata
    session_id = Column(String)
    response_time = Column(Integer)  # AI response time in ms
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="conversations")


class UserProfileManager:
    """Manages user profiles and conversation analysis"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        if not db_path:
            db_path = settings.data_dir / "databases" / "user_profiles.db"
        
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Information extraction patterns
        self._setup_extraction_patterns()
        
        self.logger.info("User Profile Manager initialized")
    
    def _setup_extraction_patterns(self):
        """Setup regex patterns for extracting user information"""
        self.extraction_patterns = {
            'name': [
                r"(?:my name is|i'm|i am|call me|name's)\s+([a-zA-Z\s]+)",
                r"(?:i'm|i am)\s+([a-zA-Z]+)",
            ],
            'age': [
                r"(?:i'm|i am|age is|years old)\s*(\d{1,2})\s*(?:years?\s*old)?",
                r"(\d{1,2})\s*(?:years?\s*old|yr|yrs)",
            ],
            'city': [
                r"(?:i live in|from|in|located in|based in)\s+([a-zA-Z\s]+)(?:,|$|\s)",
                r"(?:my city is|city:)\s*([a-zA-Z\s]+)",
            ],
            'profession': [
                r"(?:i work as|i'm a|i am a|my job is|profession is|work at)\s+([a-zA-Z\s]+)",
                r"(?:i'm|i am)\s+(?:a|an)\s+([a-zA-Z\s]+)(?:\s+at|\s+in|$)",
            ],
            'interests': [
                r"(?:i like|i love|interested in|enjoy|hobby|hobbies)\s+([a-zA-Z\s,]+)",
                r"(?:my favorite|favourite)\s+([a-zA-Z\s]+)",
            ],
            'education': [
                r"(?:i studied|graduated from|degree in|education)\s+([a-zA-Z\s]+)",
                r"(?:university|college|school)\s+([a-zA-Z\s]+)",
            ],
            'relationship': [
                r"(?:i'm|i am)\s+(?:married|single|dating|in a relationship)",
                r"(?:my wife|my husband|my partner|my girlfriend|my boyfriend)",
            ],
            'goals': [
                r"(?:i want to|goal is|planning to|hoping to)\s+([a-zA-Z\s]+)",
                r"(?:my goal|objective|aim)\s+(?:is|:)\s*([a-zA-Z\s]+)",
            ]
        }
    
    async def process_conversation(
        self,
        user_id: str,
        message: str,
        message_type: str = "user_message",
        platform: str = "telegram",
        persona_used: Optional[str] = None,
        ai_provider: Optional[str] = None,
        task_type: Optional[str] = None,
        platform_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a conversation message and extract user information
        
        Returns:
            Tuple of (extracted_info, updated_profile_data)
        """
        try:
            # Extract information from the message
            extracted_info = await self._extract_information(message, message_type)
            
            # Analyze sentiment and topics
            sentiment = self._analyze_sentiment(message)
            topics = self._extract_topics(message)
            intent = self._determine_intent(message, message_type)
            
            # Save conversation record
            await self._save_conversation(
                user_id=user_id,
                platform=platform,
                message_type=message_type,
                content=message,
                persona_used=persona_used,
                ai_provider=ai_provider,
                task_type=task_type,
                extracted_info=extracted_info,
                sentiment=sentiment,
                topics=topics,
                intent=intent,
                session_id=session_id
            )
            
            # Update user profile if information was extracted
            updated_profile = {}
            if extracted_info and message_type == "user_message":
                updated_profile = await self._update_user_profile(
                    user_id=user_id,
                    platform=platform,
                    extracted_info=extracted_info,
                    platform_data=platform_data
                )
            
            log_system_activity(
                action="conversation_processed",
                metadata={
                    "user_id": user_id,
                    "platform": platform,
                    "extracted_fields": len(extracted_info),
                    "updated_profile": bool(updated_profile)
                }
            )
            
            return extracted_info, updated_profile
            
        except Exception as e:
            self.logger.error(f"Error processing conversation for user {user_id}: {e}")
            return {}, {}
    
    async def update_user_info(
        self,
        user_id: str,
        platform: str = "telegram",
        **user_data
    ) -> bool:
        """Update user information directly (used for onboarding)"""
        try:
            # Filter and prepare the user data
            extracted_info = {}
            platform_data = {}
            
            # Handle platform-specific data
            if platform == "telegram":
                for field in ['username', 'first_name', 'last_name']:
                    if field in user_data:
                        platform_data[field] = user_data[field]
            
            # Handle profile fields
            profile_fields = ['name', 'age', 'city', 'profession', 'interests', 'education', 'goals']
            for field in profile_fields:
                if field in user_data and user_data[field] is not None:
                    extracted_info[field] = user_data[field]
            
            # Update the profile
            updated_profile = await self._update_user_profile(
                user_id=user_id,
                platform=platform,
                extracted_info=extracted_info,
                platform_data=platform_data
            )
            
            self.logger.info(f"Updated user info for {user_id}: {list(extracted_info.keys())}")
            return bool(updated_profile)
            
        except Exception as e:
            self.logger.error(f"Error updating user info for {user_id}: {e}")
            return False

    async def _extract_information(self, message: str, message_type: str) -> Dict[str, Any]:
        """Extract structured information from message"""
        if message_type != "user_message":
            return {}
        
        extracted = {}
        message_lower = message.lower()
        
        for field, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                if matches:
                    if field in ['interests', 'goals']:
                        # Handle list fields
                        items = []
                        for match in matches:
                            # Split by common delimiters
                            split_items = re.split(r'[,;]', match)
                            items.extend([item.strip() for item in split_items if item.strip()])
                        if items:
                            extracted[field] = items
                    elif field == 'age':
                        # Convert age to integer
                        try:
                            extracted[field] = int(matches[0])
                        except ValueError:
                            continue
                    else:
                        # Single value fields
                        extracted[field] = matches[0].strip()
                    break
        
        return extracted
    
    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['happy', 'good', 'great', 'excellent', 'love', 'like', 'amazing', 'wonderful']
        negative_words = ['sad', 'bad', 'terrible', 'hate', 'dislike', 'awful', 'horrible', 'angry']
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract main topics from message"""
        topic_keywords = {
            'technology': ['tech', 'computer', 'software', 'programming', 'code', 'ai', 'machine learning'],
            'work': ['job', 'work', 'career', 'office', 'business', 'professional'],
            'personal': ['family', 'relationship', 'friend', 'personal', 'life'],
            'education': ['school', 'university', 'study', 'learn', 'education', 'course'],
            'health': ['health', 'fitness', 'exercise', 'medical', 'doctor'],
            'entertainment': ['movie', 'music', 'game', 'book', 'sport', 'travel'],
            'finance': ['money', 'budget', 'investment', 'financial', 'savings']
        }
        
        message_lower = message.lower()
        topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _determine_intent(self, message: str, message_type: str) -> str:
        """Determine user intent"""
        if message_type != "user_message":
            return "system"
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['?', 'what', 'how', 'why', 'when', 'where', 'who']):
            return "question"
        elif any(word in message_lower for word in ['please', 'can you', 'could you', 'help me']):
            return "request"
        elif any(word in message_lower for word in ['thank', 'thanks', 'bye', 'goodbye']):
            return "social"
        else:
            return "chat"
    
    async def _save_conversation(
        self,
        user_id: str,
        platform: str,
        message_type: str,
        content: str,
        persona_used: Optional[str],
        ai_provider: Optional[str],
        task_type: Optional[str],
        extracted_info: Dict[str, Any],
        sentiment: str,
        topics: List[str],
        intent: str,
        session_id: Optional[str]
    ):
        """Save conversation record to database"""
        session = self.SessionLocal()
        try:
            conversation = UserConversation(
                user_id=user_id,
                platform=platform,
                message_type=message_type,
                content=content,
                persona_used=persona_used,
                ai_provider=ai_provider,
                task_type=task_type,
                extracted_info=extracted_info,
                sentiment=sentiment,
                topics=topics,
                intent=intent,
                session_id=session_id
            )
            session.add(conversation)
            session.commit()
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving conversation: {e}")
        finally:
            session.close()
    
    async def _update_user_profile(
        self,
        user_id: str,
        platform: str,
        extracted_info: Dict[str, Any],
        platform_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update user profile with extracted information"""
        session = self.SessionLocal()
        try:
            # Get or create user profile
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            
            if not profile:
                profile = UserProfile(
                    user_id=user_id,
                    platform=platform,
                    preferences={},
                    confidence_scores={}
                )
                session.add(profile)
            
            # Update platform-specific data
            if platform_data and platform == "telegram":
                if 'username' in platform_data:
                    profile.telegram_username = platform_data['username']
                if 'first_name' in platform_data:
                    profile.telegram_first_name = platform_data['first_name']
                if 'last_name' in platform_data:
                    profile.telegram_last_name = platform_data['last_name']
            
            # Update extracted information with confidence scoring
            updated_fields = {}
            for field, value in extracted_info.items():
                if field in ['interests', 'goals', 'personality_traits']:
                    # Handle list fields - merge with existing
                    existing = getattr(profile, field, []) or []
                    if isinstance(value, list):
                        new_items = [item for item in value if item not in existing]
                        if new_items:
                            setattr(profile, field, existing + new_items)
                            updated_fields[field] = new_items
                    else:
                        if value not in existing:
                            setattr(profile, field, existing + [value])
                            updated_fields[field] = [value]
                else:
                    # Handle single value fields
                    current_value = getattr(profile, field, None)
                    if not current_value or self._should_update_field(field, current_value, value):
                        setattr(profile, field, value)
                        updated_fields[field] = value
                        
                        # Update confidence score
                        if not profile.confidence_scores:
                            profile.confidence_scores = {}
                        profile.confidence_scores[field] = 0.8  # Base confidence
            
            # Update timestamps
            profile.updated_at = datetime.now()
            profile.last_interaction = datetime.now()
            
            session.commit()
            
            self.logger.info(f"Updated profile for user {user_id}: {list(updated_fields.keys())}")
            return updated_fields
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error updating user profile: {e}")
            return {}
        finally:
            session.close()
    
    def _should_update_field(self, field: str, current_value: Any, new_value: Any) -> bool:
        """Determine if a field should be updated"""
        if field == 'age':
            # Only update age if new value is more recent or significantly different
            return abs(current_value - new_value) <= 2
        elif field in ['name', 'city', 'profession']:
            # Update if new value is more complete or different
            return len(str(new_value)) > len(str(current_value))
        else:
            # For other fields, always update
            return True
    
    async def get_user_profile(self, user_id: str) -> Optional[UserPersona]:
        """Get complete user profile"""
        session = self.SessionLocal()
        try:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if not profile:
                return None
            
            return UserPersona(
                user_id=profile.user_id,
                platform=profile.platform,
                name=profile.name,
                age=profile.age,
                city=profile.city,
                country=profile.country,
                profession=profile.profession,
                education=profile.education,
                background=profile.background,
                interests=profile.interests or [],
                personality_traits=profile.personality_traits or [],
                communication_style=profile.communication_style,
                language_preference=profile.language_preference,
                timezone=profile.timezone,
                relationship_status=profile.relationship_status,
                family=profile.family,
                goals=profile.goals or [],
                preferences=profile.preferences or {},
                confidence_scores=profile.confidence_scores or {},
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return None
        finally:
            session.close()
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 50,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get user conversation history"""
        async with asyncio.get_event_loop().run_in_executor(None, self.SessionLocal) as session:
            try:
                query = session.query(UserConversation).filter_by(user_id=user_id)
                
                if days_back:
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    query = query.filter(UserConversation.timestamp >= cutoff_date)
                
                conversations = query.order_by(UserConversation.timestamp.desc()).limit(limit).all()
                
                return [
                    {
                        'id': conv.id,
                        'message_type': conv.message_type,
                        'content': conv.content,
                        'persona_used': conv.persona_used,
                        'ai_provider': conv.ai_provider,
                        'task_type': conv.task_type,
                        'sentiment': conv.sentiment,
                        'topics': conv.topics,
                        'intent': conv.intent,
                        'timestamp': conv.timestamp,
                        'extracted_info': conv.extracted_info
                    }
                    for conv in conversations
                ]
                
            except Exception as e:
                self.logger.error(f"Error getting conversation history: {e}")
                return []
            finally:
                session.close()
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics and insights for a user"""
        async with asyncio.get_event_loop().run_in_executor(None, self.SessionLocal) as session:
            try:
                # Get basic stats
                total_messages = session.query(UserConversation).filter_by(
                    user_id=user_id, 
                    message_type="user_message"
                ).count()
                
                # Get conversation data
                conversations = session.query(UserConversation).filter_by(user_id=user_id).all()
                
                # Analyze patterns
                sentiment_counts = {}
                topic_counts = {}
                intent_counts = {}
                
                for conv in conversations:
                    # Sentiment analysis
                    sentiment = conv.sentiment or "neutral"
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                    
                    # Topic analysis
                    for topic in conv.topics or []:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    
                    # Intent analysis
                    intent = conv.intent or "chat"
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
                
                return {
                    'total_messages': total_messages,
                    'conversation_count': len(conversations),
                    'sentiment_distribution': sentiment_counts,
                    'top_topics': dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                    'intent_distribution': intent_counts,
                    'most_common_sentiment': max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "neutral",
                    'engagement_level': "high" if total_messages > 50 else "medium" if total_messages > 10 else "low"
                }
                
            except Exception as e:
                self.logger.error(f"Error getting user analytics: {e}")
                return {}
            finally:
                session.close()
    
    async def search_users(
        self,
        criteria: Dict[str, Any],
        limit: int = 100
    ) -> List[UserPersona]:
        """Search users by criteria"""
        async with asyncio.get_event_loop().run_in_executor(None, self.SessionLocal) as session:
            try:
                query = session.query(UserProfile)
                
                # Apply filters
                for field, value in criteria.items():
                    if hasattr(UserProfile, field):
                        query = query.filter(getattr(UserProfile, field) == value)
                
                profiles = query.limit(limit).all()
                
                return [
                    UserPersona(
                        user_id=profile.user_id,
                        platform=profile.platform,
                        name=profile.name,
                        age=profile.age,
                        city=profile.city,
                        country=profile.country,
                        profession=profile.profession,
                        education=profile.education,
                        background=profile.background,
                        interests=profile.interests or [],
                        personality_traits=profile.personality_traits or [],
                        communication_style=profile.communication_style,
                        language_preference=profile.language_preference,
                        timezone=profile.timezone,
                        relationship_status=profile.relationship_status,
                        family=profile.family,
                        goals=profile.goals or [],
                        preferences=profile.preferences or {},
                        confidence_scores=profile.confidence_scores or {},
                        created_at=profile.created_at,
                        updated_at=profile.updated_at
                    )
                    for profile in profiles
                ]
                
            except Exception as e:
                self.logger.error(f"Error searching users: {e}")
                return []
            finally:
                session.close()
    
    async def shutdown(self):
        """Cleanup resources"""
        try:
            self.engine.dispose()
            self.logger.info("User Profile Manager shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Export main classes
__all__ = ["UserProfileManager", "UserPersona", "UserProfile", "UserConversation"]
