# ChoyAI Brain - Docker Management Makefile
# Usage: make [target]

.PHONY: help build run stop logs clean dev test deploy backup restore

# Variables
IMAGE_NAME = choyai-brain
CONTAINER_NAME = choyai-brain
DEV_CONTAINER_NAME = choyai-brain-dev
BACKUP_DIR = ./backups
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)

# Default target
help: ## Show this help message
	@echo "ChoyAI Brain - Docker Management"
	@echo "================================"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
dev-build: ## Build development image
	@echo "🔨 Building development image..."
	docker-compose -f config/docker-compose.dev.yml build

dev-run: ## Run in development mode with live reload
	@echo "🚀 Starting ChoyAI Brain in development mode..."
	docker-compose -f config/docker-compose.dev.yml up -d
	@echo "✅ Development server running at http://localhost:8000"
	@echo "📊 View logs with: make dev-logs"

dev-stop: ## Stop development containers
	@echo "🛑 Stopping development containers..."
	docker-compose -f config/docker-compose.dev.yml down

dev-logs: ## Show development logs (follow)
	docker-compose -f config/docker-compose.dev.yml logs -f

dev-shell: ## Open shell in development container
	docker-compose -f config/docker-compose.dev.yml exec choyai-dev /bin/bash

# Production commands
build: ## Build production image
	@echo "🔨 Building production image..."
	docker-compose -f config/docker-compose.yml build --no-cache

run: ## Run in production mode
	@echo "🚀 Starting ChoyAI Brain in production mode..."
	@make env-fix-location
	docker-compose -f config/docker-compose.yml up -d
	@echo "✅ Production server started"
	@echo "📊 View logs with: make logs"

start: ## Alias for run command
	@make run

stop: ## Stop all containers
	@echo "🛑 Stopping all containers..."
	docker-compose -f config/docker-compose.yml down

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	docker-compose -f config/docker-compose.yml restart

logs: ## Show logs (follow)
	docker-compose -f config/docker-compose.yml logs -f choyai

logs-all: ## Show all service logs
	docker-compose -f config/docker-compose.yml logs -f

# Database and data management
backup: ## Create database backup
	@echo "💾 Creating backup..."
	@mkdir -p $(BACKUP_DIR)
	docker-compose -f config/docker-compose.yml exec choyai tar -czf /tmp/choyai_backup_$(TIMESTAMP).tar.gz /app/data
	docker cp $(CONTAINER_NAME):/tmp/choyai_backup_$(TIMESTAMP).tar.gz $(BACKUP_DIR)/
	@echo "✅ Backup created: $(BACKUP_DIR)/choyai_backup_$(TIMESTAMP).tar.gz"

restore: ## Restore from backup (usage: make restore BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Please specify backup file: make restore BACKUP=filename"; \
		exit 1; \
	fi
	@echo "♻️ Restoring from backup: $(BACKUP)"
	docker cp $(BACKUP_DIR)/$(BACKUP) $(CONTAINER_NAME):/tmp/restore.tar.gz
	docker-compose -f config/docker-compose.yml exec choyai tar -xzf /tmp/restore.tar.gz -C /
	@echo "✅ Backup restored"

init-db: ## Initialize database with schema
	@echo "🗄️ Initializing database..."
	docker-compose -f config/docker-compose.yml exec choyai python tools/init_db.py
	@echo "✅ Database initialized"

# Maintenance commands
clean: ## Clean up containers and images
	@echo "🧹 Cleaning up..."
	docker-compose -f config/docker-compose.yml down --rmi all --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

clean-all: ## Clean everything including volumes
	@echo "🧹 Cleaning everything..."
	docker-compose -f config/docker-compose.yml down --rmi all --volumes --remove-orphans
	docker volume prune -f
	docker system prune -a -f
	@echo "✅ Complete cleanup done"

update: ## Update and rebuild
	@echo "🔄 Updating ChoyAI Brain..."
	git pull
	make stop
	make build
	make run
	@echo "✅ Update complete"

# Monitoring and debugging
status: ## Show container status
	@echo "📊 Container Status:"
	docker-compose -f config/docker-compose.yml ps

