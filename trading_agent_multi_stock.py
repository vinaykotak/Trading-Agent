import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta, timezone
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical.stock import (
    StockHistoricalDataClient,
    StockLatestTradeRequest,
)
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from zoneinfo import ZoneInfo

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, assume env vars are set manually

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === CONFIG ===
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Validate required environment variables
if not API_KEY or not SECRET_KEY:
    raise ValueError(
        "ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables must be set.\n"
        "Create a .env file with your credentials or export them manually.\n"
        "See .env.example for template."
    )

# Email notification configuration
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_TO = os.getenv("EMAIL_TO", "vinnykotak@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Multi-stock strategy configuration - All S&P 500 stocks (~490 stocks)
SP500_WATCHLIST = [
    # Information Technology (68 stocks)
    'AAPL', 'MSFT', 'NVDA', 'AVGO', 'ADBE', 'CRM', 'ORCL', 'ACN', 'CSCO', 'AMD',
    'IBM', 'INTC', 'QCOM', 'TXN', 'INTU', 'NOW', 'AMAT', 'PANW', 'PLTR', 'MU',
    'ADI', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'CRWD', 'ADSK', 'ROP', 'FTNT', 'MCHP',
    'NXPI', 'FICO', 'MRVL', 'ON', 'MPWR', 'PAYX', 'ANSS', 'IT', 'CTSH', 'GLW',
    'APH', 'TYL', 'MSI', 'KEYS', 'CDW', 'GDDY', 'WDC', 'STX', 'ZBRA', 'TRMB',
    'TDY', 'TER', 'FSLR', 'HPQ', 'NTAP', 'AKAM', 'JNPR', 'ENPH', 'FFIV', 'GEN',
    'VRSN', 'SWKS', 'JBL', 'JKHY', 'QRVO', 'SMCI', 'DELL', 'HPE',

    # Healthcare (63 stocks)
    'UNH', 'LLY', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'AMGN',
    'BMY', 'VRTX', 'GILD', 'ELV', 'CVS', 'CI', 'REGN', 'MCK', 'ZTS', 'ISRG',
    'BSX', 'SYK', 'HCA', 'MDT', 'CNC', 'BIIB', 'HUM', 'DXCM', 'IQV', 'A',
    'GEHC', 'IDXX', 'RMD', 'EW', 'ILMN', 'BDX', 'COR', 'MTD', 'WAT', 'STE',
    'ALGN', 'ZBH', 'TECH', 'COO', 'RVTY', 'HOLX', 'DGX', 'LH', 'PODD', 'MOH',
    'BAX', 'VTRS', 'INCY', 'MRNA', 'CAH', 'WST', 'UHS', 'CTLT', 'TFX', 'CRL',
    'DVA', 'SOLV', 'HSIC',

    # Financials (70 stocks)
    'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'SPGI', 'BLK',
    'AXP', 'C', 'SCHW', 'CB', 'MMC', 'PGR', 'ICE', 'CME', 'AON', 'USB',
    'PNC', 'TFC', 'COF', 'BK', 'AIG', 'AFL', 'MET', 'PRU', 'ALL', 'FIS',
    'TRV', 'AMP', 'HIG', 'MSCI', 'DFS', 'MTB', 'FI', 'FITB', 'RJF', 'STT',
    'TROW', 'BRO', 'SYF', 'HBAN', 'RF', 'CFG', 'WTW', 'CINF', 'NTRS', 'KEY',
    'AIZ', 'GL', 'AJG', 'IVZ', 'EWBC', 'BEN', 'L', 'JKHY', 'MKTX', 'CBOE',
    'CFR', 'NDAQ', 'WAL', 'FDS', 'ZION', 'RNR', 'ACGL', 'PFG', 'ALLY', 'WRB',

    # Consumer Discretionary (51 stocks)
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'CMG',
    'MAR', 'GM', 'ORLY', 'HLT', 'F', 'AZO', 'ABNB', 'RCL', 'DHI', 'LEN',
    'YUM', 'ROST', 'GPC', 'EBAY', 'NVR', 'DPZ', 'PHM', 'POOL', 'LVS', 'BBY',
    'CCL', 'APTV', 'GRMN', 'EXPE', 'NCLH', 'MGM', 'WYNN', 'HAS', 'TPR', 'RL',
    'ULTA', 'DRI', 'BWA', 'WHR', 'MHK', 'TSCO', 'KMX', 'CZR', 'LULU', 'DECK',
    'LKQ',

    # Communication Services (24 stocks)
    'META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'T', 'VZ', 'CMCSA', 'TMUS', 'CHTR',
    'EA', 'TTWO', 'WBD', 'MTCH', 'FOXA', 'FOX', 'OMC', 'IPG', 'PARA', 'NWSA',
    'NWS', 'LYV', 'PINS', 'SNAP',

    # Industrials (71 stocks)
    'CAT', 'RTX', 'HON', 'UNP', 'BA', 'GE', 'UPS', 'DE', 'LMT', 'ADP',
    'ETN', 'WM', 'GEV', 'MMM', 'TT', 'PH', 'ITW', 'CSX', 'EMR', 'GD',
    'NOC', 'NSC', 'CARR', 'FDX', 'PCAR', 'JCI', 'CMI', 'RSG', 'PAYX', 'URI',
    'TDG', 'PWR', 'HWM', 'ODFL', 'SNA', 'FAST', 'OTIS', 'AME', 'VRSK', 'IR',
    'DAL', 'LHX', 'ROK', 'EFX', 'WAB', 'AXON', 'XYL', 'CPRT', 'HUBB', 'DOV',
    'LDOS', 'BR', 'VLTO', 'BLDR', 'J', 'UAL', 'EXPD', 'IEX', 'ROL', 'CHRW',
    'GNRC', 'SWK', 'NDSN', 'MAS', 'PNR', 'TXT', 'JBHT', 'LUV', 'AOS', 'ALLE',
    'HII',

    # Consumer Staples (33 stocks)
    'WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'TGT',
    'GIS', 'KMB', 'MNST', 'KHC', 'STZ', 'SYY', 'HSY', 'K', 'CHD', 'CLX',
    'TSN', 'MKC', 'CAG', 'HRL', 'CPB', 'SJM', 'LW', 'TAP', 'DG', 'DLTR',
    'KR', 'KDP', 'EL',

    # Energy (23 stocks)
    'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'WMB',
    'KMI', 'HES', 'BKR', 'FANG', 'HAL', 'DVN', 'TRGP', 'EQT', 'MRO', 'OKE',
    'CTRA', 'APA', 'FTI',

    # Utilities (29 stocks)
    'NEE', 'SO', 'DUK', 'CEG', 'SRE', 'AEP', 'VST', 'D', 'PCG', 'PEG',
    'EXC', 'XEL', 'ED', 'EIX', 'WEC', 'AWK', 'ES', 'DTE', 'FE', 'PPL',
    'ETR', 'AEE', 'CMS', 'CNP', 'NI', 'LNT', 'EVRG', 'PNW', 'ATO',

    # Real Estate (30 stocks)
    'AMT', 'PLD', 'EQIX', 'CCI', 'PSA', 'WELL', 'DLR', 'O', 'CBRE', 'SPG',
    'AVB', 'EQR', 'SBAC', 'WY', 'VICI', 'VTR', 'EXR', 'INVH', 'MAA', 'ARE',
    'DOC', 'KIM', 'ESS', 'UDR', 'CPT', 'HST', 'REG', 'BXP', 'FRT', 'PEAK',

    # Materials (28 stocks)
    'LIN', 'SHW', 'APD', 'FCX', 'ECL', 'NEM', 'CTVA', 'DOW', 'VMC', 'DD',
    'MLM', 'NUE', 'PPG', 'ALB', 'BALL', 'AVY', 'STLD', 'IFF', 'CE', 'CF',
    'EMN', 'MOS', 'FMC', 'LYB', 'IP', 'PKG', 'AMCR', 'SW',
]

BAR_TIMEFRAME = "1Day"
MAX_INVESTMENT_PER_TRADE = 0.25  # 25% of portfolio per trade
MAX_POSITIONS = 4  # Maximum number of simultaneous positions
STOP_LOSS_PCT = 0.05  # 5% stop-loss
TRADE_LOG_FILE = "trade_log_multi.csv"

# Set the local timezone
NY_TZ = ZoneInfo('America/New_York')

# === INIT ===
api = TradingClient(api_key=API_KEY, secret_key=SECRET_KEY, paper=True, url_override=BASE_URL)

# === UTILS ===
def get_latest_data(symbol, limit=300):
    """Fetch historical data for a symbol."""
    try:
        bars_request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(amount=1, unit=TimeFrameUnit.Day),
            start=datetime.now(NY_TZ).date() - timedelta(days=limit)
        )
        client = StockHistoricalDataClient(api_key=API_KEY, secret_key=SECRET_KEY)
        bars = client.get_stock_bars(bars_request).df
        return bars
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def get_account_info():
    """Get account cash and portfolio value."""
    acct = api.get_account()
    return float(acct.cash), float(acct.portfolio_value)

