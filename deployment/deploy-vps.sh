#!/bin/bash
# ChoyAI Brain VPS Deployment Script
# Usage: curl -sSL https://your-repo/deploy.sh | bash

set -e

echo "🚀 ChoyAI Brain VPS Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/shanchoynoor/ChoyAI.git"
INSTALL_DIR="/opt/choyai"
SERVICE_USER="choyai"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update system
    apt-get update && apt-get upgrade -y
    
    # Install required packages
    apt-get install -y \
        curl \
        git \
        docker.io \
        docker-compose \
        nginx \
        certbot \
        python3-certbot-nginx \
        ufw \
        htop \
        wget \
        unzip
    
    # Start and enable Docker
    systemctl enable docker
    systemctl start docker
    
    log_info "Dependencies installed successfully"
}

create_user() {
    log_info "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER"
        log_info "User $SERVICE_USER created"
    else
        log_warn "User $SERVICE_USER already exists"
    fi
    
    # Also add the admin user to docker group for management
    if id "admin" &>/dev/null; then
        usermod -aG docker admin
        log_info "Added admin user to docker group"
    fi
}

clone_repository() {
    log_info "Cloning repository..."
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Installation directory exists, updating..."
        cd "$INSTALL_DIR"
        sudo -u "$SERVICE_USER" git pull
    else
        sudo -u "$SERVICE_USER" git clone "$REPO_URL" "$INSTALL_DIR"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    fi
    
    cd "$INSTALL_DIR"
    log_info "Repository cloned successfully"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Copy environment template
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        sudo -u "$SERVICE_USER" cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        log_warn "Please edit $INSTALL_DIR/.env with your API keys"
    fi
    
    # Create necessary directories
    sudo -u "$SERVICE_USER" mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/ssl"
    
    log_info "Environment setup complete"
}

setup_firewall() {
    log_info "Configuring firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
    
    log_info "Firewall configured"
}

setup_ssl() {
    log_info "Setting up SSL (optional)..."
    
    read -p "Do you want to set up SSL with Let's Encrypt? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your domain name: " DOMAIN
        
        if [ -n "$DOMAIN" ]; then
            # Get SSL certificate
            certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
            
            # Copy certificates to project directory
            cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem "$INSTALL_DIR/ssl/cert.pem"
            cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem "$INSTALL_DIR/ssl/key.pem"
            chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/ssl"
            
            log_info "SSL certificate installed for $DOMAIN"
        fi
    fi
}

create_systemd_service() {
    log_info "Creating systemd service..."
    
    cat > /etc/systemd/system/choyai.service << EOF
[Unit]
Description=ChoyAI Brain Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
User=$SERVICE_USER
Group=$SERVICE_USER
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable choyai
    
    log_info "Systemd service created"
}

setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/choyai << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        /usr/bin/docker-compose -f $INSTALL_DIR/docker-compose.yml restart choyai
    endscript
}
EOF

    log_info "Log rotation configured"
}

build_and_start() {
    log_info "Building and starting ChoyAI Brain..."
    
    cd "$INSTALL_DIR"
    
    # Build the application
    sudo -u "$SERVICE_USER" docker-compose build
    
    # Start the service
    systemctl start choyai
    
    log_info "ChoyAI Brain started successfully"
}

show_status() {
    log_info "Deployment Summary:"
    echo "===================="
    echo "Installation Directory: $INSTALL_DIR"
    echo "Service User: $SERVICE_USER"
    echo "Service Status: $(systemctl is-active choyai)"
    echo
    echo "Next steps:"
    echo "1. Edit $INSTALL_DIR/.env with your API keys"
    echo "2. Restart the service: systemctl restart choyai"
    echo "3. Check logs: journalctl -u choyai -f"
    echo "4. Check container logs: cd $INSTALL_DIR && docker-compose logs -f"
    echo
    echo "Management commands:"
    echo "- Start: systemctl start choyai"
    echo "- Stop: systemctl stop choyai"
    echo "- Restart: systemctl restart choyai"
    echo "- Status: systemctl status choyai"
    echo "- Logs: journalctl -u choyai -f"
    echo
    echo "Using Makefile (from $INSTALL_DIR):"
    echo "- make help    # Show all available commands"
    echo "- make status  # Check container status"
    echo "- make logs    # Show application logs"
    echo "- make backup  # Create backup"
    echo "- make update  # Update and restart"
}

# Main deployment process
main() {
    log_info "Starting ChoyAI Brain deployment..."
    
    check_root
    install_dependencies
    create_user
    clone_repository
    setup_environment
    setup_firewall
    setup_ssl
    create_systemd_service
    setup_log_rotation
    build_and_start
    show_status
    
    log_info "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
