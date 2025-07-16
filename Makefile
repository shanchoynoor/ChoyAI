# ChoyAI Cost-Effective Productivity Suite - Enhanced Makefile
# Complete deployment and management for VPS servers
# Usage: make [target]

.PHONY: help install deps setup deploy start stop restart status logs build clean backup health update shell
.PHONY: vps-setup vps-install vps-deploy productivity-setup test-modules
.PHONY: install-python install-deps install-node install-docker
.PHONY: update-deps upgrade security-update

# Variables
COMPOSE_FILE = config/docker-compose.yml
DEV_COMPOSE_FILE = config/docker-compose.dev.yml
CONTAINER_NAME = choyai-brain
IMAGE_NAME = choyai-brain:latest
BACKUP_DIR = ./backups
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)
PYTHON_VERSION = 3.11
NODE_VERSION = 20

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# ==============================================================================
# 📖 HELP & DOCUMENTATION
# ==============================================================================

help: ## Show this help message
	@echo "$(BLUE)🚀 ChoyAI Cost-Effective Productivity Suite$(NC)"
	@echo "$(GREEN)Complete VPS deployment and management system$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Available Commands:$(NC)"
	@echo ""
	@echo "$(BLUE)🛠️  Installation & Setup:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$2 ~ /Install|Setup|Configure/) printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)🎯 Productivity Modules:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$2 ~ /productivity|modules|test/) printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)🐳 Docker & Deployment:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$2 ~ /Deploy|Docker|Container|Start|Stop/) printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)🔨 Development & Build:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$2 ~ /Build|Update|Development|Test/) printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)📊 Monitoring & Maintenance:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { if ($$2 ~ /Monitor|Health|Status|Logs|Clean|Backup/) printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)💡 Quick Start:$(NC)"
	@echo "  1. make vps-setup     # Complete VPS setup"
	@echo "  2. make setup         # Configure environment"
	@echo "  3. make deploy        # Deploy ChoyAI"
	@echo "  4. make status        # Check deployment"
	@echo ""
	@echo "$(YELLOW)🔗 Documentation:$(NC)"
	@echo "  📚 Full docs: docs/DEPLOYMENT_GUIDE.md"
	@echo "  🐳 Docker:    docs/DOCKER.md"
	@echo "  🚀 VPS:       docs/VPS_SETUP_GUIDE.md"

# ==============================================================================
# 🛠️  INSTALLATION & DEPENDENCIES
# ==============================================================================

install-python: ## Install Python 3.11
	@echo "🐍 $(BLUE)Installing Python $(PYTHON_VERSION)...$(NC)"
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo apt-get install -y python$(PYTHON_VERSION) python$(PYTHON_VERSION)-pip python$(PYTHON_VERSION)-venv; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y python$(PYTHON_VERSION) python$(PYTHON_VERSION)-pip; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y python$(PYTHON_VERSION) python$(PYTHON_VERSION)-pip; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install python@$(PYTHON_VERSION); \
	else \
		echo "$(RED)❌ Unsupported package manager$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python $(PYTHON_VERSION) installed$(NC)"

install-deps: ## Install Python dependencies
	@echo "📦 $(BLUE)Installing Python dependencies...$(NC)"
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠️  Python not found, installing...$(NC)"; \
		make install-python; \
	fi
	@python3 -m pip install --upgrade pip
	@python3 -m pip install -r requirements.txt
	@echo "$(GREEN)✅ Python dependencies installed$(NC)"

install-node: ## Install Node.js 20
	@echo "🟩 $(BLUE)Installing Node.js $(NODE_VERSION)...$(NC)"
	@if command -v apt-get >/dev/null 2>&1; then \
		curl -fsSL https://deb.nodesource.com/setup_$(NODE_VERSION).x | sudo -E bash -; \
		sudo apt-get install -y nodejs; \
	elif command -v yum >/dev/null 2>&1; then \
		curl -fsSL https://rpm.nodesource.com/setup_$(NODE_VERSION).x | sudo bash -; \
		sudo yum install -y nodejs; \
	elif command -v dnf >/dev/null 2>&1; then \
		curl -fsSL https://rpm.nodesource.com/setup_$(NODE_VERSION).x | sudo bash -; \
		sudo dnf install -y nodejs; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install node@$(NODE_VERSION); \
	else \
		echo "$(RED)❌ Unsupported package manager$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Node.js $(NODE_VERSION) installed$(NC)"

