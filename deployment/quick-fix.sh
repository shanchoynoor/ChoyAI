#!/bin/bash

# 🚀 ChoyAI Quick Fix Script
# This script resolves common deployment issues

echo "🔧 ChoyAI Quick Fix Starting..."
echo "================================"

# Step 1: Force stop and remove conflicting containers
echo "💀 Step 1: Removing conflicting containers..."
docker-compose -f config/docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
docker container rm -f choyai-brain choyai-redis choyai-postgres 2>/dev/null || true
docker network rm config_choyai_network 2>/dev/null || true
echo "✅ Containers cleaned"

# Step 2: Check for .env file
echo "🔍 Step 2: Checking environment configuration..."
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f config/.env.example ]; then
        cp config/.env.example .env
        echo "✅ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env with your API keys!"
        echo "📝 Required variables:"
        echo "   - TELEGRAM_BOT_TOKEN=your_bot_token_here"
        echo "   - DEEPSEEK_API_KEY=your_deepseek_key_here"
        echo ""
        echo "💡 Edit with: nano .env"
        echo ""
        read -p "Press Enter after you've added your API keys to .env file..."
    else
        echo "❌ Template file not found. Creating basic .env..."
        cat > .env << 'EOF'
# ChoyAI Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_key_here

# Optional AI Providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
XAI_API_KEY=
GEMINI_API_KEY=

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=production
TELEGRAM_USE_POLLING=true
EOF
        echo "✅ Basic .env file created"
        echo "⚠️  Please edit .env with your API keys!"
        echo "💡 Edit with: nano .env"
        read -p "Press Enter after you've added your API keys..."
    fi
else
    echo "✅ .env file exists"
fi

# Step 3: Validate API keys
echo "🔍 Step 3: Validating API keys..."
if grep -q "your_bot_token_here" .env || grep -q "your_deepseek_key_here" .env; then
    echo "⚠️  WARNING: Placeholder values detected in .env file"
    echo "📝 Please update .env with real API keys"
    echo "💡 Edit with: nano .env"
    read -p "Press Enter after updating API keys..."
fi

# Step 4: Build and start
echo "🔨 Step 4: Building containers..."
docker-compose -f config/docker-compose.yml build --no-cache

echo "🚀 Step 5: Starting ChoyAI..."
docker-compose -f config/docker-compose.yml up -d

# Step 6: Wait and check status
echo "⏳ Waiting for containers to start..."
sleep 10

echo "📊 Step 6: Checking status..."
docker-compose -f config/docker-compose.yml ps

echo ""
echo "🎉 Quick Fix Complete!"
echo "====================="
echo ""
echo "📊 To check status: make status"
echo "📋 To view logs: make logs"
echo "🔍 To debug: make debug"
echo ""
echo "If issues persist:"
echo "1. Check logs: make logs"
echo "2. Verify .env file has correct API keys"
echo "3. Try fresh deployment: make deploy-fresh"
