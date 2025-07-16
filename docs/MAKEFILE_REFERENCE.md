# ChoyAI Quick Reference Card
# ==========================

# 🚀 QUICK START
make setup          # Complete production setup (run with sudo)
make deploy          # Deploy ChoyAI with validation  
make start           # Start services
make logs            # View live logs

# 📊 MONITORING  
make status          # Show service status and resource usage
make health          # Check service health
make logs-tail       # Show last 50 log lines

# 🔄 MANAGEMENT
make stop            # Stop services
make restart         # Restart services  
make update          # Pull latest code and restart
make backup          # Create database backup

# 🛠️ DEVELOPMENT
make dev-start       # Start development environment
make dev-stop        # Stop development environment
make dev-logs        # Show development logs
make shell           # Access container shell

# 💾 DATABASE
make db-init         # Initialize database
make db-migrate      # Run database migrations

# 🧹 MAINTENANCE  
make clean           # Clean up Docker resources
make rebuild         # Force rebuild image (no cache)

# Examples:
# sudo make setup                    # Initial setup
# make deploy                        # Deploy to production
# make start && make logs            # Start and view logs
# make update                        # Update to latest version
