# check_deps.py

def check_import(pkg_name, import_stmt):
    try:
        exec(import_stmt, globals())
        return True
    except ImportError:
        return False

print("🛠️ Dependency Check:")

# Check python-telegram-bot
telegram_ok = check_import("python-telegram-bot", "import telegram")
print(f"{'✅' if telegram_ok else '❌'} python-telegram-bot  - {'Import successful' if telegram_ok else 'NOT INSTALLED'}")

# Check deepseek-sdk
deepseek_ok = check_import("deepseek-sdk", "from deepseek_sdk import Deepseek")
print(f"{'✅' if deepseek_ok else '❌'} deepseek-sdk         - {'Import successful' if deepseek_ok else 'NOT INSTALLED'}")

# Check sqlalchemy
sqlalchemy_ok = check_import("sqlalchemy", "import sqlalchemy")
print(f"{'✅' if sqlalchemy_ok else '❌'} sqlalchemy           - {'Import successful' if sqlalchemy_ok else 'NOT INSTALLED'}")

# Check pydantic
pydantic_ok = check_import("pydantic", "import pydantic")
print(f"{'✅' if pydantic_ok else '❌'} pydantic             - {'Import successful' if pydantic_ok else 'NOT INSTALLED'}")

if not deepseek_ok:
    print("\nTo install deepseek-sdk run:")
    print("pip install deepseek    git add check_deps.py