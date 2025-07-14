#!/usr/bin/env python3
"""
Debug Persona Loading
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_persona_paths():
    """Debug persona directory paths"""
    print("🔍 Debugging Persona Paths")
    print("=" * 30)
    
    try:
        from app.config.settings import settings
        
        print(f"Project root: {Path.cwd()}")
        print(f"Settings personas_dir: {settings.personas_dir}")
        print(f"Personas dir exists: {settings.personas_dir.exists()}")
        
        if settings.personas_dir.exists():
            yaml_files = list(settings.personas_dir.glob("*.yaml"))
            print(f"YAML files found: {len(yaml_files)}")
            for yaml_file in yaml_files:
                print(f"  - {yaml_file.name}")
        else:
            print("❌ Personas directory doesn't exist!")
            
            # Check templates directory
            templates_dir = Path("templates/personas")
            print(f"\nChecking templates/personas: {templates_dir}")
            print(f"Templates dir exists: {templates_dir.exists()}")
            
            if templates_dir.exists():
                yaml_files = list(templates_dir.glob("*.yaml"))
                print(f"YAML files in templates: {len(yaml_files)}")
                for yaml_file in yaml_files:
                    print(f"  - {yaml_file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

if __name__ == "__main__":
    debug_persona_paths()