health: ## Check health status
	@echo "🏥 Health Check:"
	docker-compose -f config/docker-compose.yml exec choyai curl -f http://localhost:8000/health || echo "❌ Health check failed"

stats: ## Show container resource usage
	docker stats $(CONTAINER_NAME) --no-stream

shell: ## Open shell in production container
	docker-compose -f config/docker-compose.yml exec choyai /bin/bash

# Testing
test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose -f config/docker-compose.yml exec choyai python -m pytest tests/ -v

test-build: ## Build and test
	make build
	make test

# Deployment helpers
deploy-vps: ## Deploy to VPS (requires .env file)
	@echo "🚀 Deploying to VPS..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please create it first."; \
		exit 1; \
	fi
	make stop || true
	make build
	make run
	@echo "✅ Deployment complete"

setup-env: ## Create .env template
	@echo "📝 Creating .env template..."
	@if [ ! -f .env ]; then \
		cp config/.env.example .env; \
		echo "✅ .env file created from template"; \
		echo "📝 Please edit .env with your API keys"; \
	else \
		echo "⚠️ .env file already exists"; \
	fi

# Quick start commands
quick-start: setup-env build run ## Quick start (setup + build + run)
	@echo "🎉 ChoyAI Brain is running!"
	@echo "📱 Add your bot token to .env and restart"

dev-start: setup-env dev-build dev-run ## Quick development start
	@echo "🎉 ChoyAI Brain development environment is running!"

quick-fix: ## Run automated fix for common deployment issues
	@echo "🔧 Running ChoyAI Quick Fix..."
	@bash deployment/quick-fix.sh

# Security
security-scan: ## Run security scan on image
	@echo "🔒 Running security scan..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(pwd):/app -w /app \
		aquasec/trivy image $(IMAGE_NAME):latest

# Monitoring
monitor: ## Monitor logs in real-time
	@echo "📊 Monitoring ChoyAI Brain..."
	docker-compose -f config/docker-compose.yml logs -f --tail=100

install-deps: ## Install system dependencies for VPS
	@echo "📦 Installing system dependencies..."
	sudo apt-get update
	@echo "🔍 Checking Docker installation..."
	@if command -v docker >/dev/null 2>&1; then \
		echo "✅ Docker already installed"; \
		docker --version; \
	else \
		echo "📦 Installing Docker..."; \
		sudo apt-get install -y docker.io; \
	fi
	@if command -v docker-compose >/dev/null 2>&1; then \
		echo "✅ Docker Compose already installed"; \
		docker-compose --version; \
	else \
		echo "📦 Installing Docker Compose..."; \
		sudo apt-get install -y docker-compose; \
	fi
	sudo apt-get install -y curl git
	sudo systemctl enable docker
	sudo systemctl start docker
	sudo usermod -aG docker admin
	@echo "✅ Dependencies installed. Please log out and back in."

# Production deployment with SSL
deploy-ssl: ## Deploy with SSL (nginx + certbot)
	@echo "🔒 Deploying with SSL..."
	docker-compose --profile webhook up -d
	@echo "✅ SSL deployment complete"

fix-docker: ## Fix Docker permissions and conflicts
	@echo "🔧 Fixing Docker setup..."
	sudo systemctl enable docker
	sudo systemctl start docker
	sudo usermod -aG docker admin
	@echo "💡 Please log out and back in to apply Docker group changes"
	@echo "🔍 Current Docker status:"
	sudo systemctl status docker --no-pager -l

# Debugging and troubleshooting
debug: ## Show detailed container and error information
	@echo "🔍 ChoyAI Debug Information"
	@echo "=========================="
	@echo ""
	@echo "📊 Container Status:"
	docker-compose -f config/docker-compose.yml ps
	@echo ""
	@echo "🔍 Main Container Logs (last 50 lines):"
	docker-compose -f config/docker-compose.yml logs --tail=50 choyai
	@echo ""
	@echo "💾 Resource Usage:"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "No running containers"
	@echo ""
	@echo "🌐 Network Status:"
	docker network ls | grep choyai || echo "No ChoyAI networks found"

