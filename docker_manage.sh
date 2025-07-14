#!/bin/bash
# ChoyAI Docker Management Script
# Easy commands to manage your ChoyAI Docker deployment

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE="config/docker-compose.yml"

show_help() {
    echo "🐳 ChoyAI Docker Management"
    echo "=========================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start      Start ChoyAI services"
    echo "  stop       Stop ChoyAI services"
    echo "  restart    Restart ChoyAI services"
    echo "  status     Show service status"
    echo "  logs       Show live logs"
    echo "  logs-tail  Show last 50 log lines"
    echo "  update     Pull latest code and rebuild"
    echo "  backup     Create database backup"
    echo "  shell      Access container shell"
    echo "  cleanup    Remove old images and containers"
    echo "  rebuild    Force rebuild without cache"
    echo "  health     Check service health"
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
}

start_services() {
    echo -e "${BLUE}🚀 Starting ChoyAI services...${NC}"
    docker-compose -f $COMPOSE_FILE up -d
    echo -e "${GREEN}✅ Services started${NC}"
}

stop_services() {
    echo -e "${BLUE}🛑 Stopping ChoyAI services...${NC}"
    docker-compose -f $COMPOSE_FILE down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${BLUE}🔄 Restarting ChoyAI services...${NC}"
    docker-compose -f $COMPOSE_FILE restart
    echo -e "${GREEN}✅ Services restarted${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo -e "${BLUE}🔍 Container Details:${NC}"
    docker-compose -f $COMPOSE_FILE top
}

show_logs() {
    echo -e "${BLUE}📋 Live logs (Ctrl+C to exit):${NC}"
    docker-compose -f $COMPOSE_FILE logs -f
}

show_logs_tail() {
    echo -e "${BLUE}📋 Last 50 log lines:${NC}"
    docker-compose -f $COMPOSE_FILE logs --tail=50
}

update_services() {
    echo -e "${BLUE}🔄 Updating ChoyAI...${NC}"
    
    # Pull latest code
    echo -e "${BLUE}📥 Pulling latest code...${NC}"
    git pull
    
    # Rebuild and restart
    echo -e "${BLUE}🔨 Rebuilding services...${NC}"
    docker-compose -f $COMPOSE_FILE up -d --build
    
    echo -e "${GREEN}✅ Update completed${NC}"
}

backup_data() {
    echo -e "${BLUE}💾 Creating backup...${NC}"
    
    if [ -f "./backup_choyai.sh" ]; then
        ./backup_choyai.sh
    else
        # Simple backup
        BACKUP_DIR="./backups"
        DATE=$(date +%Y%m%d_%H%M%S)
        mkdir -p "$BACKUP_DIR"
        
        # Copy databases
        docker-compose -f $COMPOSE_FILE exec choyai cp -r /app/data/databases /tmp/backup_$DATE
        docker cp $(docker-compose -f $COMPOSE_FILE ps -q choyai):/tmp/backup_$DATE $BACKUP_DIR/
        
        echo -e "${GREEN}✅ Backup created in $BACKUP_DIR/backup_$DATE${NC}"
    fi
}

access_shell() {
    echo -e "${BLUE}🐚 Accessing container shell...${NC}"
    docker-compose -f $COMPOSE_FILE exec choyai bash
}

cleanup_docker() {
    echo -e "${BLUE}🧹 Cleaning up Docker resources...${NC}"
    
    # Remove stopped containers
    docker-compose -f $COMPOSE_FILE down --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

rebuild_services() {
    echo -e "${BLUE}🔨 Force rebuilding services...${NC}"
    
    # Stop services
    docker-compose -f $COMPOSE_FILE down
    
    # Remove existing images
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    # Start services
    docker-compose -f $COMPOSE_FILE up -d
    
    echo -e "${GREEN}✅ Rebuild completed${NC}"
}

check_health() {
    echo -e "${BLUE}🏥 Checking service health...${NC}"
    
    # Check if container is running
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Container is running${NC}"
        
        # Check logs for errors
        ERROR_COUNT=$(docker-compose -f $COMPOSE_FILE logs --since="5m" | grep -i error | wc -l)
        if [ $ERROR_COUNT -gt 0 ]; then
            echo -e "${YELLOW}⚠️  Found $ERROR_COUNT errors in recent logs${NC}"
        else
            echo -e "${GREEN}✅ No recent errors in logs${NC}"
        fi
        
        # Check memory usage
        echo -e "${BLUE}💾 Memory usage:${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        
    else
        echo -e "${RED}❌ Container is not running${NC}"
        echo -e "${BLUE}Recent logs:${NC}"
        docker-compose -f $COMPOSE_FILE logs --tail=20
    fi
}

# Main script
check_docker

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-tail)
        show_logs_tail
        ;;
    update)
        update_services
        ;;
    backup)
        backup_data
        ;;
    shell)
        access_shell
        ;;
    cleanup)
        cleanup_docker
        ;;
    rebuild)
        rebuild_services
        ;;
    health)
        check_health
        ;;
    *)
        show_help
        ;;
esac
