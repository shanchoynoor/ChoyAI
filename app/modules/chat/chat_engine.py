"""
Chat Engine for Choy AI Brain

Orchestrates conversation processing with memory and persona integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.modules.memory.core_memory import CoreMemoryManager
from app.modules.memory.user_memory import UserMemoryManager
from app.modules.memory.conversation_memory import ConversationMemoryManager
from app.modules.personas.persona_manager import PersonaManager
from app.core.ai_providers import AIProviderManager, AIMessage, TaskType
from app.config.settings import settings


class ChatEngine:
    """Central chat processing engine"""
    
    def __init__(
        self,
        core_memory: CoreMemoryManager,
        user_memory: UserMemoryManager,
        conversation_memory: ConversationMemoryManager,
        persona_manager: PersonaManager,
        ai_provider_manager: Optional[AIProviderManager] = None,
        rag_engine: Optional[Any] = None,  # Import type hint would create circular dependency
        productivity_manager: Optional[Any] = None  # Import type hint would create circular dependency
    ):
        self.logger = logging.getLogger(__name__)
        
        # Memory systems
        self.core_memory = core_memory
        self.user_memory = user_memory
        self.conversation_memory = conversation_memory
        self.persona_manager = persona_manager
        
        # AI Provider Manager
        self.ai_provider_manager = ai_provider_manager
        
        # RAG Engine for enhanced context
        self.rag_engine = rag_engine
        
        # Productivity Manager for live information access
        self.productivity_manager = productivity_manager
        
        # Active conversations cache
        self.active_conversations: Dict[str, int] = {}
        
    async def initialize(self):
        """Initialize chat engine"""
        self.logger.info("💭 Initializing Chat Engine...")
        
        try:
            # AI Provider Manager should be initialized externally
            if not self.ai_provider_manager:
                self.logger.warning("No AI Provider Manager provided - creating default")
                from app.core.ai_providers import AIProviderManager
                self.ai_provider_manager = AIProviderManager()
                await self.ai_provider_manager.initialize()
            
            self.logger.info("✅ Chat Engine initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Chat Engine: {e}")
            raise
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_context: Any,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a user message and generate AI response
        
        Args:
            user_id: User identifier
            message: User message text
            conversation_context: Conversation context object
            additional_context: Additional context data
            
        Returns:
            Generated AI response
        """
        try:
            # Get or create conversation
            conversation_id = await self._get_or_create_conversation(
                user_id=user_id,
                platform=conversation_context.platform,
                persona=conversation_context.persona
            )
            
            # Log user message
            await self.conversation_memory.log_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=message,
                metadata=additional_context
            )
            
            # Get user information and memories
            user_info = await self.user_memory.get_or_create_user(user_id)
            user_memories = await self.user_memory.get_memories(user_id, limit=20)
            
            # Get conversation history
            conversation_history = await self.conversation_memory.get_conversation_history(
                user_id=user_id,
                platform=conversation_context.platform,
                limit=settings.max_conversation_history
            )
            
            # Get persona
            persona = await self.persona_manager.get_persona(conversation_context.persona)
            if not persona:
                persona = await self.persona_manager.get_default_persona()
            
            # Build context for AI
            ai_context = await self._build_ai_context(
                user_info=user_info,
                user_memories=user_memories,
                conversation_history=conversation_history,
                persona=persona,
                current_message=message,
                additional_context=additional_context
            )
            
            # Check if live data was already provided via additional_context
            live_info = additional_context.get("live_data_context") if additional_context else None
            
            # If no live data provided, try to detect and fetch
            if not live_info:
                live_info = await self._detect_and_fetch_live_info(message, user_id)
            
            if live_info:
                ai_context['live_info'] = live_info
                self.logger.debug(f"🌐 Added live information to context for user {user_id}")

            # Generate AI response with enhanced context
            response = await self._generate_ai_response(
                context=ai_context,
                persona=persona,
                user_message=message,
                live_data=additional_context.get("live_data") if additional_context else None
            )
            
            # Log AI response
            await self.conversation_memory.log_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=response,
                persona=persona.name
            )
            
            # Extract and save any new memories from the conversation
            await self._extract_and_save_memories(user_id, message, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message for user {user_id}: {e}")
            return "I apologize, but I encountered an error processing your message. Please try again."
    
    async def _get_or_create_conversation(
        self,
        user_id: str,
        platform: str,
        persona: str
    ) -> int:
        """Get or create conversation ID"""
        conversation_key = f"{platform}_{user_id}"
        
        if conversation_key in self.active_conversations:
            return self.active_conversations[conversation_key]
        
        # Check for existing active conversation
        active_conv = await self.conversation_memory.get_active_conversation(
            user_id=user_id,
            platform=platform
        )
        
        if active_conv:
            conversation_id = active_conv['id']
        else:
            # Create new conversation
            conversation_id = await self.conversation_memory.start_conversation(
                user_id=user_id,
                platform=platform,
                session_id=conversation_key,
                persona=persona
            )
        
        # Cache the conversation ID
        self.active_conversations[conversation_key] = conversation_id
        
        return conversation_id
    
    async def _build_ai_context(
        self,
        user_info: Dict[str, Any],
        user_memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        persona: Any,
        current_message: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive context for AI with RAG enhancement"""
        
        # Format user information
        user_context = {
            "name": f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
            "username": user_info.get('username', ''),
            "bio": user_info.get('bio', 'Not provided'),
            "preferred_persona": user_info.get('preferred_persona', 'choy'),
            "member_since": user_info.get('created_at', 'Unknown')
        }
        
        # Format memories
        formatted_memories = []
        for memory in user_memories[:10]:  # Limit to most important memories
            memory_text = f"{memory['key']}: {memory['value']}"
            if memory.get('context'):
                memory_text += f" (Context: {memory['context']})"
            formatted_memories.append(memory_text)
        
        # Format recent conversation
        recent_messages = []
        for msg in conversation_history[:10]:  # Last 10 messages
            role = "User" if msg['message_type'] == 'user' else "AI"
            recent_messages.append(f"{role}: {msg['content']}")
        
        # Enhanced context with RAG if available
        rag_context = {}
        if self.rag_engine:
            try:
                # Get RAG-enhanced context for the current message
                user_id = user_info.get('user_id', 'unknown')
                enhanced_prompt, context_data = await self.rag_engine.enhance_prompt_with_context(
                    original_prompt=current_message,
                    user_id=user_id,
                    context_types=["conversation_rag", "knowledge", "core_facts", "user_memory"],
                    max_context_length=1200
                )
                
                rag_context = {
                    "enhanced_available": True,
                    "context_types": list(context_data.get("contexts", {}).keys()),
                    "relevance_scores": context_data.get("relevance_scores", {}),
                    "enhanced_prompt": enhanced_prompt
                }
                
                # Index current conversation for future RAG retrieval
                full_conversation = "\n".join([
                    f"User: {current_message}"
                ] + recent_messages[-3:])  # Include some recent context
                
                await self.rag_engine.index_conversation(
                    user_id=user_id,
                    conversation_text=full_conversation,
                    metadata={
                        "persona": persona.name,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            except Exception as e:
                self.logger.warning(f"⚠️ RAG enhancement failed: {e}")
                rag_context = {"enhanced_available": False, "error": str(e)}
        else:
            rag_context = {"enhanced_available": False, "reason": "RAG engine not initialized"}
        
        return {
            "user_context": user_context,
            "memories": formatted_memories,
            "recent_conversation": recent_messages,
            "current_message": current_message,
            "rag_context": rag_context,
            "persona": {
                "name": persona.name,
                "style": persona.style,
                "purpose": persona.purpose
            }
        }
    
    async def _detect_and_fetch_live_info(self, user_message: str, user_id: str) -> Optional[str]:
        """Detect if user message requires live information and fetch it"""
        if not self.productivity_manager:
            return None
            
        try:
            # Keywords that indicate need for live information
            live_info_keywords = {
                'weather': ['weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny', 'cloudy'],
                'news': ['news', 'latest', 'current events', 'breaking', 'happening now', 'today'],
                'search': ['search', 'find', 'look up', 'google', 'information about'],
                'finance': ['stock', 'price', 'market', 'crypto', 'bitcoin', 'trading', 'shares'],
                'maps': ['location', 'address', 'directions', 'map', 'where is', 'distance'],
                'time': ['time', 'date', 'today', 'current time', 'what day'],
                'trends': ['trending', 'popular', 'viral', 'social media trends']
            }
            
            message_lower = user_message.lower()
            
            # Check for weather requests
            if any(keyword in message_lower for keyword in live_info_keywords['weather']):
                # Extract location if possible
                location = self._extract_location_from_message(message_lower)
                if not location:
                    location = "current location"  # Default
                
                from app.modules.productivity import ModuleRequest, ModuleType
                request = ModuleRequest(
                    user_id=user_id,
                    module_type=ModuleType.ONLINE_AGENT,
                    action="get_weather",
                    data={"location": location}
                )
                
                response = await self.productivity_manager.process_request(request)
                if response.success:
                    return self._format_weather_info(response.data)
            
            # Check for news requests
            elif any(keyword in message_lower for keyword in live_info_keywords['news']):
                query = self._extract_news_query(message_lower)
                
                from app.modules.productivity import ModuleRequest, ModuleType
                request = ModuleRequest(
                    user_id=user_id,
                    module_type=ModuleType.ONLINE_AGENT,
                    action="get_news",
                    data={"query": query}
                )
                
                response = await self.productivity_manager.process_request(request)
                if response.success:
                    return self._format_news_info(response.data)
            
            # Check for general search requests
            elif any(keyword in message_lower for keyword in live_info_keywords['search']):
                search_query = self._extract_search_query(user_message)
                
                from app.modules.productivity import ModuleRequest, ModuleType
                request = ModuleRequest(
                    user_id=user_id,
                    module_type=ModuleType.ONLINE_AGENT,
                    action="web_search",
                    data={"query": search_query, "num_results": 3}
                )
                
                response = await self.productivity_manager.process_request(request)
                if response.success:
                    return self._format_search_results(response.data)
            
            # Check for financial information
            elif any(keyword in message_lower for keyword in live_info_keywords['finance']):
                symbol = self._extract_financial_symbol(message_lower)
                if symbol:
                    from app.modules.productivity import ModuleRequest, ModuleType
                    request = ModuleRequest(
                        user_id=user_id,
                        module_type=ModuleType.ONLINE_AGENT,
                        action="get_finance",
                        data={"symbol": symbol}
                    )
                    
                    response = await self.productivity_manager.process_request(request)
                    if response.success:
                        return self._format_finance_info(response.data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching live information: {e}")
            return None
    
    def _extract_location_from_message(self, message: str) -> Optional[str]:
        """Extract location from user message"""
        # Simple extraction - could be enhanced with NLP
        location_indicators = ['in ', 'at ', 'for ', 'weather in ', 'weather for ']
        for indicator in location_indicators:
            if indicator in message:
                parts = message.split(indicator, 1)
                if len(parts) > 1:
                    location = parts[1].split()[0:3]  # Take up to 3 words
                    return ' '.join(location).strip('.,!?')
        return None
    
    def _extract_news_query(self, message: str) -> str:
        """Extract news query from message"""
        # Remove common news keywords and extract the topic
        news_words = ['news', 'latest', 'current events', 'breaking', 'about']
        query = message
        for word in news_words:
            query = query.replace(word, '').strip()
        return query or "latest news"
    
    def _extract_search_query(self, message: str) -> str:
        """Extract search query from message"""
        # Remove search keywords
        search_words = ['search', 'find', 'look up', 'google', 'information about']
        query = message
        for word in search_words:
            query = query.replace(word, '').strip()
        return query or message
    
    def _extract_financial_symbol(self, message: str) -> Optional[str]:
        """Extract financial symbol from message"""
        # Look for common stock symbols or crypto names
        common_symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN', 'BTC', 'ETH', 'bitcoin', 'ethereum']
        words = message.upper().split()
        for word in words:
            if word in [s.upper() for s in common_symbols]:
                return word
        return None
    
    def _format_weather_info(self, weather_data: Dict[str, Any]) -> str:
        """Format weather information for AI context"""
        if not weather_data:
            return "Weather information is not available."
        
        current = weather_data.get('current', {})
        location = weather_data.get('location', 'Unknown location')
        
        info = f"Current weather for {location}:\n"
        info += f"Temperature: {current.get('temperature_c', 'N/A')}°C ({current.get('temperature_f', 'N/A')}°F)\n"
        info += f"Condition: {current.get('condition', 'N/A')}\n"
        info += f"Humidity: {current.get('humidity', 'N/A')}%\n"
        info += f"Wind: {current.get('wind_speed_kph', 'N/A')} km/h\n"
        
        return info
    
    def _format_news_info(self, news_data: Dict[str, Any]) -> str:
        """Format news information for AI context"""
        if not news_data or not news_data.get('articles'):
            return "No recent news found."
        
        articles = news_data.get('articles', [])[:3]  # Top 3 articles
        info = "Latest news:\n"
        
        for i, article in enumerate(articles, 1):
            info += f"{i}. {article.get('headline', 'No title')}\n"
            info += f"   {article.get('summary', 'No summary')}\n"
            info += f"   Source: {article.get('source', 'Unknown')}\n\n"
        
        return info
    
    def _format_search_results(self, search_data: Dict[str, Any]) -> str:
        """Format search results for AI context"""
        if not search_data or not search_data.get('results'):
            return "No search results found."
        
        results = search_data.get('results', [])[:3]  # Top 3 results
        query = search_data.get('query', 'search')
        
        info = f"Search results for '{query}':\n"
        
        for i, result in enumerate(results, 1):
            info += f"{i}. {result.get('title', 'No title')}\n"
            info += f"   {result.get('snippet', 'No description')}\n"
            info += f"   URL: {result.get('url', 'No URL')}\n\n"
        
        return info
    
    def _format_finance_info(self, finance_data: Dict[str, Any]) -> str:
        """Format financial information for AI context"""
        if not finance_data:
            return "Financial information is not available."
        
        symbol = finance_data.get('symbol', 'Unknown')
        info = f"Financial information for {symbol}:\n"
        
        # Check if there's an answer box with current price
        answer_box = finance_data.get('answer_box')
        if answer_box:
            info += f"Current data: {answer_box}\n"
        
        # Include search results for additional context
        search_results = finance_data.get('search_results', [])
        if search_results:
            info += "Recent market information:\n"
            for result in search_results[:2]:
                info += f"- {result.get('snippet', 'No information')}\n"
        
        return info

    async def _generate_ai_response(
        self,
        context: Dict[str, Any],
        persona: Any,
        user_message: str,
        live_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response with live data integration and graceful error handling"""
        
        # Build system prompt with live data instructions
        system_prompt = self._build_system_prompt(context, persona, live_data)
        
        # Prepare conversation history for API
        ai_messages = []
        ai_messages.append(AIMessage(role="system", content=system_prompt))
        
        # Add recent conversation context
        for msg_text in context["recent_conversation"][-5:]:  # Last 5 messages
            if msg_text.startswith("User: "):
                ai_messages.append(AIMessage(role="user", content=msg_text[6:]))
            elif msg_text.startswith("AI: "):
                ai_messages.append(AIMessage(role="assistant", content=msg_text[4:]))
        
        # Add live information context if available
        if context.get("live_info"):
            live_context_msg = f"[LIVE INFORMATION CONTEXT]: {context['live_info']}"
            ai_messages.append(AIMessage(role="user", content=live_context_msg))
        
        # Handle API errors gracefully - if live data failed, include graceful message
        if live_data and not live_data.get("success"):
            graceful_msg = live_data.get("error_message", "Some information is temporarily unavailable.")
            error_context = f"[SYSTEM NOTE]: {graceful_msg} Please respond naturally without mentioning technical limitations."
            ai_messages.append(AIMessage(role="user", content=error_context))
        
        # Add current message
        ai_messages.append(AIMessage(role="user", content=user_message))

        try:
            # Determine task type based on message content and persona
            task_type = self._determine_task_type(user_message, persona)
            
            # Generate response using AI Provider Manager
            response = await self.ai_provider_manager.chat_completion(
                messages=ai_messages,
                task_type=task_type,
                temperature=persona.response_style.get("temperature", 0.7),
                max_tokens=min(settings.max_response_length, 4000)
            )
            
            if response.content:
                ai_response = response.content.strip()
                
                # Apply persona-specific post-processing
                ai_response = self._apply_persona_style(ai_response, persona)
                
                # Log which provider was used
                self.logger.info(f"✅ Response generated using {response.provider} ({response.model})")
                
                return ai_response
            else:
                error_msg = response.error or "No response content generated"
                raise Exception(error_msg)
        
        except Exception as e:
            self.logger.error(f"❌ Error generating AI response: {e}")
            
            # Use graceful error messages based on persona
            if persona.name.lower() == "tony":
                return "The systems are acting up right now. Give me a moment to sort this out."
            elif persona.name.lower() == "rose":
                return "I'm having a little trouble accessing some information right now, but I'm here to help in any way I can."
            else:  # Default Choy response
                return "I'm experiencing some technical difficulties at the moment. Let me try again shortly."
    
    def _determine_task_type(self, message: str, persona: Any) -> TaskType:
        """Determine the appropriate task type based on message content and persona"""
        message_lower = message.lower()
        
        # Emotional support keywords
        if any(word in message_lower for word in ["sad", "depressed", "anxious", "worried", "upset", "feel", "emotion"]):
            return TaskType.EMOTIONAL_SUPPORT
        
        # Technical/coding keywords
        if any(word in message_lower for word in ["code", "programming", "function", "algorithm", "debug", "error", "python", "javascript"]):
            return TaskType.TECHNICAL
            
        # Creative writing keywords
        if any(word in message_lower for word in ["story", "write", "creative", "poem", "fiction", "character"]):
            return TaskType.CREATIVE
            
        # Analysis keywords
        if any(word in message_lower for word in ["analyze", "analysis", "compare", "evaluate", "review", "assess"]):
            return TaskType.ANALYSIS
            
        # Research keywords
        if any(word in message_lower for word in ["research", "information", "fact", "explain", "learn", "study"]):
            return TaskType.RESEARCH
            
        # Problem solving keywords
        if any(word in message_lower for word in ["problem", "solve", "solution", "help", "fix", "issue"]):
            return TaskType.PROBLEM_SOLVING
            
        # Summarization keywords
        if any(word in message_lower for word in ["summarize", "summary", "brief", "overview", "tldr"]):
            return TaskType.SUMMARIZATION
            
        # Translation keywords
        if any(word in message_lower for word in ["translate", "translation", "language"]):
            return TaskType.TRANSLATION
        
        # Default to conversation
        return TaskType.CONVERSATION
    
    def _build_system_prompt(self, context: Dict[str, Any], persona: Any, live_data: Optional[Dict[str, Any]] = None) -> str:
        """Build comprehensive system prompt with user profile and live data capabilities"""
        
        user_ctx = context["user_context"]
        memories = context["memories"]
        user_profile = context.get("user_profile")
        
        # Start with the core persona prompt (which already includes live API instructions)
        prompt = f"""{persona.system_prompt}

PERSONA BIOGRAPHICAL INFORMATION:
{persona.short_bio if persona.short_bio else 'No biographical information available.'}

DEVELOPER INFORMATION:
- You were created by Shanchoy Noor (known as Choy)
- Choy is a UI/UX Designer & Video Editor from Bangladesh
- He founded Choy Agency Ltd with 30+ team members
- Choy has 8+ years of experience in design, AI, and automation
- He manages social media for YouTube Village Park, AroundMeBD, and Village Grandpa's Cooking
- Choy developed this AI system to be a personal assistant with memory and multiple personalities
- If asked about your creator, developer, or who made you, refer to this information

CRITICAL RESPONSE REQUIREMENTS:
- Response style: {persona.response_style.get('length', 'concise')} length
- Voice tone: {persona.voice_tone}
- Emoji usage: {persona.emoji_usage}
- NO theatrical descriptions (no "leans back", "checks watch", "pulls up", etc.)
- NO unnecessary actions or gestures
- Stay in character as {persona.name} but be direct and focused
- Answer the question directly without excessive context
- If asked about your personal history, background, past, or life experiences, refer to the biographical information above

USER INFO:
- Name: {user_ctx['name'] or 'User'}
- Username: @{user_ctx['username'] or 'Unknown'}"""

        # Add only essential user profile information
        if user_profile:
            essential_info = []
            if user_profile.city:
                essential_info.append(f"Location: {user_profile.city}")
            if user_profile.profession:
                essential_info.append(f"Profession: {user_profile.profession}")
            if user_profile.interests:
                essential_info.append(f"Interests: {', '.join(user_profile.interests[:3])}")  # Only top 3
            
            if essential_info:
                prompt += f"\n- " + "\n- ".join(essential_info)

        # Add only the most important memories (limit to 5)
        if memories:
            important_memories = memories[:5]
            prompt += f"\n\nKEY MEMORIES:\n"
            for memory in important_memories:
                prompt += f"- {memory}\n"
        
        # Add live data context if available
        if live_data and live_data.get("success"):
            prompt += f"\n\nLIVE DATA AVAILABLE:\n"
            data_source = live_data.get("source", "unknown")
            prompt += f"- Current {data_source} information has been retrieved\n"
            prompt += f"- Use this information naturally in your response\n"
            prompt += f"- Don't mention technical details about data retrieval\n"
        
        prompt += f"""
RESPONSE RULES:
1. Be {persona.style.lower()}
2. Answer directly and precisely
3. No dramatic narration or role-playing actions
4. Keep responses focused on the user's actual question
5. Use persona traits: {', '.join(persona.personality_traits[:4])}
6. Maximum {settings.max_response_length} characters
7. NEVER mention internet access limitations or API failures
8. If information is unavailable, respond professionally: "That information isn't available right now"
"""
        
        return prompt.strip()
    
    def _apply_persona_style(self, response: str, persona: Any) -> str:
        """Apply persona-specific styling to response"""
        
        # Remove common theatrical elements that shouldn't be there
        theatrical_patterns = [
            r'\*[^*]*\*',  # Remove *actions*
            r'leans? (?:back|forward|in)',
            r'(?:checks?|glances? at) (?:watch|clock|time)',
            r'pulls? up (?:holographic|virtual|digital)',
            r'(?:adjusts?|straightens?) (?:tie|collar|glasses)',
            r'(?:smiles?|grins?|chuckles?|laughs?) (?:slightly|softly|quietly)',
            r'(?:in virtual|in digital) (?:chair|space|reality)',
            r'(?:fingers? )?steepled?',
            r'(?:looks?|gazes?) (?:thoughtfully|contemplatively)',
            r'(?:taps?|drums?) (?:fingers?|desk)',
            r'(?:raises?|arches?) (?:eyebrow|brow)',
        ]
        
        import re
        
        # Remove theatrical descriptions
        for pattern in theatrical_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and line breaks
        response = re.sub(r'\s+', ' ', response).strip()
        response = re.sub(r'\n\s*\n', '\n\n', response)  # Fix multiple line breaks
        
        # Apply persona-specific adjustments
        if persona.emoji_usage == "minimal":
            # Limit to 1-2 emojis max and only at the end
            emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
            emojis = re.findall(emoji_pattern, response)
            if len(emojis) > 2:
                # Remove excess emojis, keep only last 1-2
                for emoji in emojis[:-1]:
                    response = response.replace(emoji, '', 1)
        
        # Apply length requirements based on persona style
        response_length = persona.response_style.get('length', 'medium')
        if response_length == 'concise':
            # For concise responses, limit to 300 characters unless user specifically asks for details
            if len(response) > 300:
                sentences = response.split('. ')
                truncated = sentences[0]
                for sentence in sentences[1:]:
                    if len(truncated + '. ' + sentence) <= 280:
                        truncated += '. ' + sentence
                    else:
                        break
                response = truncated + ('.' if not truncated.endswith('.') else '')
        
        # Ensure response isn't too long overall
        if len(response) > settings.max_response_length:
            response = response[:settings.max_response_length - 3] + "..."
        
        return response.strip()
    
    async def _extract_and_save_memories(
        self,
        user_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """Extract and save important information as memories"""
        # This is a simplified version - could be enhanced with NLP
        
        # Look for explicit information sharing patterns
        memory_patterns = [
            ("my name is", "name"),
            ("i am", "identity"),
            ("i work", "work"),
            ("i live", "location"),
            ("my favorite", "preference"),
            ("i like", "preference"),
            ("i don't like", "preference"),
            ("i hate", "preference"),
            ("my birthday", "birthday"),
            ("i was born", "birthday"),
        ]
        
        user_message_lower = user_message.lower()
        
        for pattern, category in memory_patterns:
            if pattern in user_message_lower:
                # Extract the relevant information
                start_idx = user_message_lower.find(pattern)
                if start_idx != -1:
                    # Get the sentence containing this information
                    sentences = user_message.split('.')
                    for sentence in sentences:
                        if pattern in sentence.lower():
                            # Save as memory
                            key = f"auto_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            await self.user_memory.save_memory(
                                user_id=user_id,
                                key=key,
                                value=sentence.strip(),
                                context=f"Auto-extracted from conversation",
                                category=category,
                                importance=2
                            )
                            break
                break
    
    async def shutdown(self):
        """Shutdown chat engine"""
        # Note: Provider cleanup is handled by the AI Engine
        self.logger.info("💭 Chat Engine shutdown complete")


# Export the main class
__all__ = ["ChatEngine"]