def log_trade(action, symbol, qty, price):
    """Log trade to CSV file."""
    log = pd.DataFrame([{
        "timestamp": datetime.now(),
        "action": action,
        "ticker": symbol,
        "qty": qty,
        "price": price
    }])
    log.to_csv(TRADE_LOG_FILE, mode='a', index=False, header=not pd.io.common.file_exists(TRADE_LOG_FILE))

def calculate_moving_averages(df):
    """Calculate 50-day and 200-day moving averages."""
    ma50 = df['close'].rolling(window=50).mean()
    ma200 = df['close'].rolling(window=200).mean()
    return ma50, ma200

def get_all_positions():
    """Get all current positions."""
    try:
        positions = api.get_all_positions()
        return {pos.symbol: float(pos.qty) for pos in positions}
    except Exception as e:
        logger.warning(f"No positions found or error: {e}")
        return {}

def has_open_position(symbol):
    """Check if we have an open position for the given symbol."""
    try:
        pos = api.get_open_position(symbol)
        return float(pos.qty) if pos else 0
    except Exception as e:
        return 0

def is_market_open():
    """Check if the market is currently open."""
    try:
        clock = api.get_clock()
        return clock.is_open
    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        return False

def save_daily_report(summary_data):
    """Save daily trading summary to HTML file."""
    try:
        # Create reports directory if it doesn't exist
        reports_dir = "daily_reports"
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now(NY_TZ).strftime('%Y-%m-%d_%H-%M-%S')
        report_filename = f"{reports_dir}/trading_report_{timestamp}.html"
        latest_link = f"{reports_dir}/latest_report.html"

        # Create HTML report body
        html_content = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Report - {datetime.now(NY_TZ).strftime('%Y-%m-%d')}</title>
    <style>
      body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f5f5f5; }}
      .container {{ max-width: 1200px; margin: 20px auto; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
      .header {{ background-color: #4CAF50; color: white; padding: 30px; text-align: center; }}
      .header h1 {{ margin: 0; font-size: 32px; }}
      .header p {{ margin: 10px 0 0 0; font-size: 18px; opacity: 0.9; }}
      .content {{ padding: 30px; }}
      .summary {{ background-color: #f4f4f4; padding: 20px; margin: 20px 0; border-radius: 8px; }}
      .summary h2 {{ margin-top: 0; color: #2c3e50; }}
      .trade {{ background-color: #fff; border-left: 4px solid #4CAF50; padding: 15px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
      .trade.sell {{ border-left-color: #f44336; }}
      .stats {{ display: flex; justify-content: space-around; margin: 30px 0; flex-wrap: wrap; }}
      .stat-box {{ text-align: center; padding: 20px; background: #e3f2fd; border-radius: 8px; min-width: 200px; margin: 10px; }}
      .stat-value {{ font-size: 28px; font-weight: bold; color: #1976d2; }}
      .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
      .footer {{ background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th {{ background: #f4f4f4; padding: 12px; text-align: left; font-weight: bold; }}
      td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
      tr:hover {{ background: #f9f9f9; }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>📊 Multi-Stock Trading Agent</h1>
        <p>Daily Report - {datetime.now(NY_TZ).strftime('%A, %B %d, %Y at %I:%M %p %Z')}</p>
      </div>

      <div class="content">
        <div class="stats">
          <div class="stat-box">
            <div class="stat-value">${summary_data['portfolio_value']:,.2f}</div>
            <div class="stat-label">Portfolio Value</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">${summary_data['cash']:,.2f}</div>
            <div class="stat-label">Cash Available</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">{summary_data['num_positions']}</div>
            <div class="stat-label">Open Positions</div>
          </div>
        </div>

        <div class="summary">
          <h2>📍 Current Positions</h2>
          {summary_data['positions_html']}
        </div>

        <div class="summary">
          <h2>📝 Today's Activity</h2>
          {summary_data['trades_html']}
        </div>

        <div class="summary">
          <h2>🔍 Market Scan Results</h2>
          <p><strong>Stocks Scanned:</strong> {summary_data['stocks_scanned']}</p>
          <p><strong>Golden Crosses Found:</strong> {summary_data['golden_crosses_found']}</p>
          <p><strong>Execution Time:</strong> {summary_data['execution_time']}</p>
        </div>
      </div>

      <div class="footer">
        <p><strong>Multi-Stock Trading Agent</strong> | Automated by Claude Code</p>
        <p>Report generated at {datetime.now(NY_TZ).strftime('%Y-%m-%d %I:%M:%S %p %Z')}</p>
        <p>Portfolio values are from Alpaca Paper Trading</p>
      </div>
    </div>
  </body>
</html>
"""

        # Save to file
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Create/update symlink to latest report
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(os.path.basename(report_filename), latest_link)

        logger.info(f"✅ Daily report saved to: {report_filename}")
        logger.info(f"📄 View latest report: {latest_link}")

    except Exception as e:
        logger.error(f"❌ Failed to save daily report: {e}")

def check_for_golden_cross(symbol):
    """Check if a symbol has a golden cross (MA50 crosses above MA200)."""
    try:
        df = get_latest_data(symbol)

        if df is None or len(df) < 200:
            return False

        ma50, ma200 = calculate_moving_averages(df)

        # Check if we have valid MAs
        if pd.isna(ma50.iloc[-1]) or pd.isna(ma200.iloc[-1]):
            return False

        if len(df) < 2:
            return False

        # Check for golden cross: MA50 crosses from below to above MA200
        prev_ma50 = ma50.iloc[-2]
        prev_ma200 = ma200.iloc[-2]
        curr_ma50 = ma50.iloc[-1]
        curr_ma200 = ma200.iloc[-1]

        if prev_ma50 < prev_ma200 and curr_ma50 > curr_ma200:
            current_price = df['close'].iloc[-1]
            logger.info(f"🟢 GOLDEN CROSS: {symbol} at ${current_price:.2f}")
            logger.info(f"   MA50: {curr_ma50:.2f} (prev: {prev_ma50:.2f})")
            logger.info(f"   MA200: {curr_ma200:.2f} (prev: {prev_ma200:.2f})")
            return True

        return False

    except Exception as e:
        logger.error(f"Error checking golden cross for {symbol}: {e}")
        return False

def check_for_death_cross_or_stoploss(symbol):
    """Check if a position should be sold (death cross or stop-loss)."""
    try:
        df = get_latest_data(symbol)

        if df is None or len(df) < 200:
            return False, None

        ma50, ma200 = calculate_moving_averages(df)

        # Check if we have valid MAs
        if pd.isna(ma50.iloc[-1]) or pd.isna(ma200.iloc[-1]):
            return False, None

        if len(df) < 2:
            return False, None

        # Get current values
        prev_ma50 = ma50.iloc[-2]
        prev_ma200 = ma200.iloc[-2]
        curr_ma50 = ma50.iloc[-1]
        curr_ma200 = ma200.iloc[-1]
        current_price = df['close'].iloc[-1]

        # Check for death cross
        death_cross = prev_ma50 > prev_ma200 and curr_ma50 < curr_ma200

        if death_cross:
            logger.info(f"🔴 DEATH CROSS: {symbol} at ${current_price:.2f}")
            return True, "Death Cross"

        # Check for stop-loss
        try:
            position = api.get_open_position(symbol)
            entry_price = float(position.avg_entry_price)
            stop_price = entry_price * (1 - STOP_LOSS_PCT)
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100

            if current_price <= stop_price:
                logger.warning(f"🛑 STOP-LOSS: {symbol} at ${current_price:.2f} (entry: ${entry_price:.2f}, P/L: {profit_loss_pct:+.2f}%)")
                return True, "Stop-Loss"

            # Log current status
            logger.info(f"✋ HOLDING: {symbol} at ${current_price:.2f} (entry: ${entry_price:.2f}, P/L: {profit_loss_pct:+.2f}%)")

        except Exception as e:
            logger.error(f"Error checking stop-loss for {symbol}: {e}")

        return False, None

    except Exception as e:
        logger.error(f"Error checking sell signals for {symbol}: {e}")
        return False, None

# === STRATEGY ===
def evaluate_and_trade():
    """Main strategy: scan for golden crosses to buy, check positions for death crosses to sell."""
    start_time = datetime.now(NY_TZ)
    trades_today = []
    golden_crosses_found = 0

    try:
        # Check if market is open
        if not is_market_open():
            logger.info("Market is closed. Skipping trade evaluation.")
            return

        logger.info("=" * 60)
        logger.info("MULTI-STOCK TRADING AGENT - EVALUATION START")
        logger.info("=" * 60)

        # Get account info
        cash, portfolio_value = get_account_info()
        positions = get_all_positions()

        logger.info(f"Portfolio Value: ${portfolio_value:.2f}")
        logger.info(f"Cash Available: ${cash:.2f}")
        logger.info(f"Current Positions: {len(positions)}")
        if positions:
            for symbol, qty in positions.items():
                logger.info(f"  - {symbol}: {qty} shares")

        # === STEP 1: Check existing positions for sell signals ===
        logger.info("")
        logger.info("--- STEP 1: Checking Positions for Sell Signals ---")

        if positions:
            for symbol in list(positions.keys()):
                should_sell, reason = check_for_death_cross_or_stoploss(symbol)

                if should_sell:
                    qty = positions[symbol]
                    try:
                        # Get current price for tracking
                        df = get_latest_data(symbol, limit=10)
                        current_price = df['close'].iloc[-1] if df is not None else 0

                        logger.info(f"Submitting SELL order: {symbol} {qty} shares ({reason})")
                        order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=int(qty),
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.GTC
                        )
                        order = api.submit_order(order_data=order_data)
                        logger.info(f"✅ SELL order submitted: {order.id}")
                        log_trade(f"SELL ({reason})", symbol, qty, current_price)

                        # Track trade for email
                        trades_today.append({
                            'action': 'SELL',
                            'symbol': symbol,
                            'qty': qty,
                            'price': current_price,
                            'reason': reason
                        })

                        # Update positions dict
                        del positions[symbol]

                        # Update cash (approximate)
                        cash, portfolio_value = get_account_info()

                    except Exception as e:
                        logger.error(f"❌ Failed to submit SELL order for {symbol}: {e}")
        else:
            logger.info("No positions to check.")

        # === STEP 2: Scan for golden crosses to buy ===
        logger.info("")
        logger.info("--- STEP 2: Scanning for Golden Crosses ---")
        logger.info(f"Scanning {len(SP500_WATCHLIST)} stocks...")

        # Check if we can buy more positions
        if len(positions) >= MAX_POSITIONS:
            logger.info(f"⏸️  Maximum positions ({MAX_POSITIONS}) reached. Skipping buy scans.")
            return

        # Calculate investment amount per trade
        invest_amount = portfolio_value * MAX_INVESTMENT_PER_TRADE

        for symbol in SP500_WATCHLIST:
            # Skip if we already have this position
            if symbol in positions:
                continue

            # Check for golden cross
            if check_for_golden_cross(symbol):
                golden_crosses_found += 1

                # Try to buy
                df = get_latest_data(symbol)
                if df is not None:
                    current_price = df['close'].iloc[-1]
                    qty = int(invest_amount // current_price)

                    if qty > 0 and invest_amount <= cash:
                        try:
                            logger.info(f"Submitting BUY order: {symbol} {qty} shares at ~${current_price:.2f}")
                            order_data = MarketOrderRequest(
                                symbol=symbol,
                                qty=qty,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.GTC
                            )
                            order = api.submit_order(order_data=order_data)
                            logger.info(f"✅ BUY order submitted: {order.id}")
                            log_trade("BUY", symbol, qty, current_price)

                            # Track trade for email
                            trades_today.append({
                                'action': 'BUY',
                                'symbol': symbol,
                                'qty': qty,
                                'price': current_price,
                                'reason': 'Golden Cross'
                            })

                            # Update positions and cash
                            positions[symbol] = qty
                            cash -= (qty * current_price)

                            # Check if we've reached max positions
                            if len(positions) >= MAX_POSITIONS:
                                logger.info(f"Maximum positions ({MAX_POSITIONS}) reached.")
                                break

                        except Exception as e:
                            logger.error(f"❌ Failed to submit BUY order for {symbol}: {e}")
                    else:
                        if qty == 0:
                            logger.warning(f"Insufficient funds for {symbol}: ${invest_amount:.2f} / ${current_price:.2f} = 0 shares")
                        else:
                            logger.warning(f"Insufficient cash for {symbol}: need ${invest_amount:.2f}, have ${cash:.2f}")

        logger.info("")
        logger.info("--- Scan Complete ---")
        logger.info(f"Final Positions: {len(positions)}")

        # === STEP 3: Send Daily Email Summary ===
        end_time = datetime.now(NY_TZ)
        execution_time = (end_time - start_time).total_seconds()

        # Get final account info
        final_cash, final_portfolio_value = get_account_info()
        final_positions = get_all_positions()

        # Format positions HTML
        if final_positions:
            positions_html = "<table style='width:100%; border-collapse: collapse;'>"
            positions_html += "<tr style='background:#f4f4f4;'><th style='padding:8px; text-align:left;'>Symbol</th><th style='padding:8px; text-align:right;'>Quantity</th><th style='padding:8px; text-align:right;'>Current Price</th><th style='padding:8px; text-align:right;'>Value</th><th style='padding:8px; text-align:right;'>P/L %</th></tr>"

            for symbol, qty in final_positions.items():
                try:
                    position = api.get_open_position(symbol)
                    current_price = float(position.current_price)
                    entry_price = float(position.avg_entry_price)
                    market_value = float(position.market_value)
                    pl_pct = ((current_price - entry_price) / entry_price) * 100
                    pl_color = "#4CAF50" if pl_pct >= 0 else "#f44336"

                    positions_html += f"<tr style='border-bottom:1px solid #ddd;'>"
                    positions_html += f"<td style='padding:8px;'><strong>{symbol}</strong></td>"
                    positions_html += f"<td style='padding:8px; text-align:right;'>{int(qty)}</td>"
                    positions_html += f"<td style='padding:8px; text-align:right;'>${current_price:.2f}</td>"
                    positions_html += f"<td style='padding:8px; text-align:right;'>${market_value:.2f}</td>"
                    positions_html += f"<td style='padding:8px; text-align:right; color:{pl_color};'><strong>{pl_pct:+.2f}%</strong></td>"
                    positions_html += "</tr>"
                except Exception as e:
                    logger.error(f"Error getting position details for {symbol}: {e}")

            positions_html += "</table>"
        else:
            positions_html = "<p>No open positions.</p>"

        # Format trades HTML
        if trades_today:
            trades_html = ""
            for trade in trades_today:
                trade_class = "sell" if trade['action'] == 'SELL' else ""
                emoji = "🔴" if trade['action'] == 'SELL' else "🟢"
                trades_html += f"<div class='trade {trade_class}'>"
                trades_html += f"<p><strong>{emoji} {trade['action']}</strong> {trade['symbol']}</p>"
                trades_html += f"<p>Quantity: {int(trade['qty'])} shares | Price: ${trade['price']:.2f}</p>"
                trades_html += f"<p>Reason: {trade['reason']}</p>"
                trades_html += "</div>"
        else:
            trades_html = "<p>No trades executed today.</p>"

        # Build summary data
        summary_data = {
            'portfolio_value': final_portfolio_value,
            'cash': final_cash,
            'num_positions': len(final_positions),
            'positions_html': positions_html,
            'trades_html': trades_html,
            'stocks_scanned': len(SP500_WATCHLIST),
            'golden_crosses_found': golden_crosses_found,
            'execution_time': f"{execution_time:.2f} seconds"
        }

        # Save daily report to file
        save_daily_report(summary_data)

    except Exception as e:
        logger.error(f"Error in evaluate_and_trade: {e}", exc_info=True)

# === MAIN ENTRY POINT ===
def main():
    """Main function to run the trading agent."""
    logger.info("="*60)
    logger.info("MULTI-STOCK TRADING AGENT - STARTED")
    logger.info(f"Timestamp: {datetime.now(NY_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"Watchlist: {len(SP500_WATCHLIST)} stocks")
    logger.info(f"Max Positions: {MAX_POSITIONS}")
    logger.info(f"Investment per Trade: {MAX_INVESTMENT_PER_TRADE*100}% of portfolio")
    logger.info("="*60)

    try:
        evaluate_and_trade()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        return 1

    logger.info("="*60)
    logger.info("MULTI-STOCK TRADING AGENT - COMPLETED")
    logger.info("="*60)
    return 0

if __name__ == "__main__":
    exit(main())
