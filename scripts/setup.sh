#!/bin/bash

# Trading Bot Setup Script
# This script sets up the development environment for the trading bot

set -e  # Exit on error

echo "========================================"
echo "Trading Bot - Setup Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.9+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment recreated${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p logs
mkdir -p htmlcov
echo -e "${GREEN}✓ Directories created${NC}"

# Setup .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Setting up environment variables..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your Alpaca API credentials${NC}"
else
    echo -e "${YELLOW}.env file already exists (not overwriting)${NC}"
fi

# Check .gitignore
echo ""
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠️  Warning: .gitignore not found${NC}"
else
    echo -e "${GREEN}✓ .gitignore exists${NC}"
fi

# Run initial tests
echo ""
echo "Running tests to verify setup..."
if pytest -q tests/; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed (this is expected if API keys aren't configured)${NC}"
fi

# Display next steps
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Alpaca API credentials"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo ""
echo "3. Run tests:"
echo "   pytest -v"
echo ""
echo "4. Run the trading bot:"
echo "   python main.py"
echo ""
echo "5. Run backtests:"
echo "   python backtest.py"
echo ""
echo "For more information, see README.md"
echo ""