logs-error: ## Show only error logs from main container
	@echo "❌ ChoyAI Error Logs:"
	docker-compose -f config/docker-compose.yml logs choyai | grep -i error || echo "No error logs found"

logs-tail: ## Show recent logs from main container
	@echo "📋 Recent ChoyAI Logs:"
	docker-compose -f config/docker-compose.yml logs --tail=20 choyai

restart-main: ## Restart only the main ChoyAI container
	@echo "🔄 Restarting ChoyAI main container..."
	docker-compose -f config/docker-compose.yml restart choyai
	@echo "✅ Main container restarted"

force-rebuild: ## Force rebuild without cache and restart
	@echo "🔄 Force rebuilding ChoyAI (no cache)..."
	make force-stop
	docker-compose -f config/docker-compose.yml build --no-cache --pull
	make run
	@echo "✅ Force rebuild complete"

check-imports: ## Check if TaskType is properly exported
	@echo "🔍 Checking TaskType import..."
	docker-compose -f config/docker-compose.yml exec choyai python -c "from app.core.ai_providers import TaskType; print('✅ TaskType import successful')" || echo "❌ TaskType import failed"

# Container management
force-stop: ## Force stop and remove all containers
	@echo "💀 Force stopping and removing all containers..."
	docker-compose -f config/docker-compose.yml down --volumes --remove-orphans
	docker container rm -f choyai-brain choyai-redis choyai-postgres 2>/dev/null || true
	@echo "✅ All containers force removed"

clean-containers: ## Remove conflicting containers
	@echo "🧹 Cleaning conflicting containers..."
	@docker container rm -f choyai-brain choyai-redis choyai-postgres 2>/dev/null || echo "No conflicting containers found"
	@echo "✅ Container cleanup complete"

check-env: ## Check if .env file exists and has required variables
	@echo "🔍 Checking environment configuration..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found!"; \
		echo "📝 Creating from template..."; \
		cp config/.env.example .env; \
		echo "✅ .env file created from template"; \
		echo "⚠️  IMPORTANT: Please edit .env with your API keys before running!"; \
		echo "📝 Required: TELEGRAM_BOT_TOKEN and DEEPSEEK_API_KEY"; \
		echo "💡 Edit with: nano .env"; \
		exit 1; \
	fi
	@echo "✅ .env file exists"
	@if grep -q "your_bot_token_here\|your_deepseek_key_here\|your_.*_here" .env; then \
		echo "⚠️  WARNING: Placeholder values detected in .env file!"; \
		echo "📝 Please replace placeholder values with real API keys"; \
		echo "💡 Edit with: nano .env"; \
		exit 1; \
	fi
	@if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || ! grep -q "DEEPSEEK_API_KEY=" .env; then \
		echo "⚠️  .env file exists but may be missing required variables"; \
		echo "📝 Required: TELEGRAM_BOT_TOKEN and DEEPSEEK_API_KEY"; \
		exit 1; \
	fi
	@echo "✅ Environment configuration looks good"

show-env: ## Show current environment variables
	@echo "🔍 Environment Variables Status:"
	@echo "================================"
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		echo "📄 .env file contents:"; \
		echo ""; \
		grep -E "(TELEGRAM_BOT_TOKEN|DEEPSEEK_API_KEY)" .env | sed 's/=.*/=***HIDDEN***/' || echo "⚠️  No API keys found in .env"; \
		echo ""; \
	else \
		echo "❌ .env file not found"; \
	fi
	@echo "🔍 Docker Compose Environment:"
	@docker-compose -f config/docker-compose.yml config | grep -E "(TELEGRAM_BOT_TOKEN|DEEPSEEK_API_KEY)" || echo "⚠️  Variables not detected by Docker Compose"

fix-env: ## Fix environment variable issues
	@echo "🔧 Fixing environment variables..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp config/.env.example .env; \
	fi
	@echo "🔍 Current .env status:"
	@ls -la .env
	@echo "📄 Current working directory:"
	@pwd
	@echo "⚠️  Make sure to edit .env with your real API keys!"
	@echo "💡 Run: nano .env"

