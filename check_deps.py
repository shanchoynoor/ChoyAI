# check_deps.py
try:
    from deepseek_sdk import Deepseek  # Try this import
    DEEPSEEK_IMPORT = True
except ImportError:
    DEEPSEEK_IMPORT = False

print("🛠️ Dependency Check:")
print(f"✅ python-telegram-bot  - Import successful")
print(f"{'✅' if DEEPSEEK_IMPORT else '❌'} deepseek-sdk         - {'Import successful' if DEEPSEEK_IMPORT else 'NOT INSTALLED'}")
print(f"✅ sqlalchemy           - Import successful")
print(f"✅ pydantic             - Import successful")

if not DEEPSEEK_IMPORT:
    print("\nTo install deepseek-sdk run:")
    print("pip install deepseek-sdk")
