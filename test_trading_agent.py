"""
Comprehensive test suite for trading_agent_realtime.py

Run with: pytest test_trading_agent.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from zoneinfo import ZoneInfo

# Import functions from the trading agent
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock environment variables before importing
with patch.dict(os.environ, {
    'ALPACA_API_KEY': 'test_key',
    'ALPACA_SECRET_KEY': 'test_secret'
}):
    import trading_agent_multi_stock as agent


class TestMovingAverageCalculations:
    """Test the moving average calculation logic."""

    def test_calculate_moving_averages_basic(self):
        """Test basic MA calculation with simple data."""
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
        data = pd.DataFrame({
            'close': np.arange(1, 251, dtype=float),  # Simple ascending series
            'symbol': ['TEST'] * 250
        }, index=dates)

        ma50, ma200 = agent.calculate_moving_averages(data)

        # Check that we get the right length
        assert len(ma50) == 250
        assert len(ma200) == 250

        # First 49 values should be NaN for MA50 (index 0-48)
        assert pd.isna(ma50.iloc[48])
        assert not pd.isna(ma50.iloc[49])  # First valid MA50 at index 49

        # First 199 values should be NaN for MA200 (index 0-198)
        assert pd.isna(ma200.iloc[198])
        assert not pd.isna(ma200.iloc[199])  # First valid MA200 at index 199

    def test_calculate_moving_averages_values(self):
        """Test MA calculations produce correct values."""
        # Create data with known values
        data = pd.DataFrame({
            'close': [100.0] * 250  # Constant price
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # All non-NaN values should equal 100
        assert ma50.iloc[49] == 100.0
        assert ma200.iloc[199] == 100.0

    def test_calculate_moving_averages_trend(self):
        """Test MA calculation with trending data."""
        # Create uptrending data
        data = pd.DataFrame({
            'close': list(range(1, 251))
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # MA50 should be less than MA200 for uptrending data
        # (shorter MA reacts faster to trends)
        assert ma50.iloc[-1] > ma200.iloc[-1]


class TestGoldenCrossDetection:
    """Test golden cross (buy signal) detection."""

    def create_golden_cross_data(self):
        """Create data that produces a golden cross."""
        # Create scenario where MA50 crosses above MA200
        prices = []

        # Start with strong downtrend for 200 days (MA50 will be below MA200)
        base_price = 200.0
        for i in range(200):
            prices.append(base_price - i * 0.5)

        # Then strong uptrend for 100 days (MA50 will cross above MA200)
        start_price = prices[-1]
        for i in range(100):
            prices.append(start_price + i * 1.0)

        return pd.DataFrame({'close': prices})

    def test_golden_cross_detected(self):
        """Test that golden cross is properly detected."""
        data = self.create_golden_cross_data()
        ma50, ma200 = agent.calculate_moving_averages(data)

        # Find the crossover point
        crossover_detected = False
        for i in range(200, len(data) - 1):
            # Skip if either MA is NaN
            if pd.isna(ma50.iloc[i]) or pd.isna(ma200.iloc[i]):
                continue
            if pd.isna(ma50.iloc[i-1]) or pd.isna(ma200.iloc[i-1]):
                continue

            # Check for golden cross: MA50 crosses from below to above MA200
            if (ma50.iloc[i-1] < ma200.iloc[i-1] and
                ma50.iloc[i] > ma200.iloc[i]):
                crossover_detected = True
                break

        assert crossover_detected, "Golden cross should be detected in uptrending data"

    def test_no_golden_cross_when_ma50_below(self):
        """Test that golden cross is NOT detected when MA50 stays below MA200."""
        # Create downtrending data
        data = pd.DataFrame({
            'close': [100 - i*0.1 for i in range(250)]
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # In downtrend, MA50 should be below MA200
        assert ma50.iloc[-1] < ma200.iloc[-1]


class TestDeathCrossDetection:
    """Test death cross (sell signal) detection."""

    def create_death_cross_data(self):
        """Create data that produces a death cross."""
        prices = []

        # Start with uptrend (MA50 > MA200)
        prices.extend([100 + i*0.3 for i in range(150)])

        # Then downtrend (MA50 < MA200)
        prices.extend([145 - i*0.3 for i in range(100)])

        return pd.DataFrame({'close': prices})

    def test_death_cross_detected(self):
        """Test that death cross is properly detected."""
        data = self.create_death_cross_data()
        ma50, ma200 = agent.calculate_moving_averages(data)

        # Find the crossover point
        crossover_detected = False
        for i in range(200, len(data) - 1):
            if (ma50.iloc[i-1] > ma200.iloc[i-1] and
                ma50.iloc[i] < ma200.iloc[i]):
                crossover_detected = True
                break

        assert crossover_detected, "Death cross should be detected in downtrending data"


class TestStopLossLogic:
    """Test stop-loss calculation and triggering."""

    def test_stop_loss_calculation(self):
        """Test that stop-loss price is calculated correctly."""
        entry_price = 100.0
        stop_loss_pct = 0.05  # 5%

        expected_stop_price = entry_price * (1 - stop_loss_pct)

        assert expected_stop_price == 95.0

    def test_stop_loss_triggered(self):
        """Test stop-loss trigger condition."""
        entry_price = 100.0
        stop_loss_pct = 0.05
        stop_price = entry_price * (1 - stop_loss_pct)

        # Prices that should trigger stop-loss
        assert 94.0 <= stop_price  # Should trigger
        assert 95.0 <= stop_price  # Should trigger (at exact stop price)

        # Prices that should NOT trigger stop-loss
        assert not (96.0 <= stop_price)  # Should not trigger

    def test_profit_loss_calculation(self):
        """Test profit/loss percentage calculation."""
        entry_price = 100.0

        # Test profit
        current_price = 110.0
        pl_pct = ((current_price - entry_price) / entry_price) * 100
        assert pl_pct == 10.0

        # Test loss
        current_price = 95.0
        pl_pct = ((current_price - entry_price) / entry_price) * 100
        assert pl_pct == -5.0


class TestPositionSizing:
    """Test position sizing calculations."""

    def test_position_size_calculation(self):
        """Test that position size is calculated correctly."""
        portfolio_value = 10000.0
        max_investment_pct = 0.25  # 25%
        current_price = 100.0

        invest_amount = portfolio_value * max_investment_pct
        qty = int(invest_amount // current_price)

        assert invest_amount == 2500.0
        assert qty == 25

    def test_position_size_with_fractional_shares(self):
        """Test position sizing when price doesn't divide evenly."""
        portfolio_value = 10000.0
        max_investment_pct = 0.25
        current_price = 333.33

        invest_amount = portfolio_value * max_investment_pct
        qty = int(invest_amount // current_price)

        assert qty == 7  # 2500 / 333.33 = 7.5, truncated to 7

    def test_insufficient_funds(self):
        """Test handling of insufficient funds."""
        portfolio_value = 100.0
        max_investment_pct = 0.25
        current_price = 1000.0

        invest_amount = portfolio_value * max_investment_pct
        qty = int(invest_amount // current_price)

        assert qty == 0  # Not enough money to buy even 1 share


class TestMarketHoursLogic:
    """Test market hours checking logic."""

    @patch.object(agent, 'api')
    def test_market_open(self, mock_api):
        """Test detection when market is open."""
        mock_clock = Mock()
        mock_clock.is_open = True
        mock_api.get_clock.return_value = mock_clock

        result = agent.is_market_open()
        assert result is True

    @patch.object(agent, 'api')
    def test_market_closed(self, mock_api):
        """Test detection when market is closed."""
        mock_clock = Mock()
        mock_clock.is_open = False
        mock_api.get_clock.return_value = mock_clock

        result = agent.is_market_open()
        assert result is False

    @patch.object(agent, 'api')
    def test_market_status_api_error(self, mock_api):
        """Test handling of API errors when checking market status."""
        mock_api.get_clock.side_effect = Exception("API Error")

        result = agent.is_market_open()
        assert result is False  # Should return False on error


class TestPositionChecking:
    """Test position checking logic."""

    @patch.object(agent, 'api')
    def test_has_position(self, mock_api):
        """Test detection of existing position."""
        mock_position = Mock()
        mock_position.qty = "10"
        mock_api.get_open_position.return_value = mock_position

        result = agent.has_open_position("MSFT")
        assert result == 10.0

    @patch.object(agent, 'api')
    def test_no_position(self, mock_api):
        """Test detection when no position exists."""
        mock_api.get_open_position.side_effect = Exception("No position")

        result = agent.has_open_position("MSFT")
        assert result == 0


class TestDataValidation:
    """Test data validation and error handling."""

    def test_insufficient_data_length(self):
        """Test handling of insufficient data for MA calculation."""
        # Only 100 days of data (need 200 for MA200)
        data = pd.DataFrame({
            'close': list(range(100))
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # MA200 should be all NaN
        assert pd.isna(ma200.iloc[-1])
        # MA50 should have some valid values
        assert not pd.isna(ma50.iloc[-1])

    def test_nan_handling(self):
        """Test handling of NaN values in price data."""
        data = pd.DataFrame({
            'close': [100.0] * 50 + [np.nan] * 50 + [100.0] * 150
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # MAs should handle NaN appropriately
        assert isinstance(ma50, pd.Series)
        assert isinstance(ma200, pd.Series)


class TestIntegrationScenarios:
    """Integration tests for complete trading scenarios."""

    def create_complete_dataset(self, scenario='golden_cross'):
        """Create a complete dataset for testing full scenarios."""
        if scenario == 'golden_cross':
            # Downtrend followed by uptrend
            prices = [100 - i*0.1 for i in range(150)]
            prices.extend([85 + i*0.3 for i in range(100)])
        elif scenario == 'death_cross':
            # Uptrend followed by downtrend
            prices = [100 + i*0.3 for i in range(150)]
            prices.extend([145 - i*0.3 for i in range(100)])
        else:
            # Ranging market
            prices = [100 + np.sin(i*0.1)*5 for i in range(250)]

        dates = pd.date_range(start='2023-01-01', periods=len(prices), freq='D')
        return pd.DataFrame({
            'close': prices,
            'open': prices,
            'high': [p*1.02 for p in prices],
            'low': [p*0.98 for p in prices],
            'volume': [1000000] * len(prices)
        }, index=dates)

    def test_golden_cross_scenario(self):
        """Test complete golden cross scenario."""
        data = self.create_complete_dataset('golden_cross')
        ma50, ma200 = agent.calculate_moving_averages(data)

        # Verify we have valid MAs
        assert not pd.isna(ma50.iloc[-1])
        assert not pd.isna(ma200.iloc[-1])

        # In this scenario, MA50 should eventually cross above MA200
        # Check that crossover exists somewhere in the data
        crossed = False
        for i in range(200, len(data)-1):
            if ma50.iloc[i-1] < ma200.iloc[i-1] and ma50.iloc[i] > ma200.iloc[i]:
                crossed = True
                break

        assert crossed, "Golden cross should occur in this scenario"

    def test_death_cross_scenario(self):
        """Test complete death cross scenario."""
        data = self.create_complete_dataset('death_cross')
        ma50, ma200 = agent.calculate_moving_averages(data)

        # Verify we have valid MAs
        assert not pd.isna(ma50.iloc[-1])
        assert not pd.isna(ma200.iloc[-1])

        # Check that death cross exists
        crossed = False
        for i in range(200, len(data)-1):
            if ma50.iloc[i-1] > ma200.iloc[i-1] and ma50.iloc[i] < ma200.iloc[i]:
                crossed = True
                break

        assert crossed, "Death cross should occur in this scenario"

    def test_no_signal_scenario(self):
        """Test ranging market with no clear signals."""
        data = self.create_complete_dataset('ranging')
        ma50, ma200 = agent.calculate_moving_averages(data)

        # Verify MAs are calculated
        assert not pd.isna(ma50.iloc[-1])
        assert not pd.isna(ma200.iloc[-1])

        # In ranging market, MAs should be relatively close
        diff_pct = abs(ma50.iloc[-1] - ma200.iloc[-1]) / ma200.iloc[-1] * 100
        # Difference should be small in ranging market
        assert diff_pct < 10.0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_exact_crossover_point(self):
        """Test behavior when MAs are exactly equal."""
        data = pd.DataFrame({
            'close': [100.0] * 250
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # When prices are constant, MAs should be equal
        assert ma50.iloc[-1] == ma200.iloc[-1] == 100.0

    def test_single_data_point(self):
        """Test handling of minimal data."""
        data = pd.DataFrame({
            'close': [100.0]
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # Should not crash, but MAs will be NaN
        assert pd.isna(ma50.iloc[0])
        assert pd.isna(ma200.iloc[0])

    def test_zero_price(self):
        """Test handling of zero prices (data error)."""
        data = pd.DataFrame({
            'close': [100.0] * 100 + [0.0] + [100.0] * 149
        })

        ma50, ma200 = agent.calculate_moving_averages(data)

        # Should still calculate, but values will be affected
        assert isinstance(ma50, pd.Series)
        assert isinstance(ma200, pd.Series)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
