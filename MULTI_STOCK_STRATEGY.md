# Multi-Stock Trading Strategy

## Overview

The **multi-stock trading agent** (`trading_agent_multi_stock.py`) is an enhanced version that automatically scans ~500 S&P 500 stocks daily for trading opportunities, rather than trading a single fixed ticker.

---

## How It Works

### Daily Execution Flow

```
1. Market Opens
2. Check All Positions → Sell if Death Cross or Stop-Loss
3. Scan ~500 S&P 500 Stocks → Buy stocks with Golden Cross
4. Repeat Daily
```

---

## Strategy Logic

### SELL Logic (Step 1): Check Existing Positions

For **every stock in your portfolio**:

- ✅ **Death Cross Detected** → SELL entire position
  - Occurs when MA50 crosses **from above to below** MA200
  - Indicates trend reversal from bullish to bearish

- ✅ **Stop-Loss Triggered** → SELL entire position
  - Occurs when price drops 5% below entry price
  - Protects capital from large losses

- ⏸️ **No Sell Signal** → HOLD position
  - Continue monitoring daily

### BUY Logic (Step 2): Scan for Opportunities

For **every stock in the watchlist** (~500 stocks):

- ✅ **Golden Cross Detected** → BUY new position
  - Occurs when MA50 crosses **from below to above** MA200
  - Indicates trend reversal from bearish to bullish
  - Only if:
    - We don't already own this stock
    - We haven't reached max positions (4)
    - We have sufficient cash

- ⏸️ **No Golden Cross** → Skip, continue scanning

---

## Configuration

### Key Parameters

```python
# Stock watchlist (~500 S&P 500 stocks organized by sector)
SP500_WATCHLIST = [
    'AAPL', 'MSFT', 'NVDA', 'AVGO', 'ADBE', 'CRM', 'ORCL', ...
]

# Position sizing
MAX_INVESTMENT_PER_TRADE = 0.25  # 25% of portfolio per trade
MAX_POSITIONS = 4                 # Max 4 simultaneous positions

# Risk management
STOP_LOSS_PCT = 0.05             # 5% stop-loss per position
```

### Portfolio Allocation

- **Per Trade**: 25% of total portfolio value
- **Max Positions**: 4 stocks simultaneously
- **Max Allocation**: 100% (4 positions × 25% each)

**Example with $100,000 portfolio:**
- Position 1: $25,000 (25%)
- Position 2: $25,000 (25%)
- Position 3: $25,000 (25%)
- Position 4: $25,000 (25%)
- **Total**: $100,000 invested

---

## Advantages Over Single-Stock Strategy

| Feature | Single-Stock | Multi-Stock |
|---------|--------------|-------------|
| **Diversification** | ❌ All capital in 1 stock | ✅ Up to 4 stocks |
| **Opportunity Detection** | ⏸️ Waits for 1 ticker signal | ✅ Scans ~500 tickers daily |
| **Risk Management** | ⚠️ High concentration risk | ✅ Spread across 4 positions |
| **Uptime** | ⏸️ Often waiting | ✅ More active trading |
| **Market Adaptability** | ❌ Fixed to one sector | ✅ Captures trends across sectors |

---

## Example Scenario

### Day 1: Market Open
**Portfolio**: $100,000 cash, 0 positions

**Scan Results**:
- ✅ **KO**: Golden cross detected → BUY $25,000 (80 shares @ $312)
- ✅ **MCD**: Golden cross detected → BUY $25,000 (80 shares @ $311)
- ⏸️ Other 48 stocks: No signals

**End of Day**: $50,000 cash, 2 positions (KO, MCD)

---

### Day 2: Market Open
**Portfolio**: $50,000 cash, 2 positions

**Step 1 - Check Positions**:
- KO: No sell signal → HOLD
- MCD: No sell signal → HOLD

**Step 2 - Scan for New Opportunities**:
- ✅ **NVDA**: Golden cross detected → BUY $25,000
- ⏸️ Other stocks: No signals

**End of Day**: $25,000 cash, 3 positions (KO, MCD, NVDA)

---

### Day 5: Market Open
**Portfolio**: $25,000 cash, 3 positions

**Step 1 - Check Positions**:
- KO: ❌ **Death cross detected** → SELL (realize profit/loss)
- MCD: ✅ Holding (up 5%)
- NVDA: ✅ Holding (up 8%)

**Step 2 - Scan**:
- ✅ **AAPL**: Golden cross detected → BUY $25,000

**End of Day**: $0 cash, 3 positions (MCD, NVDA, AAPL)

---

## Risk Management

### Position-Level Protections

1. **Stop-Loss (5%)**: Limits loss on any single position
2. **Death Cross Exit**: Exits when trend reverses
3. **Golden Cross Entry**: Only enters when trend confirms

