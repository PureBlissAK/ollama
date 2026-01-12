#!/bin/bash
# Bootstrap script for Ollama development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Ollama Bootstrap Script${NC}"
echo -e "${YELLOW}Initializing local AI development environment...${NC}\n"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites met${NC}\n"
}

# Setup Python environment
setup_python_env() {
    echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    source venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements/core.txt
    pip install -r requirements/dev.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}\n"
}

# Setup Git hooks
setup_git_hooks() {
    echo -e "${YELLOW}🔗 Setting up Git hooks...${NC}"
    
    if ! command -v pre-commit &> /dev/null; then
        pip install pre-commit
    fi
    
    pre-commit install
    echo -e "${GREEN}✓ Git hooks installed${NC}\n"
}

# Configure environment
setup_environment() {
    echo -e "${YELLOW}⚙️  Configuring environment...${NC}"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created (review and update as needed)${NC}"
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
    
    echo -e ""
}

# Initialize database
init_database() {
    echo -e "${YELLOW}🗄️  Initializing database...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d postgres redis
        sleep 5
        # Run migrations (placeholder)
        echo -e "${GREEN}✓ Database containers started${NC}"
    fi
    
    echo -e ""
}

# Download models
download_models() {
    read -p "Download recommended models? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}📥 Downloading models...${NC}"
        python -m ollama.cli pull llama2:7b-chat
        echo -e "${GREEN}✓ Models downloaded${NC}"
    fi
    echo -e ""
}

# Run tests
run_tests() {
    echo -e "${YELLOW}🧪 Running tests...${NC}"
    pytest tests/ -v --tb=short --cov=ollama
    echo -e "${GREEN}✓ Tests completed${NC}\n"
}

# Main execution
main() {
    check_prerequisites
    setup_python_env
    setup_git_hooks
    setup_environment
    init_database
    
    if [ "${1:-}" = "--production" ]; then
        echo -e "${YELLOW}🔒 Production mode enabled${NC}"
        echo -e "${GREEN}✓ To start production stack, run:${NC}"
        echo -e "  ${YELLOW}docker-compose -f docker-compose.prod.yml up -d${NC}\n"
    else
        read -p "Initialize database and download models? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            init_database
            download_models
        fi
    fi
    
    echo -e "${GREEN}✨ Bootstrap complete!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Review and update .env if needed"
    echo -e "  2. Start development: docker-compose up -d && python -m ollama.server"
    echo -e "  3. API will be available at: http://localhost:8000"
    echo -e "  4. Health check: curl http://localhost:8000/health"
    echo -e ""
}

main "$@"
