#!/bin/bash
# ChoyAI Docker Production Deployment Script
# This script sets up ChoyAI to run permanently on your server using Docker

set -e  # Exit on any error

echo "🐳 ChoyAI Docker Production Deployment"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << 'EOF'
# ChoyAI Configuration
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

# Database (default uses SQLite)
DATABASE_URL=sqlite:///app/data/choyai.db

# Memory Settings
MAX_CONVERSATION_HISTORY=50
DEFAULT_PERSONA=choy

# Security (optional)
ALLOWED_USERS=
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_WINDOW=60
EOF
    echo -e "${YELLOW}📝 Please edit .env file with your API keys before continuing.${NC}"
    echo -e "${BLUE}   nano .env${NC}"
    exit 1
fi

# Validate required environment variables
echo -e "${BLUE}🔍 Validating configuration...${NC}"
source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set in .env file${NC}"
    exit 1
fi

if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo -e "${RED}❌ DEEPSEEK_API_KEY not set in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration validated${NC}"

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p data/databases
mkdir -p data/logs
mkdir -p backups

# Stop existing containers (if any)
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f config/docker-compose.yml down || true

# Build the image
echo -e "${BLUE}🔨 Building ChoyAI Docker image...${NC}"
docker-compose -f config/docker-compose.yml build

# Initialize database
echo -e "${BLUE}💾 Initializing database...${NC}"
docker-compose -f config/docker-compose.yml run --rm choyai python tools/init_databases.py

# Run database migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
docker-compose -f config/docker-compose.yml run --rm choyai python tools/fix_database_schema.py

# Start services
echo -e "${BLUE}🚀 Starting ChoyAI services...${NC}"
docker-compose -f config/docker-compose.yml up -d

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${BLUE}📊 Checking service status...${NC}"
if docker-compose -f config/docker-compose.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ ChoyAI is running successfully!${NC}"
    echo ""
    echo -e "${GREEN}📱 Your Telegram bot is now live and ready to use!${NC}"
    echo ""
    echo "Useful commands:"
    echo -e "${BLUE}  View logs:${NC}     docker-compose -f config/docker-compose.yml logs -f"
    echo -e "${BLUE}  Stop service:${NC}  docker-compose -f config/docker-compose.yml down"
    echo -e "${BLUE}  Restart:${NC}      docker-compose -f config/docker-compose.yml restart"
    echo -e "${BLUE}  Update code:${NC}   git pull && docker-compose -f config/docker-compose.yml up -d --build"
    echo ""
    echo -e "${YELLOW}💡 The service will automatically restart if the server reboots.${NC}"
else
    echo -e "${RED}❌ Failed to start ChoyAI. Check logs:${NC}"
    echo -e "${BLUE}docker-compose -f config/docker-compose.yml logs${NC}"
    exit 1
fi

# Create backup script
echo -e "${BLUE}💾 Creating backup script...${NC}"
cat > backup_choyai.sh << 'EOF'
#!/bin/bash
# ChoyAI Backup Script

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 Creating backup: $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup databases
cp -r data/databases "$BACKUP_DIR/databases_$DATE"

# Backup logs (last 7 days)
find data/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# Compress backup
tar -czf "$BACKUP_DIR/choyai_backup_$DATE.tar.gz" -C "$BACKUP_DIR" "databases_$DATE"

# Clean up temporary files
rm -rf "$BACKUP_DIR/databases_$DATE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/choyai_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "✅ Backup completed: choyai_backup_$DATE.tar.gz"
EOF

chmod +x backup_choyai.sh

echo -e "${GREEN}🎉 ChoyAI Docker deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test your Telegram bot"
echo "2. Set up automated backups (optional): ./backup_choyai.sh"
echo "3. Monitor logs: docker-compose -f config/docker-compose.yml logs -f"
