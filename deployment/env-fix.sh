#!/bin/bash

# 🔧 ChoyAI Environment Fix Script
# This script helps diagnose and fix environment variable issues

echo "🔍 ChoyAI Environment Diagnostics"
echo "================================="

# Check current directory
echo "📂 Current directory: $(pwd)"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ .env file found"
    echo "📄 File size: $(wc -c < .env) bytes"
    echo "📍 File location: $(realpath .env)"
    echo ""
    
    # Check for common issues
    echo "🔍 Checking .env content..."
    
    if grep -q "your_.*_here" .env; then
        echo "❌ ISSUE: Placeholder values detected!"
        echo "📝 Found placeholders:"
        grep "your_.*_here" .env | head -5
        echo ""
        echo "💡 SOLUTION: Replace placeholders with real API keys"
        echo "   Edit with: nano .env"
        echo ""
    fi
    
    # Check required variables
    if grep -q "TELEGRAM_BOT_TOKEN=" .env; then
        if grep -q "TELEGRAM_BOT_TOKEN=$\|TELEGRAM_BOT_TOKEN=your_" .env; then
            echo "❌ TELEGRAM_BOT_TOKEN is empty or has placeholder"
        else
            echo "✅ TELEGRAM_BOT_TOKEN is set"
        fi
    else
        echo "❌ TELEGRAM_BOT_TOKEN is missing"
    fi
    
    if grep -q "DEEPSEEK_API_KEY=" .env; then
        if grep -q "DEEPSEEK_API_KEY=$\|DEEPSEEK_API_KEY=your_" .env; then
            echo "❌ DEEPSEEK_API_KEY is empty or has placeholder"
        else
            echo "✅ DEEPSEEK_API_KEY is set"
        fi
    else
        echo "❌ DEEPSEEK_API_KEY is missing"
    fi
    
else
    echo "❌ .env file not found!"
    echo "📝 Creating from template..."
    
    if [ -f config/.env.example ]; then
        cp config/.env.example .env
        echo "✅ .env file created from template"
    else
        echo "❌ Template not found, creating basic .env..."
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
    fi
fi

echo ""
echo "🐳 Docker Compose Environment Test:"
echo "====================================="

# Test if docker-compose can read the variables
if [ -f config/docker-compose.yml ]; then
    echo "📋 Testing Docker Compose configuration..."
    
    # Try to validate compose file
    if docker-compose -f config/docker-compose.yml config > /dev/null 2>&1; then
        echo "✅ Docker Compose file is valid"
        
        # Check if variables are being read
        echo "🔍 Checking environment variable resolution..."
        ENV_CHECK=$(docker-compose -f config/docker-compose.yml config | grep -E "TELEGRAM_BOT_TOKEN|DEEPSEEK_API_KEY" | head -2)
        
        if echo "$ENV_CHECK" | grep -q "TELEGRAM_BOT_TOKEN.*your_\|TELEGRAM_BOT_TOKEN.*null\|TELEGRAM_BOT_TOKEN.*''"; then
            echo "❌ TELEGRAM_BOT_TOKEN not properly resolved"
        elif echo "$ENV_CHECK" | grep -q "TELEGRAM_BOT_TOKEN"; then
            echo "✅ TELEGRAM_BOT_TOKEN resolved by Docker Compose"
        fi
        
        if echo "$ENV_CHECK" | grep -q "DEEPSEEK_API_KEY.*your_\|DEEPSEEK_API_KEY.*null\|DEEPSEEK_API_KEY.*''"; then
            echo "❌ DEEPSEEK_API_KEY not properly resolved"
        elif echo "$ENV_CHECK" | grep -q "DEEPSEEK_API_KEY"; then
            echo "✅ DEEPSEEK_API_KEY resolved by Docker Compose"
        fi
        
    else
        echo "❌ Docker Compose configuration has errors"
    fi
else
    echo "❌ docker-compose.yml not found in config/"
fi

echo ""
echo "🎯 RECOMMENDATIONS:"
echo "==================="

if [ ! -f .env ] || grep -q "your_.*_here" .env; then
    echo "1. 📝 Edit .env file with real API keys:"
    echo "   nano .env"
    echo ""
    echo "2. 🔑 Get your tokens:"
    echo "   - Telegram: @BotFather on Telegram"
    echo "   - DeepSeek: https://platform.deepseek.com/"
    echo ""
fi

echo "3. 🔄 After editing .env, restart containers:"
echo "   make safe-restart"
echo ""

echo "4. ✅ Verify with:"
echo "   make show-env"
echo "   make status"
echo ""

echo "💡 EXAMPLE .env format:"
echo "======================"
echo "TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhiJklMnoPqrsTuvWxyZ"
echo "DEEPSEEK_API_KEY=sk-1234567890abcdefghijk"
echo ""

echo "🚀 Quick Fix Commands:"
echo "====================="
echo "make show-env     # Show environment status"
echo "make fix-env      # Fix common environment issues"
echo "make safe-restart # Restart with environment check"
