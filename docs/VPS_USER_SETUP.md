# VPS Deployment User Configuration

## User Setup for ChoyAI Deployment

When deploying ChoyAI on your VPS, the system sets up two types of users:

### 1. Service User: `choyai`
- **Purpose**: Dedicated user for running the ChoyAI application
- **Security**: Follows principle of least privilege
- **Created automatically** by the deployment script
- **Docker access**: Added to docker group for container management

### 2. Admin User: `admin` (Your existing user)
- **Purpose**: System administration and management
- **Docker access**: Added to docker group during deployment
- **Usage**: Can manage Docker containers and monitor the system

## Commands Updated for VPS

### Makefile Command
```bash
# Updated to use 'admin' user specifically
make install-deps
```

### Deployment Script
```bash
# Handles both users automatically
./scripts/deploy-vps.sh your-domain.com
```

## After Deployment

Both users will have Docker access:

```bash
# As admin user
sudo docker ps
sudo docker logs choyai-brain

# As choyai service user  
sudo -u choyai docker ps
sudo -u choyai docker logs choyai-brain
```

## Security Note

The ChoyAI application runs under the `choyai` service user for security isolation, while the `admin` user retains full system access for management tasks.
