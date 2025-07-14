#!/bin/bash
# Emergency VPS Fix Script for ChoyAI Configuration

echo "🚨 ChoyAI Emergency Configuration Fix"
echo "====================================="

echo "🔍 Checking current status..."
if [ ! -f "app/config/settings.py" ]; then
    echo "❌ settings.py not found!"
    exit 1
fi

echo "📥 Restoring settings.py from git..."
git checkout HEAD -- app/config/settings.py

echo "🧪 Testing configuration..."
python test_config.py

if [ $? -eq 0 ]; then
    echo "✅ Configuration fixed!"
    echo "🚀 You can now run: python app/main.py"
else
    echo "❌ Still having issues. Manual fix needed."
    echo ""
    echo "🔧 Manual steps:"
    echo "1. Check your .env file for this line:"
    echo "   AVAILABLE_PERSONAS=choy,stark,rose,sherlock,joker,hermione,harley"
    echo ""
    echo "2. Make sure it has NO quotes around the value"
    echo "3. Make sure there are NO spaces after commas"
    echo "4. Make sure the line doesn't end with a space"
    echo ""
    echo "📝 Your current .env AVAILABLE_PERSONAS line:"
    grep "AVAILABLE_PERSONAS" .env || echo "   (line not found)"
fi
