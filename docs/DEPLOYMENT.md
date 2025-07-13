# ChoyAI Brain - VPS Deployment Package

## 📦 What's Included

This deployment package contains everything you need to run ChoyAI Brain on your VPS:

```
ChoyAI/
├── 🐳 Docker Files
│   ├── Dockerfile                  # Multi-stage production container
│   ├── docker-compose.yml          # Production deployment
│   ├── docker-compose.dev.yml      # Development deployment
│   └── nginx.conf                  # Nginx reverse proxy config
│
├── 🛠️ Automation Scripts
│   ├── Makefile                    # Easy management commands
│   ├── scripts/deploy-vps.sh       # One-command VPS deployment
│   └── scripts/test-docker.sh      # Docker environment testing
│
├── ⚙️ Configuration
│   ├── .env.example                # Environment template
│   └── DOCKER.md                   # Detailed deployment guide
│
└── 🧠 Application Code
    └── app/                        # ChoyAI Brain application
```

## 🚀 Quick VPS Deployment

### Option 1: One-Command Deployment (Recommended)
```bash
# SSH to your VPS and run:
curl -sSL https://raw.githubusercontent.com/shanchoynoor/ChoyAI/main/scripts/deploy-vps.sh | sudo bash
```

### Option 2: Manual Deployment
```bash
# 1. Clone repository
git clone https://github.com/shanchoynoor/ChoyAI.git
cd ChoyAI

# 2. Install dependencies
sudo apt update && sudo apt install -y docker.io docker-compose

# 3. Setup environment
make setup-env
# Edit .env with your API keys

# 4. Deploy
make quick-start
```

## 🔑 Required API Keys

Add these to your `.env` file:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional (for multi-AI support)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
XAI_API_KEY=your_xai_key
GEMINI_API_KEY=your_gemini_key
```

## 📊 Management Commands

```bash
# Service Management
make status          # Check status
make logs           # View logs
make restart        # Restart service
make stop           # Stop service

# Maintenance
make backup         # Create backup
make update         # Update and restart
make health         # Health check

# Development
make dev-start      # Development mode
make dev-logs       # Dev logs
```

## 🎯 Features Ready for Production

✅ **Multi-Provider AI System**
- DeepSeek (primary)
- OpenAI ChatGPT
- Anthropic Claude
- xAI Grok
- Google Gemini

✅ **Intelligent Task Routing**
- Conversation → DeepSeek
- Coding → OpenAI
- Creative → xAI
- Analysis → Anthropic
- Research → Gemini

✅ **User Profiling System**
- Automatic information extraction
- Conversation analytics
- Profile confidence scoring
- Detailed history tracking

✅ **Production Features**
- Docker containerization
- Health monitoring
- Automatic backups
- Log rotation
- Security hardening
- SSL support
- Resource limiting

## 🔗 Telegram Commands Available

**Basic Commands:**
- `/start` - Welcome and setup
- `/help` - Command guide
- `/persona <name>` - Switch AI personality
- `/myid` - Show user information

**AI Provider Management:**
- `/providers` - Show AI provider status
- `/switchai <task> <provider>` - Switch provider for tasks
- `/aitask <task> <message>` - Force specific task type

**User Profile Features:**
- `/profile` - View AI-generated profile
- `/analytics` - Conversation insights
- `/fullhistory` - Detailed history

**Memory System:**
- `/remember <key> <value>` - Save memory
- `/recall <key>` - Retrieve memory
- `/memories` - List all memories

## 🏗️ Architecture

```
Internet → Nginx → Docker Container → ChoyAI Brain
                                   ├── Telegram Bot
                                   ├── AI Engine (5 providers)
                                   ├── User Profile Manager
                                   ├── Memory System
                                   └── SQLite Database
```

## 📈 Resource Requirements

**Minimum VPS Specs:**
- **CPU**: 1 core
- **RAM**: 1GB
- **Storage**: 10GB
- **OS**: Ubuntu 20.04+

**Recommended for production:**
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 20GB
- **Bandwidth**: Unlimited

## 🔒 Security Features

- Non-root container execution
- Rate limiting
- Firewall configuration
- SSL/TLS encryption
- API key protection
- User validation
- Input sanitization

## 🆘 Troubleshooting

**Container won't start:**
```bash
make logs    # Check application logs
make status  # Check container status
```

**Database issues:**
```bash
make init-db  # Initialize database
```

**Memory/performance issues:**
```bash
make stats   # Check resource usage
```

**Need help:**
```bash
make help    # Show all commands
```

## 📞 Support Contacts

- **Documentation**: See DOCKER.md for detailed guide
- **Issues**: Check GitHub repository issues
- **Logs**: `make logs` for troubleshooting

---

## ✅ Pre-Deployment Checklist

- [ ] VPS server ready (Ubuntu 20.04+)
- [ ] Domain name configured (if using webhooks)
- [ ] Telegram bot token obtained
- [ ] DeepSeek API key ready
- [ ] Optional: Additional AI provider keys
- [ ] SSH access to VPS
- [ ] Firewall ports 80/443 open

## 🎉 Ready to Deploy!

Your ChoyAI Brain is ready for VPS deployment with full multi-AI capabilities, user profiling, and production-grade features!
