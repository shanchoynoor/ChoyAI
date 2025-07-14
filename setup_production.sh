#!/bin/bash
# ChoyAI Complete Production Setup
# Sets up ChoyAI with Docker and systemd for automatic startup

set -e

echo "🚀 ChoyAI Complete Production Setup"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root for systemd setup
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  This script needs sudo privileges for systemd setup${NC}"
    echo "Run: sudo $0"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${BLUE}🔍 Setting up for user: $ACTUAL_USER${NC}"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo -e "${BLUE}📦 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $ACTUAL_USER
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo -e "${BLUE}📦 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Ensure Docker service is running
systemctl start docker
systemctl enable docker

# Make scripts executable
chmod +x deploy_docker.sh
chmod +x docker_manage.sh

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📝 Creating .env template...${NC}"
    cat > .env << 'EOF'
# ChoyAI Production Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Required: Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Required: DeepSeek API Key (primary AI provider)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Optional: Additional AI Providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
XAI_API_KEY=
GEMINI_API_KEY=

# Telegram Settings
TELEGRAM_USE_POLLING=true
TELEGRAM_WEBHOOK_URL=

# Database
DATABASE_URL=sqlite:///app/data/choyai.db

# Memory Settings
MAX_CONVERSATION_HISTORY=50
DEFAULT_PERSONA=choy

# Security (optional)
ALLOWED_USERS=
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_WINDOW=60
EOF
    chown $ACTUAL_USER:$ACTUAL_USER .env
    echo -e "${YELLOW}📝 Please edit .env file with your API keys${NC}"
fi

# Set up systemd service for auto-start
echo -e "${BLUE}⚙️  Setting up systemd service...${NC}"
cp config/choyai-docker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable choyai-docker.service

echo -e "${GREEN}✅ Systemd service installed and enabled${NC}"

# Create log rotation
echo -e "${BLUE}📋 Setting up log rotation...${NC}"
cat > /etc/logrotate.d/choyai << 'EOF'
/srv/choyai/apps/chat/ChoyAI/data/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        docker-compose -f /srv/choyai/apps/chat/ChoyAI/config/docker-compose.yml restart
    endscript
}
EOF

# Set up cron for automatic backups
echo -e "${BLUE}💾 Setting up automatic backups...${NC}"
cat > /etc/cron.d/choyai-backup << 'EOF'
# ChoyAI automatic backup - runs daily at 2 AM
0 2 * * * root cd /srv/choyai/apps/chat/ChoyAI && ./backup_choyai.sh >/dev/null 2>&1
EOF

# Set correct ownership
chown -R $ACTUAL_USER:$ACTUAL_USER .

echo -e "${GREEN}🎉 ChoyAI production setup completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit .env file with your API keys:"
echo -e "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Deploy ChoyAI:"
echo -e "   ${YELLOW}./deploy_docker.sh${NC}"
echo ""
echo "3. Or manage services:"
echo -e "   ${YELLOW}./docker_manage.sh start${NC}"
echo -e "   ${YELLOW}./docker_manage.sh logs${NC}"
echo -e "   ${YELLOW}./docker_manage.sh status${NC}"
echo ""
echo -e "${GREEN}✨ ChoyAI will now automatically start on boot!${NC}"
