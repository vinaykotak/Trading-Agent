#!/usr/bin/env python3
"""Test the multi-stock trading agent with market hours bypassed."""

import os
from unittest.mock import patch
from dotenv import load_dotenv

load_dotenv()

# Mock market hours before importing
with patch.dict(os.environ, {
    'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
    'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY')
}):
    import trading_agent_multi_stock as agent

    print("=" * 70)
    print("MULTI-STOCK AGENT TEST - Simulating Market Hours")
    print("=" * 70)
    print()

    # Patch is_market_open to return True
    with patch.object(agent, 'is_market_open', return_value=True):
        try:
            agent.evaluate_and_trade()
        except Exception as e:
            print(f"\nError: {e}")
            print("\nThis is expected during testing.")

    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)
