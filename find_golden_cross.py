#!/usr/bin/env python3
"""
Golden Cross Scanner for S&P 500 stocks
Finds stocks where MA50 recently crossed above MA200
"""

import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from zoneinfo import ZoneInfo

# S&P 500 stocks to scan (~490 stocks)
SP500_SAMPLE = [
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

NY_TZ = ZoneInfo('America/New_York')

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

def calculate_moving_averages(df):
    """Calculate 50-day and 200-day moving averages."""
    ma50 = df['close'].rolling(window=50).mean()
    ma200 = df['close'].rolling(window=200).mean()
    return ma50, ma200

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
        print(f"Error fetching {symbol}: {e}")
        return None

def check_golden_cross(symbol):
    """Check if a symbol has a recent golden cross."""
    print(f"Checking {symbol}...", end=' ')

    df = get_latest_data(symbol)
    if df is None or len(df) < 200:
        print("❌ Insufficient data")
        return None

    ma50, ma200 = calculate_moving_averages(df)

    # Check if we have valid MAs
    if pd.isna(ma50.iloc[-1]) or pd.isna(ma200.iloc[-1]):
        print("❌ Invalid MAs")
        return None

    # Get recent values (last 20 days for wider search)
    for i in range(len(df) - 1, max(200, len(df) - 21), -1):
        if pd.isna(ma50.iloc[i]) or pd.isna(ma200.iloc[i]):
            continue
        if pd.isna(ma50.iloc[i-1]) or pd.isna(ma200.iloc[i-1]):
            continue

        # Check for golden cross
        if ma50.iloc[i-1] < ma200.iloc[i-1] and ma50.iloc[i] > ma200.iloc[i]:
            days_ago = len(df) - 1 - i
            current_price = df['close'].iloc[-1]
            print(f"✅ GOLDEN CROSS {days_ago} days ago!")

            # Handle multi-index or regular index
            try:
                crossover_date = df.index[i][1].strftime('%Y-%m-%d') if isinstance(df.index[i], tuple) else df.index[i].strftime('%Y-%m-%d')
            except:
                crossover_date = str(df.index[i])

            return {
                'symbol': symbol,
                'days_ago': days_ago,
                'current_price': current_price,
                'ma50': ma50.iloc[-1],
                'ma200': ma200.iloc[-1],
                'crossover_date': crossover_date
            }

    # No golden cross, but report current status
    curr_ma50 = ma50.iloc[-1]
    curr_ma200 = ma200.iloc[-1]

    if curr_ma50 > curr_ma200:
        print(f"⏸️  MA50 > MA200 (already above, no recent cross)")
    else:
        print(f"⏸️  MA50 < MA200 (bearish)")

    return None

def main():
    print("=" * 70)
    print("Golden Cross Scanner - S&P 500 Sample")
    print("=" * 70)
    print(f"Scanning {len(SP500_SAMPLE)} popular S&P 500 stocks...")
    print(f"Looking for MA50 crossing above MA200 in last 20 days")
    print("=" * 70)
    print()

    golden_crosses = []

    for symbol in SP500_SAMPLE:
        result = check_golden_cross(symbol)
        if result:
            golden_crosses.append(result)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    if golden_crosses:
        print(f"\n✅ Found {len(golden_crosses)} stock(s) with recent golden crosses:\n")

        # Sort by most recent
        golden_crosses.sort(key=lambda x: x['days_ago'])

        for gc in golden_crosses:
            print(f"🟢 {gc['symbol']}")
            print(f"   Crossover Date: {gc['crossover_date']} ({gc['days_ago']} days ago)")
            print(f"   Current Price: ${gc['current_price']:.2f}")
            print(f"   MA50: ${gc['ma50']:.2f}")
            print(f"   MA200: ${gc['ma200']:.2f}")
            print()

        print("=" * 70)
        print("💡 RECOMMENDATION")
        print("=" * 70)

        # Recommend the most recent one
        best = golden_crosses[0]
        print(f"\nBest candidate: {best['symbol']}")
        print(f"Most recent golden cross ({best['days_ago']} days ago)")
        print(f"\nTo use this in your trading agent:")
        print(f"  1. Edit trading_agent_realtime.py")
        print(f"  2. Change TICKER = 'MSFT' to TICKER = '{best['symbol']}'")
        print(f"  3. Run: python3 trading_agent_realtime.py")

    else:
        print("\n❌ No golden crosses found in the last 20 days.")
        print("\nThis is normal - golden crosses are relatively rare events.")
        print("They typically occur when a stock transitions from downtrend to uptrend.")
        print("\nYou can:")
        print("  1. Extend the lookback period further (edit the range in check_golden_cross)")
        print("  2. Scan more stocks (add more tickers to SP500_SAMPLE)")
        print("  3. Wait for market conditions to change")
        print("  4. Use the backtesting script (tradingAgent.py) to test historical data")

    print()

if __name__ == "__main__":
    main()
