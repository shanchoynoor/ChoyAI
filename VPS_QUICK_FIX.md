# 🚀 ChoyAI VPS Deployment - Quick Fix Guide

## Current Situation
✅ Docker is already installed on your VPS  
✅ Docker Compose is already installed  
❌ Package conflict with containerd.io  
❌ User permissions need fixing  

## Quick Fix Steps

### 1. Fix Docker Permissions
```bash
make fix-docker
```

### 2. Log out and back in (important!)
```bash
logout
# Then SSH back in
```

### 3. Test Docker Access
```bash
docker ps
docker-compose --version
```

### 4. Deploy ChoyAI
```bash
# Option A: Quick deployment
make quick-start

# Option B: Manual deployment
make build
make run

# Option C: Full VPS deployment with SSL
./scripts/deploy-vps.sh your-domain.com
```

## Alternative: Manual Docker Setup
If the above doesn't work, try:

```bash
# Add yourself to docker group manually
sudo usermod -aG docker admin

# Restart Docker service
sudo systemctl restart docker

# Log out and back in
logout

# Test access
docker ps
```

## Verify Installation
```bash
# Check Docker status
sudo systemctl status docker

# Check if you're in docker group
groups

# Test container access
docker ps -a
```

## If Still Having Issues
```bash
# Check Docker daemon
sudo systemctl status docker

# Check group membership
id admin

# Force group refresh
newgrp docker
```
