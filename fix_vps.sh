#!/bin/bash
# ChoyAI VPS Quick Fix Script
# Run this if you get JSON parsing errors

echo "🔧 ChoyAI VPS Quick Fix"
echo "======================="

echo "📥 Downloading updated settings.py..."
curl -sSL https://raw.githubusercontent.com/shanchoynoor/ChoyAI/main/app/config/settings.py -o app/config/settings.py

echo "✅ Settings updated!"
echo ""

echo "🧪 Testing configuration..."
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from app.config.settings import settings
    print('✅ Configuration loaded successfully!')
    print(f'   Environment: {settings.environment}')
    print(f'   Available personas: {len(settings.available_personas)}')
    print(f'   Data directory: {settings.data_dir}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

echo ""
echo "🚀 Ready to start ChoyAI!"
echo "Run: python app/main.py"
