# 🚨 ChoyAI Troubleshooting Guide

## 🔍 **Current Issue**: Container Restarting

Your `choyai-brain` container is in "Restarting" state, meaning it's crashing and Docker keeps trying to restart it.

## 📋 **Immediate Diagnosis Steps**

Run these commands on your VPS to find the problem:

### 1. Check Error Logs
```bash
# See what's causing the crash
make logs-tail

# Or get more detailed logs
make debug

# Check for specific errors
make logs-error
```

### 2. Check Environment Setup
```bash
# Verify .env file exists and has required values
ls -la .env
cat .env | grep -E "(TELEGRAM_BOT_TOKEN|DEBUG|ENVIRONMENT)"
```

### 3. Check Container Resources
```bash
# See if container is running out of memory
docker stats --no-stream
```

## 🔧 **Common Fixes**

### Fix 1: Missing Bot Token
```bash
# Edit your .env file
nano .env

# Add your Telegram bot token:
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
DEBUG=True
ENVIRONMENT=development

# Restart after fixing
make restart-main
```

### Fix 2: Database Connection Issues
```bash
# Check if database is accessible
docker-compose exec choyai-postgres psql -U choyai -d choyai -c "SELECT 1;"

# If that fails, restart everything
make stop
make run
```

### Fix 3: Python Import/Code Errors
```bash
# See the exact Python error
docker-compose logs choyai | tail -50

# If there are import errors, rebuild
make stop
make build
make run
```

### Fix 4: Permission Issues
```bash
# Check file permissions
ls -la data/
sudo chown -R 1000:1000 data/ logs/

# Restart
make restart-main
```

## 🎯 **Most Likely Causes**

1. **Missing TELEGRAM_BOT_TOKEN** in .env file
2. **Database connection failure** 
3. **Python import errors** (we fixed some, might be more)
4. **File permission issues**

## 📱 **Bot Token Setup**

If you haven't set up your Telegram bot yet:

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your .env file
4. Restart: `make restart-main`

## ✅ **Success Check**

After fixing, you should see:
```bash
make status
# Should show: choyai-brain   Up

make logs-tail
# Should show: "Bot started successfully" or similar
```

## 🆘 **If Still Failing**

Try development mode for easier debugging:
```bash
make dev-build
make dev-run
make dev-logs
```

Run `make debug` first and share the output to see exactly what's failing! 🔍
