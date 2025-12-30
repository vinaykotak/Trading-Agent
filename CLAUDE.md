# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

This repository contains a **multi-stock trading agent** that automatically scans ~500 S&P 500 stocks daily for golden cross opportunities and manages a diversified portfolio.

**Strategy**: Moving average crossover (MA50 vs MA200) across multiple stocks simultaneously.

## Core Implementation

### Main Trading Agent

**File**: `trading_agent_multi_stock.py`

This is the production trading agent that:
- Scans ~500 S&P 500 stocks daily for golden cross signals (MA50 crosses above MA200)
- Buys stocks showing golden crosses (up to 4 simultaneous positions)
- Monitors all positions for death crosses (MA50 crosses below MA200) or stop-loss triggers
- Automatically sells positions when sell signals occur

**Key Features**:
- Multi-stock portfolio (up to 4 positions)
- 25% position sizing (per trade)
- 5% stop-loss protection (per position)
- Automatic diversification across sectors
- Market hours validation

### Utilities

**File**: `find_golden_cross.py`

Scanner utility to identify S&P 500 stocks with recent golden crosses. Useful for:
- Finding current opportunities
- Validating strategy signals
- Manual analysis

## Running the Code

### Production Deployment (Automated)

```bash
# Deploy as systemd service (runs daily at 9:35 AM ET)
sudo ./setup_service.sh
```

This sets up:
- Automatic daily execution
- Logs to systemd journal
- Environment variable loading from `.env`
- Service management via systemd

### Manual Execution

```bash
# Run once (only during market hours)
python3 trading_agent_multi_stock.py

# Test with market hours bypassed
python3 test_multi_stock.py

# Scan for current golden crosses
python3 find_golden_cross.py
```

### Testing

```bash
# Run comprehensive test suite (25 tests)
./run_tests.sh

# Verbose output
./run_tests.sh -v

# With coverage report
./run_tests.sh -c
```

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Core dependencies:
- **alpaca-trade-api** and **alpaca-py**: Alpaca API clients for live trading
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework

## Configuration

### Environment Variables (.env file)

```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### Strategy Parameters (in trading_agent_multi_stock.py)

```python
# Stock watchlist
SP500_WATCHLIST = [~500 S&P 500 stocks organized by sector]

# Position management
MAX_POSITIONS = 4                      # Maximum simultaneous positions
MAX_INVESTMENT_PER_TRADE = 0.25        # 25% of portfolio per trade

# Risk management
STOP_LOSS_PCT = 0.05                   # 5% stop-loss threshold
```

## Architecture

### Strategy Implementation

**Moving Average Crossover Strategy** applied across multiple stocks:

**BUY Signals** (Golden Cross):
- MA50 crosses **above** MA200 (bullish trend confirmation)
- Only buys if:
  - Position doesn't already exist for that stock
  - Haven't reached max positions (4)
  - Sufficient cash available

**SELL Signals**:
- **Death Cross**: MA50 crosses **below** MA200 (trend reversal)
- **Stop-Loss**: Price drops 5% below entry price (risk protection)

### Daily Execution Flow

1. **Market Hours Check**: Verify market is open
2. **STEP 1 - Sell Check**: Scan all positions for death cross or stop-loss
3. **STEP 2 - Buy Scan**: Scan ~500 stocks for golden crosses
4. **Logging**: Record all trades to `trade_log_multi.csv`

### Data Flow

1. **Fetch Data**: Retrieve 300 days of historical bars for each stock (for MA calculation)
2. **Calculate Indicators**: Compute 50-day and 200-day moving averages
3. **Generate Signals**: Detect crossovers by comparing previous vs current MA values
4. **Execute Trades**: Submit market orders via Alpaca API
5. **Log Results**: Record trades and update portfolio state

## File Structure

```
TradingSimulation/
├── trading_agent_multi_stock.py  # Main trading agent
├── test_trading_agent.py         # Comprehensive unit tests (25 tests)
├── test_multi_stock.py            # Multi-stock integration test
├── find_golden_cross.py           # Golden cross scanner utility
├── .env                           # API credentials (not in git)
├── .env.example                   # Credentials template
├── requirements.txt               # Python dependencies
├── setup_service.sh               # Systemd service installer
├── run_tests.sh                   # Test runner script
├── trading-agent.service          # Systemd service definition
├── trading-agent.timer            # Systemd timer (scheduler)
├── .gitignore                     # Git ignore rules
├── CLAUDE.md                      # This file
├── DEPLOYMENT.md                  # Deployment guide
├── TESTING.md                     # Testing documentation
└── MULTI_STOCK_STRATEGY.md        # Strategy documentation
```

## Service Management

### Deployment

```bash
# Install and enable service
sudo ./setup_service.sh

