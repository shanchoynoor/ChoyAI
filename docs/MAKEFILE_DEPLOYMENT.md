# 🐳 ChoyAI Docker Deployment with Makefile

## 🚀 Quick Start with Makefile

The easiest way to deploy ChoyAI is using the comprehensive Makefile commands:

### **Option 1: Complete Automated Setup**

```bash
# Navigate to ChoyAI directory
cd /srv/choyai/apps/chat/ChoyAI

# Pull latest changes
git pull

# Complete production setup (installs Docker, systemd, etc.)
sudo make setup
```

### **Option 2: Manual Deployment**

```bash
# Pull latest changes
git pull

# Check if environment is configured
make check-env

# Deploy ChoyAI
make deploy

# Or step by step:
make build      # Build Docker image
make start      # Start services
make logs       # View logs
```

## 📋 **Available Makefile Commands**

### **Production Commands**
```bash
make setup          # Complete production setup (requires sudo)
make deploy         # Deploy with validation
make start          # Start ChoyAI services  
make stop           # Stop ChoyAI services
make restart        # Restart ChoyAI services
make status         # Show service status and resource usage
make logs           # Show live logs (Ctrl+C to exit)
make logs-tail      # Show last 50 log lines
make update         # Pull latest code and restart
```

### **Development Commands**
```bash
make dev-start      # Start development environment
make dev-stop       # Stop development environment  
make dev-logs       # Show development logs
make build          # Build Docker image
make rebuild        # Force rebuild (no cache)
make shell          # Access container shell
```

### **Database Commands**
```bash
make db-init        # Initialize database
make db-migrate     # Run database migrations
```

### **Maintenance Commands**  
```bash
make backup         # Create database backup
make health         # Check service health
make clean          # Clean up Docker resources
```

## 🎯 **Complete Deployment Workflow**

### **First-Time Setup:**

```bash
# 1. Clone or navigate to ChoyAI
cd /srv/choyai/apps/chat/ChoyAI

# 2. Complete setup (installs Docker, systemd service, etc.)
sudo make setup

# 3. Configure environment
nano .env  # Add your API keys

# 4. Deploy ChoyAI
make deploy
```

### **Daily Operations:**

```bash
# Start services
make start

# Check status
make status

# View logs
make logs

# Stop services  
make stop

# Update to latest version
make update
```

### **Monitoring:**

```bash
# Check health
make health

# View recent logs
make logs-tail

# Check resource usage
make status
```

## ⚙️ **Environment Configuration**

Edit your `.env` file with required settings:

```bash
nano .env
```

Required variables:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## 🔄 **Auto-Startup Configuration**

The `make setup` command configures:

✅ **Systemd service** - Auto-start on boot  
✅ **Docker auto-restart** - Restart on failure  
✅ **Log rotation** - Prevent disk space issues  
✅ **Automatic backups** - Daily database backups  

## 📊 **Monitoring Commands**

```bash
# Service status with resource usage
make status

# Health check with error detection  
make health

# Live log monitoring
make logs

# Create manual backup
make backup
```

## 🛠️ **Development Workflow**

```bash
# Start development environment
make dev-start

# View development logs
make dev-logs  

# Access container shell for debugging
make shell

# Stop development environment
make dev-stop
```

## 🔄 **Update Process**

```bash
# Update to latest version
make update

# Or manual update:
git pull
make rebuild
make restart
```

## 🆘 **Troubleshooting**

### **Check Service Status:**
```bash
make status
make health
```

### **View Recent Errors:**  
```bash
make logs-tail
```

### **Restart Services:**
```bash
make restart
```

### **Force Rebuild:**
```bash
make rebuild
```

### **Access Container for Debugging:**
```bash
make shell
```

### **Clean Up and Restart:**
```bash
make clean
make deploy
```

## 🎉 **Success Verification**

After deployment, verify everything works:

1. **Check Status:** `make status` shows running services
2. **Check Health:** `make health` shows no errors  
3. **Check Logs:** `make logs-tail` shows successful startup
4. **Test Bot:** Send `/start` to your Telegram bot

## 💡 **Pro Tips**

- Use `make help` to see all available commands
- Use `make logs` to monitor real-time activity
- Use `make update` for easy updates
- Use `make backup` before major changes
- Use `make health` for quick health checks

The Makefile approach provides a simple, consistent interface for all Docker operations while maintaining the same powerful functionality as the shell scripts! 🚀
