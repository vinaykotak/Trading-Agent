# Multi-Stock Trading Agent - Deployment Guide

## Overview

Deploy the **multi-stock trading agent** as a scheduled systemd service on your Linux server. The agent will automatically scan 50 S&P 500 stocks daily for golden cross signals and manage a diversified portfolio.

---

## Quick Start

### 1. Configure API Credentials

```bash
# Copy the template
cp .env.example .env

# Add your Alpaca API credentials
nano .env
```

```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Get API keys**: https://app.alpaca.markets/paper/dashboard/overview

### 2. Run Automated Setup

```bash
sudo ./setup_service.sh
```

This will:
- ✅ Check for `.env` file
- ✅ Verify Python and install dependencies
- ✅ Configure systemd service with correct paths
- ✅ Enable and start the timer
- ✅ Display service status and next run time

### 3. Verify Installation

```bash
# Check timer status
systemctl status trading-agent.timer

# View next scheduled run
systemctl list-timers trading-agent.timer

# View recent logs
journalctl -u trading-agent.service -n 50
```

**Done!** Your multi-stock trading agent will run automatically every weekday at 9:35 AM ET.

---

## What Happens Daily

### Execution Schedule

- **When**: Monday-Friday at 9:35 AM Eastern Time (5 min after market open)
- **Duration**: ~20-30 seconds (scans 50 stocks)

### Trading Flow

```
1. Market Opens at 9:30 AM ET
2. Agent Runs at 9:35 AM ET
   ├─ STEP 1: Check all positions for sell signals
   │  ├─ Death cross detected? → SELL
   │  └─ Stop-loss triggered? → SELL
   └─ STEP 2: Scan 50 stocks for buy signals
      └─ Golden cross detected? → BUY (up to 4 positions)
3. Log all trades to trade_log_multi.csv
4. Agent Completes
```

---

## Strategy Configuration

### Stock Watchlist

The agent scans these 50 S&P 500 stocks daily:

```
AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK.B,
V, JNJ, WMT, JPM, MA, PG, UNH, HD, CVX, LLY,
ABBV, MRK, PEP, KO, COST, AVGO, MCD, TMO, ACN,
CSCO, ABT, DHR, VZ, ADBE, NKE, DIS, CRM, NFLX,
CMCSA, PFE, AMD, INTC, TXN, QCOM, NEE, PM, UNP,
RTX, HON, ORCL, IBM, BA
```

**To customize**: Edit `SP500_WATCHLIST` in `trading_agent_multi_stock.py`

### Position Management

```python
MAX_POSITIONS = 4                   # Hold up to 4 stocks
MAX_INVESTMENT_PER_TRADE = 0.25     # 25% per position
STOP_LOSS_PCT = 0.05                # 5% stop-loss
```

**Example with $100,000 portfolio**:
- Position 1: $25,000
- Position 2: $25,000
- Position 3: $25,000
- Position 4: $25,000
- **Total**: $100,000 (fully invested)

---

## Service Management

### View Status

```bash
# Timer status (schedule)
systemctl status trading-agent.timer

# Service status (last execution)
systemctl status trading-agent.service

# Next scheduled run
systemctl list-timers trading-agent.timer
```

### View Logs

```bash
# Follow logs in real-time
journalctl -u trading-agent.service -f

# Last 50 lines
journalctl -u trading-agent.service -n 50

# Logs from specific date
journalctl -u trading-agent.service --since "2025-01-15"

# Logs since today
journalctl -u trading-agent.service --since today
```

### Manual Execution

```bash
# Run immediately (for testing)
sudo systemctl start trading-agent.service

# Check result
systemctl status trading-agent.service
```

### Stop/Disable

```bash
# Stop timer (prevents future runs)
sudo systemctl stop trading-agent.timer

# Disable timer (won't start on reboot)
sudo systemctl disable trading-agent.timer

# Re-enable
sudo systemctl enable trading-agent.timer
sudo systemctl start trading-agent.timer
```

---

## Schedule Configuration

Default: **Monday-Friday at 9:35 AM ET** (5 minutes after market open)

### Adjust Run Time

Edit `/etc/systemd/system/trading-agent.timer`:

```bash
sudo nano /etc/systemd/system/trading-agent.timer
```

```ini
# For UTC timezone (server default)
OnCalendar=Mon-Fri 14:35:00  # 9:35 AM ET = 14:35 UTC (EST)

# For server in ET timezone
OnCalendar=Mon-Fri 09:35:00

# Multiple runs per day
OnCalendar=Mon-Fri 14:35:00,19:00:00  # 9:35 AM and 2:00 PM ET
```

After editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart trading-agent.timer
```

---

## Monitoring & Logs

### Trade Log File

All trades logged to `trade_log_multi.csv`:

```csv
timestamp,action,ticker,qty,price
2025-12-29 09:35:22,BUY,KO,80,69.87
2025-12-29 09:35:25,BUY,MCD,80,310.68
2025-12-30 09:35:18,SELL (Death Cross),KO,80,68.50
```

### Systemd Journal

Real-time execution logs:

