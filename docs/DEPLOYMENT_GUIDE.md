# 🚀 ChoyAI VPS Deployment Guide

## ✅ Fixes Applied

### 1. Dependency Conflict Resolution
- ✅ Updated `python-telegram-bot` to version 21.0+ (more flexible)
- ✅ Adjusted `httpx` version to `>=0.24.0` (compatible range)
- ✅ Fixed Docker warnings about casing in Dockerfile

### 2. Docker Permission Fix
- ✅ Added `fix-docker` command to Makefile
- ✅ Smart dependency checking in `install-deps`

## 🏃‍♂️ Quick Deployment Steps

### Step 1: Fix Docker Permissions
```bash
make fix-docker
logout  # Important: Log out and back in
```

### Step 2: Deploy ChoyAI
```bash
# Clean build with new dependencies
make clean
make build
make run
```

### Step 3: Verify Deployment
```bash
make status
make logs
```

## 🔧 Alternative if Build Still Fails

If there are still dependency issues, try this minimal approach:

```bash
# Remove problematic packages temporarily
sed -i 's/sentence-transformers/#sentence-transformers/' requirements.txt
sed -i 's/chromadb/#chromadb/' requirements.txt

# Build with minimal dependencies
make build

# Check if it works
make status
```

## 📝 Environment Setup

Make sure your `.env` file has the required tokens:

```bash
# Edit your .env file
nano .env

# Add at minimum:
TELEGRAM_BOT_TOKEN=your_bot_token_here
DEBUG=True
ENVIRONMENT=development
```

## 🎯 Expected Result

After successful deployment:
- ✅ Container should be running
- ✅ `make status` shows healthy container
- ✅ `make logs` shows bot starting up
- ✅ Telegram bot responds to messages

## 🆘 Troubleshooting

### If build fails again:
```bash
# Check exact error
make build 2>&1 | tail -20

# Try development mode (less dependencies)
make dev-build
make dev-run
```

### If Docker permissions still fail:
```bash
# Manual fix
sudo usermod -aG docker admin
sudo systemctl restart docker
logout
```

## ✨ Success Indicators

When everything works:
1. `docker ps` shows running containers without sudo
2. `make status` shows healthy services  
3. `make logs` shows successful bot initialization
4. Telegram bot responds to `/start` command
