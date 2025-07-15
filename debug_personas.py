#!/usr/bin/env python3
"""
Debug script to check persona loading on VPS
Run this to diagnose persona loading issues
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from app.modules.personas.persona_manager import PersonaManager
from app.config.settings import settings

async def debug_personas():
    """Debug persona loading"""
    print("🔍 Debugging Persona Loading...")
    print("=" * 50)
    
    try:
        # Initialize persona manager
        persona_manager = PersonaManager()
        await persona_manager.initialize()
        
        # Get debug information
        debug_info = await persona_manager.debug_persona_loading()
        
        print(f"📁 Personas Directory: {debug_info['personas_directory']}")
        print(f"📂 Directory Exists: {debug_info['directory_exists']}")
        print(f"📄 YAML Files Found: {debug_info['yaml_files']}")
        print(f"🎭 Loaded Personas: {debug_info['loaded_personas']}")
        print(f"⭐ Default Persona: {debug_info['default_persona']}")
        
        print("\n📋 File Details:")
        for key, value in debug_info.items():
            if key.startswith('file_'):
                print(f"  {key}: {value}")
        
        # Try to get each persona
        print("\n🔍 Persona Validation:")
        for persona_name in ['choy', 'tony', 'rose']:
            persona = await persona_manager.get_persona(persona_name)
            if persona:
                print(f"  ✅ {persona_name}: {persona.display_name} - {persona.style}")
            else:
                print(f"  ❌ {persona_name}: NOT FOUND")
        
        # List all available personas
        available_personas = await persona_manager.list_persona_names()
        print(f"\n🎭 All Available Personas: {available_personas}")
        
        # Force reload test
        print("\n🔄 Testing Force Reload...")
        reload_success = await persona_manager.reload_personas()
        print(f"  Reload Success: {reload_success}")
        
        # Check again after reload
        available_after_reload = await persona_manager.list_persona_names()
        print(f"  Available After Reload: {available_after_reload}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_personas())