```bash
# Example log output
2025-12-29 09:35:03 - INFO - MULTI-STOCK TRADING AGENT - STARTED
2025-12-29 09:35:03 - INFO - Watchlist: 50 stocks
2025-12-29 09:35:03 - INFO - Max Positions: 4
2025-12-29 09:35:04 - INFO - Portfolio Value: $100000.00
2025-12-29 09:35:04 - INFO - Current Positions: 2
2025-12-29 09:35:04 - INFO -   - KO: 80 shares
2025-12-29 09:35:04 - INFO -   - MCD: 80 shares
2025-12-29 09:35:05 - INFO - --- STEP 1: Checking Positions ---
2025-12-29 09:35:06 - INFO - ✋ HOLDING: KO (P/L: +1.5%)
2025-12-29 09:35:07 - INFO - ✋ HOLDING: MCD (P/L: -0.8%)
2025-12-29 09:35:08 - INFO - --- STEP 2: Scanning for Golden Crosses ---
2025-12-29 09:35:20 - INFO - 🟢 GOLDEN CROSS: NVDA at $850.25
2025-12-29 09:35:21 - INFO - ✅ BUY order submitted: order-12345
2025-12-29 09:35:25 - INFO - --- Scan Complete ---
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
journalctl -u trading-agent.service -xe
```

**Common issues:**
- Missing `.env` file → Create with API credentials
- Wrong Python path → Service auto-detects, but verify with `which python3`
- Missing dependencies → Run `pip3 install -r requirements.txt`
- Permission issues → Ensure `.env` is readable: `chmod 600 .env`

### Timer Not Running

```bash
# Check if enabled
systemctl is-enabled trading-agent.timer

# Check if active
systemctl is-active trading-agent.timer

# View all timers
systemctl list-timers --all | grep trading
```

### Market Closed Message

**This is normal!** The agent checks market hours (9:30 AM - 4:00 PM ET, Mon-Fri). If run outside these hours, it will log "Market is closed" and exit cleanly.

### No Trades Executing

**Possible reasons:**
- No golden crosses detected (rare events - maybe once per week per stock)
- Already at max positions (4)
- Insufficient cash
- Market conditions (ranging markets produce fewer crossovers)

**Check:** Run `python3 find_golden_cross.py` to see if any stocks have recent golden crosses.

---

## Testing Before Deployment

### Run Unit Tests

```bash
# All 25 tests should pass
./run_tests.sh

# Verbose output
./run_tests.sh -v

# With coverage
./run_tests.sh -c
```

### Manual Test Run

```bash
# Bypass market hours check (for testing)
python3 test_multi_stock.py
```

### Scan for Opportunities

```bash
# Find stocks with recent golden crosses
python3 find_golden_cross.py
```

---

## Security Best Practices

### Protect API Credentials

```bash
# Set restrictive permissions on .env
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### Use Paper Trading First

**NEVER use live trading without extensive testing:**
- Test for minimum 30 days in paper trading
- Verify buy/sell logic works correctly
- Monitor all positions and trades
- Ensure stop-loss triggers appropriately

### Rotate API Keys

If credentials are accidentally exposed:
1. Immediately rotate keys in Alpaca dashboard
2. Update `.env` with new keys
3. Restart service: `sudo systemctl restart trading-agent.timer`

---

## Transitioning to Live Trading

⚠️ **ONLY after 30+ days of successful paper trading**

### Steps

1. **Create live API keys** in Alpaca dashboard (not paper trading keys)

2. **Update `.env`**:
   ```bash
   ALPACA_API_KEY=live_key_here
   ALPACA_SECRET_KEY=live_secret_here
   ALPACA_BASE_URL=https://api.alpaca.markets  # Remove '/paper'
   ```

3. **Update code** (`trading_agent_multi_stock.py` line 52):
   ```python
   api = TradingClient(api_key=API_KEY, secret_key=SECRET_KEY, paper=False)
   ```

4. **Reduce position sizes** initially:
   ```python
   MAX_INVESTMENT_PER_TRADE = 0.10  # Start with 10% instead of 25%
   ```

5. **Monitor closely** for the first 2 weeks
   ```bash
   journalctl -u trading-agent.service -f
   ```

---

## Maintenance

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip3 install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart trading-agent.timer
```

### Backup Configuration

```bash
# Backup important files
tar -czf trading-agent-backup-$(date +%Y%m%d).tar.gz \
  .env \
  trading_agent_multi_stock.py \
  trade_log_multi.csv \
  /etc/systemd/system/trading-agent.*
```

---

## Uninstall

```bash
# Stop and disable
sudo systemctl stop trading-agent.timer
sudo systemctl disable trading-agent.timer

# Remove systemd files
sudo rm /etc/systemd/system/trading-agent.service
sudo rm /etc/systemd/system/trading-agent.timer

# Reload systemd
sudo systemctl daemon-reload
```

---

## Support & Resources

- **Alpaca API**: https://alpaca.markets/docs/
- **Strategy Guide**: `MULTI_STOCK_STRATEGY.md`
- **Testing Guide**: `TESTING.md`
- **Code Documentation**: `CLAUDE.md`

---

## Disclaimer

Trading involves risk. This software is provided as-is for educational purposes. Always:
- Test thoroughly in paper trading (minimum 30 days)
- Never invest more than you can afford to lose
- Understand strategy limitations (performs best in trending markets)
- Monitor positions regularly

No guarantees of profitability are made or implied.