# Enhanced deployment commands
safe-restart: ## Safe restart - stop, clean, and start
	@echo "🔄 Performing safe restart..."
	@make force-stop
	@make clean-containers
	@make check-env
	@make env-fix-location
	@make run
	@echo "✅ Safe restart complete"

deploy-fresh: ## Fresh deployment - clean everything and deploy
	@echo "🚀 Performing fresh deployment..."
	@make force-stop
	@make clean-containers  
	@make check-env
	@make env-fix-location
	@make build
	@make run
	@echo "✅ Fresh deployment complete"

env-fix-location: ## Fix .env file location for Docker Compose
	@echo "🔧 Fixing .env file location..."
	@if [ -f .env ] && [ ! -f config/.env ]; then \
		echo "📝 Copying .env to config/ directory..."; \
		cp .env config/.env; \
		echo "✅ .env file copied to config/.env"; \
	elif [ -f .env ] && [ -f config/.env ]; then \
		echo "🔄 Updating config/.env with latest .env..."; \
		cp .env config/.env; \
		echo "✅ config/.env updated"; \
	else \
		echo "⚠️  .env file not found in root directory"; \
	fi

force-start: ## Force start without environment checks (for when .env has real keys)
	@echo "🚀 Force starting ChoyAI Brain (bypassing checks)..."
	@make force-stop
	@make clean-containers
	@make env-fix-location
	@make run-no-check
	@echo "✅ Force start complete"

run-no-check: ## Run without environment validation
	@echo "🚀 Starting ChoyAI Brain (no validation)..."
	@make env-fix-location
	docker-compose -f config/docker-compose.yml up -d
	@echo "✅ Production server started"
	@echo "📊 View logs with: make logs"

nuclear-clean: ## Nuclear option - stop and remove ALL containers and networks
	@echo "💀 NUCLEAR CLEANUP - Stopping and removing ALL containers..."
	@echo "⚠️  This will stop ALL Docker containers on the system!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker stop $$(docker ps -aq) 2>/dev/null || true; \
		docker rm $$(docker ps -aq) 2>/dev/null || true; \
		docker network prune -f; \
		docker volume prune -f; \
		echo "✅ All containers removed"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

clean-duplicates: ## Clean duplicate containers and conflicting services
	@echo "🧹 Cleaning duplicate containers..."
	@echo "🛑 Stopping conflicting containers..."
	@docker stop choyai-brain choyai-redis choyai-postgres 2>/dev/null || true
	@docker stop choynews-bot choynews-redis choynews-postgres 2>/dev/null || true
	@echo "🗑️ Removing stopped containers..."
	@docker rm choyai-brain choyai-redis choyai-postgres 2>/dev/null || true
	@docker rm choynews-bot choynews-redis choynews-postgres 2>/dev/null || true
	@echo "🌐 Cleaning networks..."
	@docker network prune -f
	@echo "✅ Duplicate cleanup complete"

fresh-start: ## Complete fresh start - clean duplicates and restart ChoyAI
	@echo "🔄 Performing complete fresh start..."
	@make clean-duplicates
	@make env-fix-location
	@make build
	@make run-no-check
	@echo "✅ Fresh start complete"

fix-personas: ## Fix AVAILABLE_PERSONAS format in .env file
	@echo "🔧 Fixing AVAILABLE_PERSONAS format..."
	@if [ -f .env ]; then \
		if grep -q 'AVAILABLE_PERSONAS=\[' .env; then \
			echo "📝 Fixing JSON format for AVAILABLE_PERSONAS..."; \
			sed -i 's/AVAILABLE_PERSONAS=\[.*\]/AVAILABLE_PERSONAS=choy,stark,rose,sherlock,joker,hermione,harley/' .env; \
			echo "✅ AVAILABLE_PERSONAS fixed"; \
		else \
			echo "⚠️  AVAILABLE_PERSONAS not found or already in correct format"; \
		fi; \
		if [ -f config/.env ]; then \
			cp .env config/.env; \
			echo "✅ Updated config/.env"; \
		fi; \
	else \
		echo "❌ .env file not found"; \
	fi