### Portfolio-Level Protections

1. **Max Positions (4)**: Prevents over-diversification
2. **Position Sizing (25%)**: Limits exposure per trade
3. **Multi-Stock Diversification**: Reduces single-stock risk

---

## Performance Considerations

### Strengths

✅ **Captures Multiple Trends**: Can be in tech, healthcare, consumer goods simultaneously
✅ **Reduces Idle Time**: More frequent signals across 50 stocks
✅ **Sector Rotation**: Naturally follows market leadership
✅ **Downside Protection**: Stop-loss on every position

### Limitations

⚠️ **Whipsaw Risk**: Multiple false signals in ranging markets
⚠️ **Transaction Costs**: More trades = more commissions
⚠️ **Scan Time**: Takes ~20 seconds to scan 50 stocks
⚠️ **Capital Requirements**: Needs enough capital for 4 positions

---

## Monitoring

### Log Output Example

```
2025-12-29 09:35:00 - INFO - MULTI-STOCK TRADING AGENT - EVALUATION START
2025-12-29 09:35:01 - INFO - Portfolio Value: $100000.00
2025-12-29 09:35:01 - INFO - Cash Available: $50000.00
2025-12-29 09:35:01 - INFO - Current Positions: 2
2025-12-29 09:35:01 - INFO -   - KO: 80 shares
2025-12-29 09:35:01 - INFO -   - MCD: 80 shares

2025-12-29 09:35:01 - INFO - --- STEP 1: Checking Positions for Sell Signals ---
2025-12-29 09:35:02 - INFO - ✋ HOLDING: KO at $315.50 (entry: $312.00, P/L: +1.12%)
2025-12-29 09:35:03 - INFO - ✋ HOLDING: MCD at $309.00 (entry: $311.00, P/L: -0.64%)

2025-12-29 09:35:03 - INFO - --- STEP 2: Scanning for Golden Crosses ---
2025-12-29 09:35:03 - INFO - Scanning 50 stocks...
2025-12-29 09:35:15 - INFO - 🟢 GOLDEN CROSS: NVDA at $850.25
2025-12-29 09:35:15 - INFO -    MA50: 845.50 (prev: 843.20)
2025-12-29 09:35:15 - INFO -    MA200: 842.10 (prev: 844.30)
2025-12-29 09:35:16 - INFO - Submitting BUY order: NVDA 29 shares at ~$850.25
2025-12-29 09:35:16 - INFO - ✅ BUY order submitted: order-12345

2025-12-29 09:35:25 - INFO - --- Scan Complete ---
2025-12-29 09:35:25 - INFO - Final Positions: 3
```

---

## Files

- **`trading_agent_multi_stock.py`**: Main multi-stock agent
- **`test_multi_stock.py`**: Test script (bypasses market hours)
- **`trade_log_multi.csv`**: Trade history log
- **`MULTI_STOCK_STRATEGY.md`**: This documentation

---

## Deployment

### Option 1: Use Multi-Stock Agent (Recommended)

The systemd service is already configured for multi-stock:

```bash
sudo ./setup_service.sh
```

### Option 2: Run Manually

```bash
python3 trading_agent_multi_stock.py
```

### Option 3: Test Without Market Hours Check

```bash
python3 test_multi_stock.py
```

---

## Customization

### Change Watchlist

Edit the `SP500_WATCHLIST` in `trading_agent_multi_stock.py`:

```python
SP500_WATCHLIST = [
    'AAPL', 'GOOGL', 'AMZN',  # Your custom list
]
```

### Adjust Position Sizing

```python
MAX_INVESTMENT_PER_TRADE = 0.20  # 20% per trade
MAX_POSITIONS = 5                 # Allow 5 positions
```

### Modify Risk Parameters

```python
STOP_LOSS_PCT = 0.03  # Tighter 3% stop-loss
```

---

## Comparison with Single-Stock Agent

Both agents are included:

| File | Strategy | Use Case |
|------|----------|----------|
| `trading_agent_realtime.py` | Single stock (fixed ticker) | Simple, focused, one trend |
| `trading_agent_multi_stock.py` | Multi-stock scanner | Diversified, opportunistic |

You can switch between them by editing the systemd service file or running directly.

---

## Next Steps

1. **Review configuration** - Check position sizing, stop-loss, watchlist
2. **Deploy service** - `sudo ./setup_service.sh`
3. **Monitor logs** - `journalctl -u trading-agent.service -f`
4. **Adjust as needed** - Fine-tune based on performance

---

## Disclaimer

Multi-stock strategies increase complexity and transaction costs. Always:
- Test thoroughly in paper trading
- Monitor performance closely
- Understand the risks of multiple simultaneous positions
- Start with small position sizes

---

**Happy Trading! 🚀**
