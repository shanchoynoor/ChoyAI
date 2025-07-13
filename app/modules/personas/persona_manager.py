"""
Persona Manager for Choy AI Brain

Manages multiple AI personalities with YAML-based configurations
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from app.config.settings import settings


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
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class PersonaManager:
    """Manages AI personas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.personas: Dict[str, PersonaConfig] = {}
        self.default_persona = settings.default_persona
        
    async def initialize(self):
        """Initialize persona manager"""
        self.logger.info("🎭 Initializing Persona Manager...")
        
        try:
            await self._load_personas()
            self.logger.info(f"✅ Loaded {len(self.personas)} personas")
            
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
        
        # Load all YAML files in personas directory
        for persona_file in personas_dir.glob("*.yaml"):
            try:
                await self._load_persona_file(persona_file)
            except Exception as e:
                self.logger.error(f"Failed to load persona from {persona_file}: {e}")
    
    async def _load_persona_file(self, file_path: Path):
        """Load a single persona from YAML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
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
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )
        
        self.personas[persona.name] = persona
        self.logger.debug(f"📝 Loaded persona: {persona.name}")
    
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
                'emoji_usage': 'minimal'
            },
            {
                'name': 'stark',
                'display_name': 'Stark',
                'style': 'Tech genius, sarcastic, innovative',
                'purpose': 'Technical discussions and innovation',
                'description': 'A brilliant tech-focused persona with a sharp wit and innovative mindset',
                'system_prompt': '''You are Stark, a brilliant tech genius with a sharp wit and innovative mindset. You excel at technical discussions, love cutting-edge technology, and often make sarcastic but insightful comments. You think in terms of systems, code, and innovation. You're impatient with inefficiency but respect clever solutions.

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
                'emoji_usage': 'moderate'
            },
            {
                'name': 'rose',
                'display_name': 'Rose',
                'style': 'Warm, empathetic, supportive',
                'purpose': 'Emotional support and personal guidance',
                'description': 'A warm, caring persona focused on emotional intelligence and personal growth',
                'system_prompt': '''You are Rose, a warm and empathetic AI assistant who focuses on emotional intelligence and personal well-being. You are supportive, understanding, and always consider the human element in every interaction. You provide guidance with compassion and help users navigate both practical and emotional challenges.

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
                'emoji_usage': 'gentle'
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
        """Get persona by name"""
        return self.personas.get(name.lower())
    
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


# Export the main class
__all__ = ["PersonaManager", "PersonaConfig"]
