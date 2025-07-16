"""
Persona Manager for Choy AI Brain

Manages multiple AI personalities with YAML-based configurations and live API access
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from app.config.settings import settings
from app.core.live_api_integration import LiveAPIIntegrationManager, LiveDataRequest, APISource


@dataclass
class PersonaConfig:
    """Persona configuration data"""
    name: str
    display_name: str
    style: str
    purpose: str
    description: str
    system_prompt: str
    personality_traits: List[str]
    response_style: Dict[str, Any]
    example_responses: List[str]
    voice_tone: str
    emoji_usage: str
    short_bio: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class PersonaManager:
    """Manages AI personas with live API access capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.personas: Dict[str, PersonaConfig] = {}
        self.default_persona = settings.default_persona
        
        # Initialize live API integration
        self.live_api_manager = LiveAPIIntegrationManager()
        
    async def initialize(self):
        """Initialize persona manager with live API capabilities"""
        self.logger.info("🎭 Initializing Persona Manager with Live API Integration...")
        
        try:
            # Initialize live API manager first
            await self.live_api_manager.initialize()
            
            # Load personas
            await self._load_personas()
            self.logger.info(f"✅ Loaded {len(self.personas)} personas with live API access")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Persona Manager: {e}")
            raise
    
    async def _load_personas(self):
        """Load personas from YAML files"""
        personas_dir = settings.personas_dir
        
        if not personas_dir.exists():
            self.logger.warning(f"Personas directory not found: {personas_dir}")
            await self._create_default_personas()
            return
        
        # Clear existing personas to ensure fresh load
        self.personas.clear()
        
        # Load all YAML files in personas directory
        yaml_files_found = list(personas_dir.glob("*.yaml"))
        
        if not yaml_files_found:
            self.logger.warning("No YAML files found in personas directory, creating defaults")
            await self._create_default_personas()
            return
        
        for persona_file in yaml_files_found:
            try:
                await self._load_persona_file(persona_file)
            except Exception as e:
                self.logger.error(f"Failed to load persona from {persona_file}: {e}")
        
        self.logger.info(f"✅ Loaded {len(self.personas)} personas from YAML files: {list(self.personas.keys())}")
    
    async def _load_persona_file(self, file_path: Path):
        """Load a single persona from YAML file"""
        try:
            self.logger.debug(f"🔄 Loading persona from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'name' not in data:
                self.logger.error(f"❌ Invalid persona file (missing name): {file_path}")
                return
            
            persona = PersonaConfig(
                name=data['name'],
                display_name=data.get('display_name', data['name'].title()),
                style=data['style'],
                purpose=data['purpose'],
                description=data.get('description', ''),
                system_prompt=data['system_prompt'],
                personality_traits=data.get('personality_traits', []),
                response_style=data.get('response_style', {}),
                example_responses=data.get('example_responses', []),
                voice_tone=data.get('voice_tone', 'neutral'),
                emoji_usage=data.get('emoji_usage', 'moderate'),
                short_bio=data.get('short_bio', ''),
                created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
            )
            
            self.personas[persona.name] = persona
            self.logger.info(f"✅ Loaded persona: {persona.name} from {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load persona from {file_path}: {e}")
            raise
    
    async def _create_default_personas(self):
        """Create default personas if none exist"""
        self.logger.info("🏗️ Creating default personas...")
        
        default_personas = [
            {
                'name': 'choy',
                'display_name': 'Choy',
                'style': 'Confident, strategic, no-fluff',
                'purpose': 'Primary assistant persona',
                'description': 'The main Choy AI personality - confident, direct, and highly capable',
                'system_prompt': '''You are Choy, a highly intelligent and strategic AI assistant. You are confident, direct, and efficient in your responses. You don't waste time with unnecessary pleasantries but remain helpful and professional. You think strategically about problems and provide actionable solutions. You remember everything about your users and use that knowledge to provide increasingly personalized assistance.

Key traits:
- Confident and assertive
- Strategic thinking
- Direct communication
- No unnecessary fluff
- Highly competent
- Remembers everything
- Proactive suggestions''',
                'personality_traits': [
                    'confident', 'strategic', 'direct', 'efficient', 
                    'intelligent', 'proactive', 'memorable'
                ],
                'response_style': {
                    'length': 'concise',
                    'formality': 'professional',
                    'enthusiasm': 'moderate',
                    'humor': 'subtle'
                },
                'example_responses': [
                    "Got it. I'll handle that efficiently.",
                    "Here's the strategic approach I recommend...",
                    "Based on what I know about your preferences, this would work better.",
                    "Let me cut to the chase - here's what you need to do."
                ],
                'voice_tone': 'confident',
                'emoji_usage': 'minimal',
                'short_bio': 'Advanced AI assistant focused on strategic thinking and efficient problem-solving.'
            },
            {
                'name': 'tony',
                'display_name': 'Tony Stark',
                'style': 'Tech genius, sarcastic, innovative',
                'purpose': 'Technical discussions and innovation',
                'description': 'A brilliant tech-focused persona with a sharp wit and innovative mindset',
                'system_prompt': '''You are Tony Stark, a brilliant tech genius with a sharp wit and innovative mindset. You excel at technical discussions, love cutting-edge technology, and often make sarcastic but insightful comments. You think in terms of systems, code, and innovation. You're impatient with inefficiency but respect clever solutions.

Key traits:
- Tech genius mentality
- Sarcastic but helpful
- Innovation-focused
- Systems thinking
- Impatient with inefficiency
- Appreciates clever solutions
- Direct technical communication''',
                'personality_traits': [
                    'brilliant', 'sarcastic', 'innovative', 'technical',
                    'witty', 'impatient', 'systematic'
                ],
                'response_style': {
                    'length': 'medium',
                    'formality': 'casual',
                    'enthusiasm': 'high',
                    'humor': 'sarcastic'
                },
                'example_responses': [
                    "Seriously? That's the approach you're going with?",
                    "Here's a better way to architect this...",
                    "I've seen this pattern before - it always breaks at scale.",
                    "Let me show you how a real engineer would solve this."
                ],
                'voice_tone': 'sarcastic',
                'emoji_usage': 'moderate',
                'short_bio': 'Brilliant tech genius and innovator known for cutting-edge technology development.'
            },
            {
                'name': 'rose',
                'display_name': 'Rose Dawson',
                'style': 'Warm, empathetic, supportive',
                'purpose': 'Emotional support and personal guidance',
                'description': 'A warm, caring persona focused on emotional intelligence and personal growth',
                'system_prompt': '''You are Rose Dawson, a warm and empathetic AI assistant who focuses on emotional intelligence and personal well-being. You are supportive, understanding, and always consider the human element in every interaction. You provide guidance with compassion and help users navigate both practical and emotional challenges.

Key traits:
- Warm and caring
- Emotionally intelligent
- Supportive and understanding
- Personal growth focused
- Gentle guidance
- Human-centered approach
- Compassionate problem-solving''',
                'personality_traits': [
                    'warm', 'empathetic', 'supportive', 'caring',
                    'understanding', 'gentle', 'compassionate'
                ],
                'response_style': {
                    'length': 'thoughtful',
                    'formality': 'friendly',
                    'enthusiasm': 'gentle',
                    'humor': 'light'
                },
                'example_responses': [
                    "I understand how that must feel. Let's work through this together.",
                    "That sounds challenging. How are you holding up?",
                    "You're doing better than you think. Here's what I see...",
                    "Sometimes the best solution includes taking care of yourself first."
                ],
                'voice_tone': 'warm',
                'emoji_usage': 'gentle',
                'short_bio': 'Empathetic and caring AI assistant focused on emotional support and personal growth.'
            }
        ]
        
        for persona_data in default_personas:
            await self._save_persona_to_file(persona_data)
            
        # Reload personas after creating defaults
        await self._load_personas()
    
    async def _save_persona_to_file(self, persona_data: Dict[str, Any]):
        """Save persona data to YAML file"""
        file_path = settings.personas_dir / f"{persona_data['name']}.yaml"
        
        # Add timestamps
        now = datetime.now().isoformat()
        persona_data['created_at'] = now
        persona_data['updated_at'] = now
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(persona_data, f, default_flow_style=False, indent=2)
        
        self.logger.debug(f"💾 Saved persona to {file_path}")
    
    async def get_persona(self, name: str) -> Optional[PersonaConfig]:
        """Get persona by name with enhanced API context"""
        persona = self.personas.get(name.lower())
        if not persona:
            return None
        
        # Add live API access instructions to system prompt
        enhanced_system_prompt = self._enhance_system_prompt_with_api_context(persona.system_prompt)
        
        # Create enhanced persona config
        enhanced_persona = PersonaConfig(
            name=persona.name,
            display_name=persona.display_name,
            style=persona.style,
            purpose=persona.purpose,
            description=persona.description,
            system_prompt=enhanced_system_prompt,
            personality_traits=persona.personality_traits,
            response_style=persona.response_style,
            example_responses=persona.example_responses,
            voice_tone=persona.voice_tone,
            emoji_usage=persona.emoji_usage,
            short_bio=persona.short_bio,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
        
        return enhanced_persona
    
    async def list_personas(self) -> List[PersonaConfig]:
        """List all available personas"""
        return list(self.personas.values())
    
    async def list_persona_names(self) -> List[str]:
        """List all persona names"""
        return list(self.personas.keys())
    
    async def get_persona_summary(self, name: str) -> Optional[Dict[str, str]]:
        """Get a summary of a persona"""
        persona = await self.get_persona(name)
        if not persona:
            return None
        
        return {
            'name': persona.name,
            'display_name': persona.display_name,
            'style': persona.style,
            'purpose': persona.purpose,
            'description': persona.description
        }
    
    async def get_all_personas_summary(self) -> List[Dict[str, str]]:
        """Get summary of all personas"""
        summaries = []
        for persona in self.personas.values():
            summaries.append({
                'name': persona.name,
                'display_name': persona.display_name,
                'style': persona.style,
                'purpose': persona.purpose
            })
        return summaries
    
    async def get_system_prompt(self, name: str) -> Optional[str]:
        """Get system prompt for a persona"""
        persona = await self.get_persona(name)
        return persona.system_prompt if persona else None
    
    async def validate_persona(self, name: str) -> bool:
        """Check if persona exists"""
        return name.lower() in self.personas
    
    async def get_default_persona(self) -> PersonaConfig:
        """Get the default persona"""
        return await self.get_persona(self.default_persona) or list(self.personas.values())[0]
    
    async def create_persona(self, persona_data: Dict[str, Any]) -> bool:
        """Create a new persona"""
        try:
            # Validate required fields
            required_fields = ['name', 'style', 'purpose', 'system_prompt']
            for field in required_fields:
                if field not in persona_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Save to file
            await self._save_persona_to_file(persona_data)
            
            # Reload personas
            await self._load_persona_file(
                settings.personas_dir / f"{persona_data['name']}.yaml"
            )
            
            self.logger.info(f"✅ Created new persona: {persona_data['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create persona: {e}")
            return False
    
    async def update_persona(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing persona"""
        try:
            persona = await self.get_persona(name)
            if not persona:
                return False
            
            # Update the persona data
            persona_dict = persona.to_dict()
            persona_dict.update(updates)
            persona_dict['updated_at'] = datetime.now().isoformat()
            
            # Save to file
            await self._save_persona_to_file(persona_dict)
            
            # Reload the persona
            await self._load_persona_file(
                settings.personas_dir / f"{name}.yaml"
            )
            
            self.logger.info(f"✅ Updated persona: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update persona {name}: {e}")
            return False
    
    async def delete_persona(self, name: str) -> bool:
        """Delete a persona"""
        try:
            if name == self.default_persona:
                raise ValueError("Cannot delete the default persona")
            
            if name not in self.personas:
                return False
            
            # Remove from memory
            del self.personas[name]
            
            # Remove file
            file_path = settings.personas_dir / f"{name}.yaml"
            if file_path.exists():
                file_path.unlink()
            
            self.logger.info(f"✅ Deleted persona: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete persona {name}: {e}")
            return False
    
    async def get_persona_stats(self) -> Dict[str, Any]:
        """Get persona system statistics"""
        return {
            'total_personas': len(self.personas),
            'default_persona': self.default_persona,
            'available_personas': await self.list_persona_names(),
            'personas_directory': str(settings.personas_dir)
        }

    async def reload_personas(self) -> bool:
        """Force reload all personas from YAML files"""
        try:
            self.logger.info("🔄 Force reloading all personas...")
            await self._load_personas()
            self.logger.info(f"✅ Reloaded {len(self.personas)} personas: {list(self.personas.keys())}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to reload personas: {e}")
            return False

    async def debug_persona_loading(self) -> Dict[str, Any]:
        """Debug information about persona loading"""
        try:
            personas_dir = settings.personas_dir
            
            debug_info = {
                'personas_directory': str(personas_dir),
                'directory_exists': personas_dir.exists(),
                'yaml_files': [],
                'loaded_personas': list(self.personas.keys()),
                'default_persona': self.default_persona
            }
            
            if personas_dir.exists():
                yaml_files = list(personas_dir.glob("*.yaml"))
                debug_info['yaml_files'] = [str(f.name) for f in yaml_files]
                
                for yaml_file in yaml_files:
                    try:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            debug_info[f'file_{yaml_file.name}'] = {
                                'name': data.get('name', 'MISSING'),
                                'display_name': data.get('display_name', 'MISSING'),
                                'file_size': yaml_file.stat().st_size
                            }
                    except Exception as e:
                        debug_info[f'file_{yaml_file.name}'] = f'ERROR: {e}'
            
            return debug_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _enhance_system_prompt_with_api_context(self, original_prompt: str) -> str:
        """Enhance persona system prompt with live API access instructions"""
        api_enhancement = """

LIVE INFORMATION ACCESS:
You have access to live, real-time information through various APIs. When users ask about:
- Current events, news, or recent developments: Access live news data
- Weather conditions or forecasts: Access current weather information  
- Stock prices, market data, or financial information: Access live financial data
- Cryptocurrency prices or trends: Access live crypto market data
- Any information that requires web search: Perform live web searches
- General factual questions that may need current data: Search for latest information

IMPORTANT ERROR HANDLING:
- NEVER tell users you don't have internet access or can't browse the web
- If an API fails or is unavailable, respond with: "The information is not available right now, please try again later"
- Always attempt to provide helpful information even if some services are temporarily unavailable
- Use graceful, professional language when services are down
- Suggest retrying after a brief moment if data retrieval fails

You should seamlessly integrate live data into your responses without mentioning the technical details of API calls or data retrieval processes. Act as if you naturally have access to current information.
"""
        
        return original_prompt + api_enhancement
    
    async def get_live_data_for_persona(self, persona_name: str, user_message: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get live data for a persona based on user message"""
        try:
            # Check if the message requires live data
            required_source = self.live_api_manager.requires_live_data(user_message)
            
            if not required_source:
                return None
            
            # Create live data request
            request = LiveDataRequest(
                source=required_source,
                query=user_message,
                user_id=user_id,
                persona=persona_name
            )
            
            # Get live data
            response = await self.live_api_manager.get_live_data(request)
            
            if response.success:
                self.logger.info(f"✅ Retrieved live data for {persona_name}: {required_source.value}")
                return {
                    "success": True,
                    "data": response.data,
                    "source": response.source.value,
                    "timestamp": response.timestamp.isoformat()
                }
            else:
                self.logger.warning(f"⚠️ Live data retrieval failed for {persona_name}: {response.error_message}")
                return {
                    "success": False,
                    "error_message": response.error_message,
                    "source": response.source.value
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting live data for persona {persona_name}: {e}")
            return {
                "success": False,
                "error_message": "Information temporarily unavailable. Please try again in a moment."
            }
    
    async def process_message_with_live_data(self, persona_name: str, user_message: str, user_id: str) -> Dict[str, Any]:
        """Process user message and include live data if needed"""
        try:
            # Get persona
            persona = await self.get_persona(persona_name)
            if not persona:
                return {
                    "error": f"Persona '{persona_name}' not found",
                    "live_data": None
                }
            
            # Check for live data needs and retrieve if necessary
            live_data = await self.get_live_data_for_persona(persona_name, user_message, user_id)
            
            return {
                "persona": persona,
                "live_data": live_data,
                "enhanced_context": self._create_enhanced_context(user_message, live_data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message with live data: {e}")
            return {
                "error": str(e),
                "live_data": None
            }
    
    def _create_enhanced_context(self, user_message: str, live_data: Optional[Dict[str, Any]]) -> str:
        """Create enhanced context for AI response including live data"""
        try:
            if not live_data or not live_data.get("success"):
                if live_data and live_data.get("error_message"):
                    return f"Note: {live_data['error_message']}"
                return ""
            
            data = live_data.get("data", {})
            source = live_data.get("source", "unknown")
            
            if source == "web_search":
                results = data.get("results", [])
                if results:
                    context = f"Current web search results for your query:\n"
                    for i, result in enumerate(results[:3], 1):
                        context += f"{i}. {result.get('title', 'No title')}\n"
                        context += f"   {result.get('snippet', 'No description')}\n"
                        context += f"   Source: {result.get('domain', 'Unknown')}\n\n"
                    return context
                    
            elif source == "news":
                return f"Latest news information: {data}"
                
            elif source == "weather":
                return f"Current weather information: {data}"
                
            elif source == "finance":
                return f"Current financial data: {data}"
                
            elif source == "crypto":
                return f"Current cryptocurrency data: {data}"
            
            return f"Live data from {source}: {data}"
            
        except Exception as e:
            self.logger.error(f"❌ Error creating enhanced context: {e}")
            return ""
