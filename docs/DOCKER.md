# ChoyAI Brain - Docker Deployment Guide

This guide covers deploying ChoyAI Brain using Docker on your VPS server.

## 🚀 Quick Start

### Prerequisites
- Ubuntu 20.04+ VPS server
- Root access
- Domain name (optional, for webhooks)

### One-Command Deployment
```bash
curl -sSL https://raw.githubusercontent.com/shanchoynoor/ChoyAI/main/scripts/deploy-vps.sh | sudo bash
```

## 📋 Manual Deployment

### 1. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose git curl

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Clone Repository
```bash
git clone https://github.com/shanchoynoor/ChoyAI.git
cd ChoyAI
```

### 3. Configure Environment
```bash
# Create environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required Configuration:**
```bash
# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# DeepSeek API Key (primary AI provider)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Optional: Additional AI providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 4. Deploy with Make
```bash
# Quick start (recommended)
make quick-start

# Or step by step
make setup-env
make build
make run
```

## 🛠️ Available Commands

### Development
```bash
make dev-start      # Start development environment
make dev-logs       # View development logs
make dev-shell      # Open development shell
```

### Production
```bash
make build          # Build production image
make run            # Start production containers
make stop           # Stop all containers
make restart        # Restart services
make logs           # View application logs
```

### Maintenance
```bash
make status         # Check container status
make health         # Run health check
make backup         # Create database backup
make clean          # Clean up containers
make update         # Update and restart
```

### Monitoring
```bash
make stats          # Show resource usage
make monitor        # Monitor logs in real-time
```

## 📊 Service Management

### Using Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f choyai

# Stop services
docker-compose down

# Restart specific service
docker-compose restart choyai
```

### Using Systemd (Production)
```bash
# Start service
sudo systemctl start choyai

# Enable auto-start
sudo systemctl enable choyai

# Check status
sudo systemctl status choyai

# View logs
sudo journalctl -u choyai -f
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token | - |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API key | - |
| `OPENAI_API_KEY` | ❌ | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | ❌ | Anthropic API key | - |
| `XAI_API_KEY` | ❌ | xAI API key | - |
| `GEMINI_API_KEY` | ❌ | Gemini API key | - |
| `ENVIRONMENT` | ❌ | Environment mode | `production` |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` |
| `DATABASE_URL` | ❌ | Database connection | SQLite |
| `TELEGRAM_USE_POLLING` | ❌ | Use polling vs webhooks | `true` |

### Database Options

**SQLite (Default - Recommended)**
```bash
DATABASE_URL=sqlite:///app/data/choyai.db
```

**PostgreSQL (For Large Deployments)**
```bash
DATABASE_URL=postgresql://choyai:password@postgres:5432/choyai
```

### Resource Limits

Default Docker resource limits:
- **Memory**: 1GB limit, 512MB reserved
- **CPU**: 0.5 cores limit, 0.25 cores reserved

Modify in `docker-compose.yml` if needed.

## 🌐 Webhook Setup (Optional)

### 1. Configure Domain
```bash
# Update nginx.conf with your domain
sed -i 's/your_domain.com/yourdomain.com/g' nginx.conf
```

### 2. Get SSL Certificate
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

### 3. Deploy with Webhooks
```bash
# Update environment
echo "TELEGRAM_USE_POLLING=false" >> .env
echo "TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook" >> .env

# Deploy with nginx
make deploy-ssl
```

## 🔍 Monitoring & Troubleshooting

### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready

# View metrics
curl http://localhost:8000/metrics
```

### Log Locations
- **Application logs**: `./logs/choyai.log`
- **Container logs**: `docker-compose logs choyai`
- **System logs**: `journalctl -u choyai`

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs choyai

# Check environment
cat .env

# Rebuild image
make build
```

**Database issues:**
```bash
# Initialize database
make init-db

# Check database file
ls -la ./data/
```

**Memory issues:**
```bash
# Check resource usage
make stats

# Increase memory limits in docker-compose.yml
```

## 💾 Backup & Recovery

### Automatic Backups
```bash
# Create backup
make backup

# List backups
ls -la ./backups/

# Restore from backup
make restore BACKUP=choyai_backup_20250713_143000.tar.gz
```

### Manual Database Backup
```bash
# SQLite backup
docker-compose exec choyai cp /app/data/choyai.db /tmp/
docker cp choyai-brain:/tmp/choyai.db ./choyai_backup.db

# PostgreSQL backup
docker-compose exec postgres pg_dump -U choyai choyai > choyai_backup.sql
```

## 🔒 Security

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Container Security
- Runs as non-root user (`choyai`)
- Read-only file system where possible
- Limited resource access
- Regular security updates

### API Key Security
- Store keys in `.env` file only
- Never commit `.env` to version control
- Use environment-specific keys
- Rotate keys regularly

## 📈 Scaling

### Horizontal Scaling
For high-load deployments, consider:
- Load balancer (nginx/HAProxy)
- Multiple container instances
- Shared database (PostgreSQL)
- Redis for session storage

### Vertical Scaling
Increase resources in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 🆘 Support

### Getting Help
1. Check logs: `make logs`
2. Check health: `make health`
3. Review configuration: `cat .env`
4. Check GitHub issues
5. Contact support

### Performance Tuning
- Monitor memory usage with `make stats`
- Adjust AI provider settings
- Configure database optimization
- Set appropriate rate limits

## 🔄 Updates

### Automatic Updates
```bash
# Update to latest version
make update
```

### Manual Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
make stop
make build
make run
```

---

## 📝 Quick Reference

### Essential Commands
```bash
# Start everything
make quick-start

# Check status
make status

# View logs
make logs

# Create backup
make backup

# Update system
make update

# Get help
make help
```

### File Structure
```
ChoyAI/
├── docker-compose.yml          # Production deployment
├── docker-compose.dev.yml      # Development deployment
├── Dockerfile                  # Container definition
├── Makefile                   # Management commands
├── .env.example              # Environment template
├── nginx.conf                # Nginx configuration
├── scripts/
│   └── deploy-vps.sh         # VPS deployment script
└── app/                      # Application code
```

This Docker setup provides a production-ready deployment of ChoyAI Brain with monitoring, logging, backup, and security features built-in.