install-docker: ## Install Docker and Docker Compose
	@echo "🐳 $(BLUE)Installing Docker...$(NC)"
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release; \
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg; \
		echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null; \
		sudo apt-get update; \
		sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y yum-utils; \
		sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo; \
		sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install docker docker-compose; \
	else \
		echo "$(RED)❌ Unsupported system for Docker installation$(NC)"; \
		exit 1; \
	fi
	@sudo systemctl enable docker
	@sudo systemctl start docker
	@sudo usermod -aG docker $${USER}
	@echo "$(GREEN)✅ Docker installed$(NC)"
	@echo "$(YELLOW)⚠️  Please logout and login again to use Docker without sudo$(NC)"

# ==============================================================================
# 🖥️  VPS SERVER SETUP
# ==============================================================================

vps-setup: ## Complete VPS setup (Ubuntu/Debian/CentOS)
	@echo "🖥️  $(BLUE)Setting up VPS server...$(NC)"
	@make vps-install-system
	@make install-python
	@make install-deps
	@make install-docker
	@make vps-configure
	@echo "$(GREEN)✅ VPS setup completed$(NC)"

vps-install-system: ## Install essential system packages
	@echo "📦 $(BLUE)Installing system packages...$(NC)"
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo apt-get upgrade -y; \
		sudo apt-get install -y curl wget git vim nano htop unzip build-essential software-properties-common; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum update -y; \
		sudo yum groupinstall -y "Development Tools"; \
		sudo yum install -y curl wget git vim nano htop unzip; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf update -y; \
		sudo dnf groupinstall -y "Development Tools"; \
		sudo dnf install -y curl wget git vim nano htop unzip; \
	else \
		echo "$(RED)❌ Unsupported package manager$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ System packages installed$(NC)"

vps-configure: ## Configure VPS server settings
	@echo "⚙️  $(BLUE)Configuring VPS server...$(NC)"
	@# Setup firewall
	@if command -v ufw >/dev/null 2>&1; then \
		sudo ufw --force enable; \
		sudo ufw allow ssh; \
		sudo ufw allow 8000; \
		echo "$(GREEN)✅ UFW firewall configured$(NC)"; \
	fi
	@# Setup swap if not exists
	@if [ ! -f /swapfile ]; then \
		echo "$(BLUE)Creating 2GB swap file...$(NC)"; \
		sudo fallocate -l 2G /swapfile; \
		sudo chmod 600 /swapfile; \
		sudo mkswap /swapfile; \
		sudo swapon /swapfile; \
		echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab; \
		echo "$(GREEN)✅ Swap file created$(NC)"; \
	fi
	@echo "$(GREEN)✅ VPS configuration completed$(NC)"

vps-deploy: ## Deploy ChoyAI on VPS
	@echo "🚀 $(BLUE)Deploying ChoyAI on VPS...$(NC)"
	@make setup
	@make deploy
	@make install-systemd
	@echo "$(GREEN)✅ VPS deployment completed$(NC)"

# ==============================================================================
# 🎯 PRODUCTIVITY MODULES
# ==============================================================================

productivity-setup: ## Setup productivity modules
	@echo "🎯 $(BLUE)Setting up productivity modules...$(NC)"
	@# Create required directories
	@mkdir -p data/core_memory data/databases data/logs
	@mkdir -p templates/personas
	@# Initialize databases
	@python3 tools/init_databases.py || echo "$(YELLOW)⚠️  Database init script not found, will create on first run$(NC)"
	@# Setup module configuration
	@if [ ! -f ".env" ]; then \
		echo "$(YELLOW)⚠️  Creating .env from template...$(NC)"; \
		cp config/.env.example .env; \
	fi
	@echo "$(GREEN)✅ Productivity modules setup completed$(NC)"
	@echo "$(YELLOW)💡 Available modules:$(NC)"
	@echo "   📝 Tasks & To-Do Management"
	@echo "   📚 Smart Notes with AI Summarization"  
	@echo "   📅 Calendar & Scheduling"
	@echo "   💬 Enhanced Chat & Voice"
	@echo "   📨 Mail Assistant (planned)"
	@echo "   📱 Messaging Hub (planned)"
	@echo "   📰 News Aggregator (planned)"
	@echo "   💰 Finance Tracker (planned)"

