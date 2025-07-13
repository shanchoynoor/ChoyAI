#!/bin/bash
# Test script for ChoyAI Brain Docker deployment

set -e

echo "🧪 ChoyAI Brain Docker Test Suite"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing $test_name... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Tests
echo "Running Docker environment tests..."
echo

# Test 1: Docker is installed
run_test "Docker installation" "command -v docker"

# Test 2: Docker Compose is installed
run_test "Docker Compose installation" "command -v docker-compose"

# Test 3: Environment file exists
run_test "Environment file exists" "test -f .env"

# Test 4: Required directories exist
run_test "Data directory exists" "test -d data || mkdir -p data"
run_test "Logs directory exists" "test -d logs || mkdir -p logs"

# Test 5: Docker build works
echo -n "Testing Docker build... "
if docker-compose build >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 6: Docker containers can start
echo -n "Testing container startup... "
if docker-compose up -d >/dev/null 2>&1; then
    sleep 10  # Wait for startup
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Clean up
    docker-compose down >/dev/null 2>&1
else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 7: Health check endpoint (if running)
if docker-compose ps | grep -q "Up"; then
    run_test "Health check endpoint" "curl -f http://localhost:8000/health"
fi

# Test 8: Environment variables are set
echo -n "Testing environment configuration... "
if grep -q "TELEGRAM_BOT_TOKEN=" .env && grep -q "DEEPSEEK_API_KEY=" .env; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}WARN${NC} (API keys may not be configured)"
fi

# Test 9: Makefile commands work
run_test "Makefile help command" "make help"

echo
echo "================================="
echo "Test Results:"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! ChoyAI Brain is ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the issues above.${NC}"
    echo
    echo "Common solutions:"
    echo "1. Make sure Docker and Docker Compose are installed"
    echo "2. Create and configure your .env file"
    echo "3. Check that ports 8000 is not already in use"
    echo "4. Ensure you have sufficient disk space and memory"
    echo
    echo "For detailed logs, run: docker-compose logs"
    exit 1
fi
