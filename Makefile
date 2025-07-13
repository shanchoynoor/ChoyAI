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
	docker-compose -f docker-compose.dev.yml build

dev-run: ## Run in development mode with live reload
	@echo "🚀 Starting ChoyAI Brain in development mode..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development server running at http://localhost:8000"
	@echo "📊 View logs with: make dev-logs"

dev-stop: ## Stop development containers
	@echo "🛑 Stopping development containers..."
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development logs (follow)
	docker-compose -f docker-compose.dev.yml logs -f

dev-shell: ## Open shell in development container
	docker-compose -f docker-compose.dev.yml exec choyai-dev /bin/bash

# Production commands
build: ## Build production image
	@echo "🔨 Building production image..."
	docker-compose build --no-cache

run: ## Run in production mode
	@echo "🚀 Starting ChoyAI Brain in production mode..."
	docker-compose up -d
	@echo "✅ Production server started"
	@echo "📊 View logs with: make logs"

stop: ## Stop all containers
	@echo "🛑 Stopping all containers..."
	docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	docker-compose restart

logs: ## Show logs (follow)
	docker-compose logs -f choyai

logs-all: ## Show all service logs
	docker-compose logs -f

# Database and data management
backup: ## Create database backup
	@echo "💾 Creating backup..."
	@mkdir -p $(BACKUP_DIR)
	docker-compose exec choyai tar -czf /tmp/choyai_backup_$(TIMESTAMP).tar.gz /app/data
	docker cp $(CONTAINER_NAME):/tmp/choyai_backup_$(TIMESTAMP).tar.gz $(BACKUP_DIR)/
	@echo "✅ Backup created: $(BACKUP_DIR)/choyai_backup_$(TIMESTAMP).tar.gz"

restore: ## Restore from backup (usage: make restore BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Please specify backup file: make restore BACKUP=filename"; \
		exit 1; \
	fi
	@echo "♻️ Restoring from backup: $(BACKUP)"
	docker cp $(BACKUP_DIR)/$(BACKUP) $(CONTAINER_NAME):/tmp/restore.tar.gz
	docker-compose exec choyai tar -xzf /tmp/restore.tar.gz -C /
	@echo "✅ Backup restored"

init-db: ## Initialize database with schema
	@echo "🗄️ Initializing database..."
	docker-compose exec choyai python init_db.py
	@echo "✅ Database initialized"

# Maintenance commands
clean: ## Clean up containers and images
	@echo "🧹 Cleaning up..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

clean-all: ## Clean everything including volumes
	@echo "🧹 Cleaning everything..."
	docker-compose down --rmi all --volumes --remove-orphans
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
	docker-compose ps

health: ## Check health status
	@echo "🏥 Health Check:"
	docker-compose exec choyai curl -f http://localhost:8000/health || echo "❌ Health check failed"

stats: ## Show container resource usage
	docker stats $(CONTAINER_NAME) --no-stream

shell: ## Open shell in production container
	docker-compose exec choyai /bin/bash

# Testing
test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose exec choyai python -m pytest tests/ -v

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
		cp .env.example .env; \
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

# Security
security-scan: ## Run security scan on image
	@echo "🔒 Running security scan..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(pwd):/app -w /app \
		aquasec/trivy image $(IMAGE_NAME):latest

# Monitoring
monitor: ## Monitor logs in real-time
	@echo "📊 Monitoring ChoyAI Brain..."
	docker-compose logs -f --tail=100

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
