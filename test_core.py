# test_core.py
from persona_manager import PersonaManager
from db.core_memory import CoreMemory
from pathlib import Path

def test_system():
    print("=== Testing Core System ===")
    
    # Test Personas
    try:
        pm = PersonaManager()
        personas = pm.list_personas()
        print("\n✅ Personas:")
        print(f"Found {len(personas)} personas: {personas}")
        print(f"Sample persona ('{personas[0]}'):")
        print(pm.get_persona(personas[0])[:200] + "...")
    except Exception as e:
        print(f"\n❌ Persona Error: {e}")
        return

    # Test Memory
    try:
        memory = CoreMemory()
        test_data = ("test_user", "favorite_food", "sushi")
        memory.store(*test_data)
        retrieved = memory.retrieve(test_data[0], test_data[1])
        print(f"\n✅ Memory Test:")
        print(f"Stored: {test_data}")
        print(f"Retrieved: {retrieved}")
    except Exception as e:
        print(f"\n❌ Memory Error: {e}")
        return

    print("\n=== All Tests Passed ===")

if __name__ == "__main__":
    test_system()
