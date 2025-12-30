#!/bin/bash

set -e  # Exit on error

echo "=========================================="
echo "Trading Agent Service Setup"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Step 1: Check for .env file
echo -e "${YELLOW}[1/7] Checking for .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with your Alpaca API credentials."
    echo "You can copy .env.example and fill in your keys:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi
echo -e "${GREEN}✓ .env file found${NC}"
echo ""

# Step 2: Check Python
echo -e "${YELLOW}[2/7] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION installed${NC}"
echo ""

# Step 3: Check/Install dependencies
echo -e "${YELLOW}[3/7] Checking Python dependencies...${NC}"
if ! python3 -c "import alpaca_trade_api" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
echo ""

# Step 4: Update service file paths
echo -e "${YELLOW}[4/7] Updating service file paths...${NC}"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|g" trading-agent.service
sed -i "s|EnvironmentFile=.*|EnvironmentFile=$SCRIPT_DIR/.env|g" trading-agent.service
sed -i "s|ExecStart=.*|ExecStart=$(which python3) $SCRIPT_DIR/trading_agent_realtime.py|g" trading-agent.service
echo -e "${GREEN}✓ Service file updated with current paths${NC}"
echo ""

# Step 5: Install systemd files
echo -e "${YELLOW}[5/7] Installing systemd service and timer...${NC}"
cp trading-agent.service /etc/systemd/system/
cp trading-agent.timer /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓ Service files installed${NC}"
echo ""

# Step 6: Enable and start timer
echo -e "${YELLOW}[6/7] Enabling and starting timer...${NC}"
systemctl enable trading-agent.timer
systemctl start trading-agent.timer
echo -e "${GREEN}✓ Timer enabled and started${NC}"
echo ""

# Step 7: Show status
echo -e "${YELLOW}[7/7] Service status:${NC}"
echo ""
systemctl status trading-agent.timer --no-pager
echo ""

echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  - View timer status:        systemctl status trading-agent.timer"
echo "  - View next scheduled run:  systemctl list-timers trading-agent.timer"
echo "  - Run service manually:     systemctl start trading-agent.service"
echo "  - View logs:                journalctl -u trading-agent.service -f"
echo "  - View recent logs:         journalctl -u trading-agent.service -n 50"
echo "  - Stop timer:               systemctl stop trading-agent.timer"
echo "  - Disable timer:            systemctl disable trading-agent.timer"
echo ""
echo "Next scheduled run:"
systemctl list-timers trading-agent.timer --no-pager | grep trading-agent
echo ""