test-modules: ## Test productivity modules functionality
	@echo "🧪 $(BLUE)Testing productivity modules...$(NC)"
	@if [ ! -f "demo_productivity_suite.py" ]; then \
		echo "$(RED)❌ Demo script not found$(NC)"; \
		exit 1; \
	fi
	@python3 demo_productivity_suite.py
	@echo "$(GREEN)✅ Module testing completed$(NC)"

# ==============================================================================  
# 📦 DEPENDENCY MANAGEMENT
# ==============================================================================

update-deps: ## Update Python dependencies
	@echo "📦 $(BLUE)Updating Python dependencies...$(NC)"
	@python3 -m pip install --upgrade pip
	@python3 -m pip install --upgrade -r requirements.txt
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

freeze-deps: ## Freeze current dependencies to requirements.txt
	@echo "📦 $(BLUE)Freezing dependencies...$(NC)"
	@python3 -m pip freeze > requirements.txt
	@echo "$(GREEN)✅ Dependencies frozen to requirements.txt$(NC)"

security-update: ## Update dependencies with security patches
	@echo "🔒 $(BLUE)Applying security updates...$(NC)"
	@python3 -m pip install --upgrade pip
	@python3 -m pip install --upgrade $(shell python3 -m pip list --outdated --format=freeze | cut -d= -f1)
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get upgrade -y; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum update -y; \
	fi
	@echo "$(GREEN)✅ Security updates completed$(NC)"

upgrade: security-update ## Alias for security-update

# ==============================================================================
# ⚙️  SETUP & CONFIGURATION  
# ==============================================================================