# Check status
systemctl status trading-agent.timer

# View logs
journalctl -u trading-agent.service -f

# Stop service
sudo systemctl stop trading-agent.timer
```

### Schedule Configuration

Default: Runs Monday-Friday at 9:35 AM ET (5 minutes after market open)

To modify schedule, edit `/etc/systemd/system/trading-agent.timer`:
```ini
OnCalendar=Mon-Fri 14:35:00  # UTC time (9:35 AM ET)
```

## Important Notes

### Security
- **API Credentials**: Stored in `.env` file (protected by `.gitignore`)
- **Paper Trading**: Configured for Alpaca paper trading by default
- **Credentials Rotation**: Recommended if accidentally exposed

### Risk Management
- **Stop-Loss**: 5% per position limits downside
- **Position Sizing**: 25% allocation prevents over-concentration
- **Max Positions**: 4-stock limit balances diversification and manageability
- **Death Cross Exit**: Automatic trend reversal protection

### Performance Considerations
- **Scan Time**: 3-5 minutes to scan ~500 stocks (Phase 1 implementation)
- **API Rate Limits**: Respectful of Alpaca API limits
- **Data Requirements**: Needs 200+ days of historical data per stock
- **Note**: Future optimization with batch API calls can reduce scan time to <30 seconds

### Market Conditions
- **Trending Markets**: Strategy performs well
- **Ranging Markets**: May experience whipsaws (false signals)
- **Diversification**: Multi-stock approach reduces single-stock risk

## Testing

### Test Coverage
- **25 unit tests** covering all trading logic
- **100% pass rate** required for deployment
- Tests include: MA calculations, golden/death cross detection, position sizing, stop-loss logic, edge cases

### Test Categories
1. Moving average calculations
2. Golden cross detection
3. Death cross detection
4. Stop-loss logic
5. Position sizing
6. Market hours checking
7. Position management
8. Data validation
9. Integration scenarios
10. Edge cases

## Monitoring

### Logs
All activity logged to systemd journal:
```bash
# Real-time logs
journalctl -u trading-agent.service -f

# Last 50 entries
journalctl -u trading-agent.service -n 50

# Logs since today
journalctl -u trading-agent.service --since today
```

### Trade History
All trades logged to `trade_log_multi.csv`:
```csv
timestamp,action,ticker,qty,price
2025-12-29 09:35:22,BUY,KO,80,69.87
2025-12-30 09:35:18,SELL (Death Cross),KO,80,68.50
```

## Transitioning to Live Trading

**ONLY after extensive paper trading (minimum 30 days)**

1. Create live API keys in Alpaca dashboard
2. Update `.env`:
   ```bash
   ALPACA_BASE_URL=https://api.alpaca.markets  # Remove 'paper'
   ```
3. Update code (line 52):
   ```python
   api = TradingClient(api_key=API_KEY, secret_key=SECRET_KEY, paper=False)
   ```
4. Start with smaller position sizes (e.g., 10% instead of 25%)
5. Monitor closely for first 2 weeks

## Support & Resources

- **Alpaca API Docs**: https://alpaca.markets/docs/
- **Strategy Documentation**: See `MULTI_STOCK_STRATEGY.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Testing Guide**: See `TESTING.md`

---

**Note**: This is a fully automated multi-stock trading system. Always test thoroughly in paper trading before using real money.
