# ChoyAI Brain - Comprehensive Docker Management Makefile
# Usage: make [target]

.PHONY: help setup deploy start stop restart status logs build clean backup health update shell

# Variables
COMPOSE_FILE = config/docker-compose.yml
DEV_COMPOSE_FILE = config/docker-compose.dev.yml
CONTAINER_NAME = choyai-brain
IMAGE_NAME = choyai-brain:latest
BACKUP_DIR = ./backups
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Default target
help: ## Show this help message
	@echo "🐳 ChoyAI Brain - Docker Management"
	@echo "=================================="
	@echo "Available commands:"
	@echo ""
	@printf "$(BLUE)Production Commands:$(NC)\n"
	@grep -E '^(setup|deploy|start|stop|restart|status|logs|update):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@printf "$(BLUE)Development Commands:$(NC)\n"
	@grep -E '^(dev-|build|shell):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@printf "$(BLUE)Maintenance Commands:$(NC)\n"
	@grep -E '^(backup|clean|health):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Setup and deployment
setup: ## Complete production setup (requires sudo)
	@echo "🚀 Setting up ChoyAI for production..."
	@if [ "$$EUID" -ne 0 ]; then \
		echo "$(YELLOW)⚠️  This command requires sudo privileges$(NC)"; \
		echo "Run: sudo make setup"; \
		exit 1; \
	fi
	@bash deployment/setup_production.sh

deploy: check-env ## Deploy ChoyAI with Docker (validates config)
	@echo "🚀 Deploying ChoyAI..."
	@bash deployment/deploy_docker.sh

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

# Monitoring and logs
status: ## Show service status
	@echo "$(BLUE)📊 Service Status:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(BLUE)💾 Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -2

logs: ## Show live logs (Ctrl+C to exit)
	@echo "$(BLUE)📋 Live logs (Ctrl+C to exit):$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs -f

logs-tail: ## Show last 50 log lines
	@echo "$(BLUE)� Last 50 log lines:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs --tail=50

# Build and update
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
	@docker-compose -f $(COMPOSE_FILE) up -d --build
	@echo "$(GREEN)✅ Update completed$(NC)"

# Development
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

shell: ## Access container shell
	@echo "$(BLUE)🐚 Accessing container shell...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec choyai bash

# Database operations
db-init: ## Initialize database
	@echo "$(BLUE)💾 Initializing database...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) run --rm choyai python tools/init_databases.py
	@echo "$(GREEN)✅ Database initialized$(NC)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)🔄 Running database migrations...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) run --rm choyai python tools/fix_database_schema.py
	@echo "$(GREEN)✅ Migrations completed$(NC)"

# Backup and restore
backup: ## Create database backup
	@echo "$(BLUE)💾 Creating backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@docker-compose -f $(COMPOSE_FILE) exec choyai tar -czf /tmp/backup_$(TIMESTAMP).tar.gz -C /app data/databases
	@docker cp $(shell docker-compose -f $(COMPOSE_FILE) ps -q choyai):/tmp/backup_$(TIMESTAMP).tar.gz $(BACKUP_DIR)/
	@docker-compose -f $(COMPOSE_FILE) exec choyai rm /tmp/backup_$(TIMESTAMP).tar.gz
	@echo "$(GREEN)✅ Backup created: $(BACKUP_DIR)/backup_$(TIMESTAMP).tar.gz$(NC)"

backup-auto: ## Create automatic backup (for cron)
	@if [ -f "./backup_choyai.sh" ]; then \
		./backup_choyai.sh; \
	else \
		make backup; \
	fi

# Health and maintenance
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

clean: ## Clean up Docker resources
	@echo "$(BLUE)🧹 Cleaning up Docker resources...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) down --remove-orphans
	@docker image prune -f
	@docker volume prune -f
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

# Utility targets
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
	@if [ "$$EUID" -ne 0 ]; then \
		echo "$(YELLOW)⚠️  This command requires sudo privileges$(NC)"; \
		echo "Run: sudo make install-systemd"; \
		exit 1; \
	fi
	@cp config/choyai-docker.service /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable choyai-docker.service
	@echo "$(GREEN)✅ Systemd service installed and enabled$(NC)"

# Quick commands  
up: start ## Alias for start
down: stop ## Alias for stop
ps: status ## Alias for status