setup-local: ## Setup local development environment
	@echo "⚙️  $(BLUE)Setting up local development environment...$(NC)"
	@make productivity-setup
	@if [ ! -f ".env" ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp config/.env.example .env; \
		echo "$(YELLOW)⚠️  Please edit .env and add your API keys$(NC)"; \
	fi
	@echo "$(GREEN)✅ Local setup completed$(NC)"

setup-env: ## Interactive environment setup
	@echo "⚙️  $(BLUE)Setting up environment configuration...$(NC)"
	@if [ ! -f ".env" ]; then cp config/.env.example .env; fi
	@echo "$(YELLOW)Please edit .env file with your configuration:$(NC)"
	@echo "Required API keys:"
	@echo "  - TELEGRAM_BOT_TOKEN (from @BotFather)"
	@echo "  - DEEPSEEK_API_KEY (recommended primary)"
	@echo "  - OPENAI_API_KEY (optional)"
	@echo "  - ANTHROPIC_API_KEY (optional)"
	@echo ""
	@read -p "Press Enter to open .env file for editing..." dummy
	@$${EDITOR:-nano} .env
	@make check-env

setup: setup-local ## Alias for setup-local

# ==============================================================================
# 🐳 DOCKER & DEPLOYMENT
# ==============================================================================

deploy: check-env ## Deploy ChoyAI with Docker (validates config)
	@echo "🚀 $(GREEN)Deploying ChoyAI...$(NC)"
	@bash deploy_docker.sh

deploy-production: ## Deploy to production with full setup
	@echo "🚀 $(GREEN)Deploying ChoyAI to production...$(NC)"
	@make check-env
	@make backup
	@bash setup_production.sh
	@make health
	@echo "$(GREEN)✅ Production deployment completed$(NC)"

# Container management
start: ## Start ChoyAI services
	@echo "$(BLUE)🚀 Starting ChoyAI services...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Services started$(NC)"
	@make status

stop: ## Stop ChoyAI services
	@echo "$(BLUE)🛑 Stopping ChoyAI services...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: ## Restart ChoyAI services
	@echo "$(BLUE)🔄 Restarting ChoyAI services...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

# ==============================================================================
# 📊 MONITORING & LOGS
# ==============================================================================

status: ## Show service status and resource usage
	@echo "$(BLUE)📊 Service Status:$(NC)"
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose -f $(COMPOSE_FILE) ps; \
	else \
		echo "$(YELLOW)⚠️  Docker Compose not available$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)💾 Resource Usage:$(NC)"
	@if command -v docker >/dev/null 2>&1; then \
		docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | head -2 || echo "$(YELLOW)No containers running$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Docker not available$(NC)"; \
	fi

logs: ## Show live logs (Ctrl+C to exit)
	@echo "$(BLUE)📋 Live logs (Ctrl+C to exit):$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs -f

logs-tail: ## Show last 50 log lines
	@echo "$(BLUE)📋 Last 50 log lines:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs --tail=50

logs-error: ## Show recent error logs
	@echo "$(BLUE)🚨 Recent error logs:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs --since="1h" 2>/dev/null | grep -i error || echo "$(GREEN)No recent errors$(NC)"

# ==============================================================================
# 🔨 BUILD & UPDATE
# ==============================================================================

build: ## Build Docker image
	@echo "$(BLUE)🔨 Building ChoyAI Docker image...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)✅ Image built successfully$(NC)"

rebuild: ## Force rebuild Docker image (no cache)
	@echo "$(BLUE)🔨 Force rebuilding ChoyAI Docker image...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) build --no-cache
	@echo "$(GREEN)✅ Image rebuilt successfully$(NC)"

update: ## Update code and restart services
	@echo "$(BLUE)🔄 Updating ChoyAI...$(NC)"
	@git pull
	@make update-deps
	@docker-compose -f $(COMPOSE_FILE) up -d --build
	@echo "$(GREEN)✅ Update completed$(NC)"

update-production: ## Update production deployment
	@echo "$(BLUE)🔄 Updating production ChoyAI...$(NC)"
	@git pull
	@make update-deps
	@make backup
	@docker-compose -f $(COMPOSE_FILE) up -d --build
	@make health
	@echo "$(GREEN)✅ Production update completed$(NC)"

# ==============================================================================
# 🛠️  DEVELOPMENT
# ==============================================================================

dev-start: ## Start development environment
	@echo "$(YELLOW)🚀 Starting development environment...$(NC)"
	@docker-compose -f $(DEV_COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Development environment started$(NC)"

dev-stop: ## Stop development environment  
	@echo "$(YELLOW)🛑 Stopping development environment...$(NC)"
	@docker-compose -f $(DEV_COMPOSE_FILE) down
	@echo "$(GREEN)✅ Development environment stopped$(NC)"

dev-logs: ## Show development logs
	@docker-compose -f $(DEV_COMPOSE_FILE) logs -f

dev-shell: ## Access development container shell
	@echo "$(YELLOW)🐚 Accessing development container shell...$(NC)"
	@docker-compose -f $(DEV_COMPOSE_FILE) exec choyai bash

dev-install: ## Install development dependencies
	@echo "$(YELLOW)📦 Installing development dependencies...$(NC)"
	@pip3 install pytest pytest-asyncio black flake8 mypy
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

dev-test: ## Run development tests
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	@python3 -m pytest tests/ -v
	@make test-modules

dev-format: ## Format code with black
	@echo "$(YELLOW)🎨 Formatting code...$(NC)"
	@black app/ tests/ *.py
	@echo "$(GREEN)✅ Code formatted$(NC)"

shell: ## Access container shell
	@echo "$(BLUE)🐚 Accessing container shell...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec choyai bash

# ==============================================================================
# 💾 DATABASE OPERATIONS
# ==============================================================================

db-init: ## Initialize database
	@echo "$(BLUE)💾 Initializing database...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) run --rm choyai python tools/init_databases.py
	@echo "$(GREEN)✅ Database initialized$(NC)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)🔄 Running database migrations...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) run --rm choyai python tools/fix_database_schema.py
	@echo "$(GREEN)✅ Migrations completed$(NC)"

db-backup: ## Create database backup
	@echo "$(BLUE)💾 Creating database backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@docker-compose -f $(COMPOSE_FILE) exec choyai tar -czf /tmp/db_backup_$(TIMESTAMP).tar.gz -C /app data/databases
	@docker cp $(shell docker-compose -f $(COMPOSE_FILE) ps -q choyai):/tmp/db_backup_$(TIMESTAMP).tar.gz $(BACKUP_DIR)/
	@docker-compose -f $(COMPOSE_FILE) exec choyai rm /tmp/db_backup_$(TIMESTAMP).tar.gz
	@echo "$(GREEN)✅ Database backup created: $(BACKUP_DIR)/db_backup_$(TIMESTAMP).tar.gz$(NC)"

db-restore: ## Restore database from backup (requires BACKUP_FILE=path)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)❌ Please specify BACKUP_FILE=path/to/backup.tar.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🔄 Restoring database from $(BACKUP_FILE)...$(NC)"
	@docker cp $(BACKUP_FILE) $(shell docker-compose -f $(COMPOSE_FILE) ps -q choyai):/tmp/restore.tar.gz
	@docker-compose -f $(COMPOSE_FILE) exec choyai tar -xzf /tmp/restore.tar.gz -C /app
	@docker-compose -f $(COMPOSE_FILE) exec choyai rm /tmp/restore.tar.gz
	@echo "$(GREEN)✅ Database restored$(NC)"

# ==============================================================================
# 💾 BACKUP & RESTORE
# ==============================================================================

backup: ## Create full system backup
	@echo "$(BLUE)💾 Creating full system backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@docker-compose -f $(COMPOSE_FILE) exec choyai tar -czf /tmp/backup_$(TIMESTAMP).tar.gz -C /app data/
	@docker cp $(shell docker-compose -f $(COMPOSE_FILE) ps -q choyai):/tmp/backup_$(TIMESTAMP).tar.gz $(BACKUP_DIR)/
	@docker-compose -f $(COMPOSE_FILE) exec choyai rm /tmp/backup_$(TIMESTAMP).tar.gz
	@echo "$(GREEN)✅ Backup created: $(BACKUP_DIR)/backup_$(TIMESTAMP).tar.gz$(NC)"

backup-auto: ## Create automatic backup (for cron)
	@if [ -f "./backup_choyai.sh" ]; then \
		./backup_choyai.sh; \
	else \
		make backup; \
	fi

backup-config: ## Backup configuration files
	@echo "$(BLUE)💾 Creating configuration backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@tar -czf $(BACKUP_DIR)/config_backup_$(TIMESTAMP).tar.gz .env config/
	@echo "$(GREEN)✅ Configuration backup created: $(BACKUP_DIR)/config_backup_$(TIMESTAMP).tar.gz$(NC)"

restore: ## Restore from backup (requires BACKUP_FILE=path)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)❌ Please specify BACKUP_FILE=path/to/backup.tar.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🔄 Restoring from $(BACKUP_FILE)...$(NC)"
	@docker cp $(BACKUP_FILE) $(shell docker-compose -f $(COMPOSE_FILE) ps -q choyai):/tmp/restore.tar.gz
	@docker-compose -f $(COMPOSE_FILE) exec choyai tar -xzf /tmp/restore.tar.gz -C /app
	@docker-compose -f $(COMPOSE_FILE) exec choyai rm /tmp/restore.tar.gz
	@echo "$(GREEN)✅ System restored$(NC)"

# ==============================================================================
# 🏥 HEALTH & MAINTENANCE
# ==============================================================================

health: ## Check service health
	@echo "$(BLUE)🏥 Checking service health...$(NC)"
	@if docker-compose -f $(COMPOSE_FILE) ps | grep -q "Up"; then \
		echo "$(GREEN)✅ Container is running$(NC)"; \
		ERROR_COUNT=$$(docker-compose -f $(COMPOSE_FILE) logs --since="5m" 2>/dev/null | grep -i error | wc -l); \
		if [ $$ERROR_COUNT -gt 0 ]; then \
			echo "$(YELLOW)⚠️  Found $$ERROR_COUNT errors in recent logs$(NC)"; \
		else \
			echo "$(GREEN)✅ No recent errors in logs$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Container is not running$(NC)"; \
		echo "$(BLUE)Recent logs:$(NC)"; \
		docker-compose -f $(COMPOSE_FILE) logs --tail=20; \
	fi

health-check: ## Run comprehensive health check
	@echo "$(BLUE)🏥 Running comprehensive health check...$(NC)"
	@python3 tools/health_check.py || echo "$(YELLOW)⚠️  Health check script not found$(NC)"
	@make health

monitor: ## Start monitoring dashboard (if available)
	@echo "$(BLUE)📊 Starting monitoring...$(NC)"
	@if command -v htop >/dev/null 2>&1; then \
		echo "$(GREEN)💻 System Monitor (htop)$(NC)"; \
		htop; \
	elif command -v top >/dev/null 2>&1; then \
		echo "$(GREEN)💻 System Monitor (top)$(NC)"; \
		top; \
	else \
		echo "$(YELLOW)⚠️  No monitoring tool available$(NC)"; \
		make status; \
	fi

clean: ## Clean up Docker resources
	@echo "$(BLUE)🧹 Cleaning up Docker resources...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) down --remove-orphans
	@docker image prune -f
	@docker volume prune -f
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

deep-clean: ## Deep clean (removes all unused Docker resources)
	@echo "$(BLUE)🧹 Deep cleaning Docker resources...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) down --remove-orphans --volumes
	@docker system prune -a -f --volumes
	@echo "$(GREEN)✅ Deep cleanup completed$(NC)"

# ==============================================================================
# ⚙️  UTILITY FUNCTIONS
# ==============================================================================

check-env: ## Check if .env file exists and is configured
	@if [ ! -f ".env" ]; then \
		echo "$(RED)❌ .env file not found$(NC)"; \
		echo "$(YELLOW)Run 'make setup' or create .env file manually$(NC)"; \
		exit 1; \
	fi
	@if grep -q "your_telegram_bot_token_here" .env || grep -q "your_deepseek_api_key_here" .env; then \
		echo "$(RED)❌ Please configure your API keys in .env file$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Environment configuration validated$(NC)"

install-systemd: ## Install systemd service (requires sudo)
	@echo "$(BLUE)⚙️  Installing systemd service...$(NC)"
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(YELLOW)⚠️  This command requires sudo privileges$(NC)"; \
		echo "Run: sudo make install-systemd"; \
		exit 1; \
	fi
	@cp config/choyai-docker.service /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable choyai-docker.service
	@echo "$(GREEN)✅ Systemd service installed and enabled$(NC)"

ports: ## Show used ports
	@echo "$(BLUE)📡 Port Usage:$(NC)"
	@echo "$(GREEN)ChoyAI Services:$(NC)"
	@echo "  - Main API: 8000"
	@echo "  - Health Check: 8000/health"
	@echo ""
	@if command -v lsof >/dev/null 2>&1; then \
		echo "$(BLUE)Currently Used Ports:$(NC)"; \
		lsof -i :8000 2>/dev/null || echo "  Port 8000: Available"; \
	else \
		echo "$(YELLOW)⚠️  lsof not available for port checking$(NC)"; \
	fi

info: ## Show system information
	@echo "$(BLUE)📋 System Information:$(NC)"
	@echo "OS: $$(uname -s)"
	@echo "Architecture: $$(uname -m)"
	@echo "Kernel: $$(uname -r)"
	@echo ""
	@echo "$(BLUE)📦 Software Versions:$(NC)"
	@if command -v python3 >/dev/null 2>&1; then \
		echo "Python: $$(python3 --version)"; \
	else \
		echo "Python: Not installed"; \
	fi
	@if command -v docker >/dev/null 2>&1; then \
		echo "Docker: $$(docker --version | cut -d' ' -f3 | sed 's/,//')"; \
	else \
		echo "Docker: Not installed"; \
	fi
	@if command -v docker-compose >/dev/null 2>&1; then \
		echo "Docker Compose: $$(docker-compose --version | cut -d' ' -f3 | sed 's/,//')"; \
	else \
		echo "Docker Compose: Not installed"; \
	fi
	@echo ""
	@echo "$(BLUE)💾 Disk Usage:$(NC)"
	@df -h . | tail -1 | awk '{print "Available: " $$4 " (" $$5 " used)"}'

# ==============================================================================
# 🎯 QUICK ALIASES
# ==============================================================================

# Quick commands  
up: start ## Alias for start
down: stop ## Alias for stop
ps: status ## Alias for status
log: logs ## Alias for logs

# Testing aliases
test: test-modules ## Alias for test-modules
check: health ## Alias for health

# Development aliases
dev: dev-start ## Alias for dev-start
dev-down: dev-stop ## Alias for dev-stop

# Setup aliases
init: setup ## Alias for setup
configure: setup-env ## Alias for setup-env
