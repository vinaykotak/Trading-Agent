#!/bin/bash

# Test runner script for trading agent

set -e

echo "=========================================="
echo "Trading Agent Test Suite"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip3 install pytest pytest-cov pytest-mock
    echo ""
fi

# Run tests with different verbosity levels based on argument
case "${1:-normal}" in
    "verbose"|"-v")
        echo -e "${YELLOW}Running tests in verbose mode...${NC}"
        python3 -m pytest test_trading_agent.py -v --tb=short
        ;;
    "coverage"|"-c")
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        python3 -m pytest test_trading_agent.py -v --cov=trading_agent_realtime --cov-report=term-missing --cov-report=html
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick"|"-q")
        echo -e "${YELLOW}Running tests in quiet mode...${NC}"
        python3 -m pytest test_trading_agent.py -q
        ;;
    "failed"|"-f")
        echo -e "${YELLOW}Running only failed tests...${NC}"
        python3 -m pytest test_trading_agent.py --lf -v
        ;;
    *)
        echo -e "${YELLOW}Running tests...${NC}"
        python3 -m pytest test_trading_agent.py --tb=short
        ;;
esac

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✓ All tests passed!"
    echo -e "==========================================${NC}"
else
    echo -e "${RED}=========================================="
    echo "✗ Some tests failed"
    echo -e "==========================================${NC}"
    exit 1
fi

echo ""
echo "Usage:"
echo "  ./run_tests.sh          - Run all tests"
echo "  ./run_tests.sh -v       - Verbose output"
echo "  ./run_tests.sh -c       - With coverage report"
echo "  ./run_tests.sh -q       - Quiet mode"
echo "  ./run_tests.sh -f       - Run only previously failed tests"
