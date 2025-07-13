# 🚨 Environment Variables Not Loading

## 🔍 **Problem Identified**

Your containers are starting but the environment variables aren't being read properly:

```
WARNING: The TELEGRAM_BOT_TOKEN variable is not set. Defaulting to a blank string.
WARNING: The DEEPSEEK_API_KEY variable is not set. Defaulting to a blank string.
```

And the main container is restarting because it can't connect without API keys.

## ⚡ **Quick Fix Commands**

Run these commands on your VPS to diagnose and fix:

### 1. **Check Environment Status**
```bash
make show-env
```

### 2. **Comprehensive Diagnostics**
```bash
make env-debug
```

### 3. **Fix Environment Issues**
```bash
make fix-env
```

## 🔧 **Manual Fix Steps**

### Step 1: Verify .env File Location and Content
```bash
# Check if .env exists in the right place
ls -la .env

# Show current directory (should be ChoyAI root)
pwd

# Check .env content (safely)
make show-env
```

### Step 2: Edit .env with Real API Keys
```bash
nano .env
```

Make sure your .env looks like this:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhiJklMnoPqrsTuvWxyZ
DEEPSEEK_API_KEY=sk-1234567890abcdefghijk

# Optional
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
XAI_API_KEY=
GEMINI_API_KEY=

# Settings
LOG_LEVEL=INFO
ENVIRONMENT=production
TELEGRAM_USE_POLLING=true
```

### Step 3: Restart with Environment Check
```bash
make safe-restart
```

## 🎯 **Common Issues & Solutions**

### **Issue 1: .env has placeholder values**
- **Problem**: Still has `your_bot_token_here`
- **Solution**: Replace with real API keys from BotFather and DeepSeek

### **Issue 2: .env in wrong location**
- **Problem**: File not in project root
- **Solution**: Ensure you're in `/srv/choyai/apps/chat/ChoyAI/` and .env is there

### **Issue 3: Empty or malformed .env**
- **Problem**: Missing variables or wrong format
- **Solution**: Use `make fix-env` to recreate from template

### **Issue 4: Docker Compose not reading .env**
- **Problem**: Variables not being passed to containers
- **Solution**: Restart Docker Compose: `make safe-restart`

## ✅ **Expected Results After Fix**

```bash
# No warnings about missing variables
make status
# Shows:
✅ choyai-brain    Up (healthy)
✅ choyai-postgres Up  
✅ choyai-redis    Up
```

## 📋 **Verification Steps**

1. **Check environment**: `make show-env`
2. **Container status**: `make status` 
3. **View logs**: `make logs-tail`
4. **Test bot**: Send `/start` to your Telegram bot

## 🆘 **If Still Not Working**

1. **Full diagnostics**: `make env-debug`
2. **Check logs**: `make logs`
3. **Fresh restart**: `make deploy-fresh`

The issue is definitely environment variables not being loaded properly! 🔧