quick-fix-restart: ## Quick fix for personas and restart
	@echo "🚀 Quick fixing personas issue and restarting..."
	@make fix-personas
	@make env-fix-location
	@make restart-main
	@echo "✅ Quick fix complete"

check-env-format: ## Check and show .env format issues
	@echo "🔍 Checking .env file format..."
	@if [ -f .env ]; then \
		echo "📄 Current .env file content (problematic lines):"; \
		grep -n "AVAILABLE_PERSONAS\|TASK_ROUTING\|ALLOWED_USER_IDS" .env || echo "No problematic lines found"; \
		echo ""; \
		echo "🔍 Checking for JSON format issues..."; \
		grep -E "\[|\]|\{|\}" .env || echo "No JSON brackets found"; \
	else \
		echo "❌ .env file not found"; \
	fi

fix-env-format: ## Fix all .env formatting issues comprehensively
	@echo "🔧 Comprehensive .env format fixing..."
	@if [ -f .env ]; then \
		echo "📝 Creating backup..."; \
		cp .env .env.backup; \
		echo "🔧 Fixing AVAILABLE_PERSONAS..."; \
		sed -i 's/AVAILABLE_PERSONAS=\[.*\]/AVAILABLE_PERSONAS=choy,stark,rose,sherlock,joker,hermione,harley/' .env; \
		echo "🔧 Fixing ALLOWED_USER_IDS (if exists)..."; \
		sed -i 's/ALLOWED_USER_IDS=.*/ALLOWED_USER_IDS=/' .env; \
		echo "🔧 Removing any JSON brackets..."; \
		sed -i 's/\[//g; s/\]//g; s/"//g' .env; \
		echo "🔧 Fixing task routing (if exists)..."; \
		sed -i 's/TASK_ROUTING_.*=.*//' .env; \
		echo "✅ .env format fixed"; \
		echo "📄 Updated AVAILABLE_PERSONAS line:"; \
		grep "AVAILABLE_PERSONAS" .env || echo "AVAILABLE_PERSONAS not found"; \
		if [ -f config/.env ]; then \
			cp .env config/.env; \
			echo "✅ Updated config/.env"; \
		fi; \
	else \
		echo "❌ .env file not found"; \
	fi

nuclear-fix: ## Nuclear fix - completely rebuild .env and restart
	@echo "💥 NUCLEAR FIX - Rebuilding .env from scratch..."
	@if [ -f .env ]; then \
		echo "💾 Backing up current .env..."; \
		cp .env .env.nuclear.backup; \
		echo "🔑 Extracting API keys..."; \
		TELEGRAM_TOKEN=$$(grep "TELEGRAM_BOT_TOKEN=" .env | cut -d'=' -f2); \
		DEEPSEEK_KEY=$$(grep "DEEPSEEK_API_KEY=" .env | cut -d'=' -f2); \
		echo "📝 Creating clean .env..."; \
		cp config/.env.example .env; \
		if [ -n "$$TELEGRAM_TOKEN" ] && [ "$$TELEGRAM_TOKEN" != "your_telegram_bot_token_here" ]; then \
			sed -i "s/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$$TELEGRAM_TOKEN/" .env; \
			echo "✅ Telegram token preserved"; \
		fi; \
		if [ -n "$$DEEPSEEK_KEY" ] && [ "$$DEEPSEEK_KEY" != "your_deepseek_api_key_here" ]; then \
			sed -i "s/DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$$DEEPSEEK_KEY/" .env; \
			echo "✅ DeepSeek key preserved"; \
		fi; \
		sed -i 's/AVAILABLE_PERSONAS=.*/AVAILABLE_PERSONAS=choy,stark,rose,sherlock,joker,hermione,harley/' .env; \
		cp .env config/.env; \
		echo "✅ Clean .env created and copied to config/"; \
		make restart-main; \
	else \
		echo "❌ .env file not found"; \
	fi

env-debug: ## Run comprehensive environment debugging
	@echo "🔍 Running environment diagnostics..."
	@bash deployment/env-fix.sh
