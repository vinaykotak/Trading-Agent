#!/usr/bin/env python3
"""
Quick test script to validate email sending functionality.
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the email function from the trading agent
sys.path.insert(0, os.path.dirname(__file__))
import trading_agent_multi_stock as agent

def test_email_sending():
    """Send a test email to validate configuration."""
    print("=" * 60)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 60)
    print(f"EMAIL_ENABLED: {agent.EMAIL_ENABLED}")
    print(f"EMAIL_TO: {agent.EMAIL_TO}")
    print(f"EMAIL_FROM: {agent.EMAIL_FROM}")
    print(f"EMAIL_SMTP_SERVER: {agent.EMAIL_SMTP_SERVER}")
    print(f"EMAIL_SMTP_PORT: {agent.EMAIL_SMTP_PORT}")
    print(f"EMAIL_PASSWORD: {'*' * len(agent.EMAIL_PASSWORD) if agent.EMAIL_PASSWORD else 'NOT SET'}")
    print("=" * 60)

    if not agent.EMAIL_ENABLED:
        print("\n❌ Email is DISABLED in .env file")
        print("Set EMAIL_ENABLED=true to enable")
        return False

    if not agent.EMAIL_FROM or not agent.EMAIL_PASSWORD:
        print("\n❌ Email credentials not configured")
        print("Please set EMAIL_FROM and EMAIL_PASSWORD in .env file")
        return False

    print("\n📧 Sending test email...")
    print(f"To: {agent.EMAIL_TO}")
    print(f"From: {agent.EMAIL_FROM}")

    # Create test summary data
    test_summary = {
        'portfolio_value': 100000.00,
        'cash': 75000.00,
        'num_positions': 2,
        'positions_html': """
            <table style='width:100%; border-collapse: collapse;'>
                <tr style='background:#f4f4f4;'>
                    <th style='padding:8px; text-align:left;'>Symbol</th>
                    <th style='padding:8px; text-align:right;'>Quantity</th>
                    <th style='padding:8px; text-align:right;'>Current Price</th>
                    <th style='padding:8px; text-align:right;'>Value</th>
                    <th style='padding:8px; text-align:right;'>P/L %</th>
                </tr>
                <tr style='border-bottom:1px solid #ddd;'>
                    <td style='padding:8px;'><strong>KO</strong></td>
                    <td style='padding:8px; text-align:right;'>80</td>
                    <td style='padding:8px; text-align:right;'>$69.87</td>
                    <td style='padding:8px; text-align:right;'>$5,589.60</td>
                    <td style='padding:8px; text-align:right; color:#4CAF50;'><strong>+2.35%</strong></td>
                </tr>
                <tr style='border-bottom:1px solid #ddd;'>
                    <td style='padding:8px;'><strong>MCD</strong></td>
                    <td style='padding:8px; text-align:right;'>80</td>
                    <td style='padding:8px; text-align:right;'>$310.68</td>
                    <td style='padding:8px; text-align:right;'>$24,854.40</td>
                    <td style='padding:8px; text-align:right; color:#f44336;'><strong>-1.15%</strong></td>
                </tr>
            </table>
        """,
        'trades_html': """
            <div class='trade'>
                <p><strong>🟢 BUY</strong> NVDA</p>
                <p>Quantity: 50 shares | Price: $850.25</p>
                <p>Reason: Golden Cross</p>
            </div>
            <div class='trade sell'>
                <p><strong>🔴 SELL</strong> AAPL</p>
                <p>Quantity: 100 shares | Price: $195.40</p>
                <p>Reason: Death Cross</p>
            </div>
        """,
        'stocks_scanned': 50,
        'golden_crosses_found': 3,
        'execution_time': '18.45 seconds'
    }

    # Send the test email
    try:
        agent.send_daily_email(test_summary)
        print("\n✅ Test email sent successfully!")
        print(f"\nPlease check your inbox at: {agent.EMAIL_TO}")
        print("(Also check spam/junk folder if not in inbox)")
        return True
    except Exception as e:
        print(f"\n❌ Failed to send test email: {e}")
        print("\nPossible issues:")
        print("1. Invalid Gmail app password")
        print("2. EMAIL_FROM is not a valid Gmail address")
        print("3. Network connectivity issues")
        print("4. Gmail security settings blocking access")
        return False

if __name__ == "__main__":
    success = test_email_sending()
    sys.exit(0 if success else 1)
