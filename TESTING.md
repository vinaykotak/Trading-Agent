# Trading Agent Testing Guide

## Overview

This document explains the comprehensive test suite for the trading agent and how to use it to ensure the trading logic works correctly before deployment.

---

## Why Testing Matters

**Critical Importance:**
- ✅ Verify buy/sell signals trigger correctly
- ✅ Ensure stop-loss logic works as expected
- ✅ Validate position sizing calculations
- ✅ Test edge cases and error handling
- ✅ Prevent costly mistakes with real money

**Even in paper trading**, bugs can waste time and prevent you from learning if the strategy actually works.

---

## Test Suite Structure

### Test Categories

#### 1. **Moving Average Calculations** (`TestMovingAverageCalculations`)
- Basic MA calculation correctness
- Handling of NaN values
- MA behavior with trending data

#### 2. **Golden Cross Detection** (`TestGoldenCrossDetection`)
- Buy signal detection when MA50 crosses above MA200
- No false positives when MAs don't cross
- Crossover point identification

#### 3. **Death Cross Detection** (`TestDeathCrossDetection`)
- Sell signal detection when MA50 crosses below MA200
- Validation in downtrending markets

#### 4. **Stop-Loss Logic** (`TestStopLossLogic`)
- Stop price calculation (entry price - 5%)
- Trigger conditions
- Profit/loss percentage calculations

#### 5. **Position Sizing** (`TestPositionSizing`)
- Correct calculation of shares to buy
- Handling of fractional shares
- Insufficient funds scenarios

#### 6. **Market Hours Logic** (`TestMarketHoursLogic`)
- Detection of market open/closed status
- API error handling

#### 7. **Position Checking** (`TestPositionChecking`)
- Detection of existing positions
- Handling when no position exists

#### 8. **Data Validation** (`TestDataValidation`)
- Insufficient data handling
- NaN value handling
- Edge cases

#### 9. **Integration Scenarios** (`TestIntegrationScenarios`)
- Complete golden cross scenario
- Complete death cross scenario
- Ranging market (no signals)

#### 10. **Edge Cases** (`TestEdgeCases`)
- Exact MA crossover points
- Minimal data handling
- Zero/negative prices

---

## Running Tests

### Quick Start

```bash
# Install test dependencies (if not already installed)
pip3 install -r requirements.txt

# Run all tests
./run_tests.sh
```

### Test Runner Options

```bash
# Normal mode (default)
./run_tests.sh

# Verbose output (see each test)
./run_tests.sh -v

# With coverage report
./run_tests.sh -c

# Quiet mode (minimal output)
./run_tests.sh -q

# Re-run only failed tests
./run_tests.sh -f
```

### Using pytest Directly

```bash
# Run all tests
pytest test_trading_agent.py

# Verbose mode
pytest test_trading_agent.py -v

# Run specific test class
pytest test_trading_agent.py::TestGoldenCrossDetection -v

# Run specific test
pytest test_trading_agent.py::TestGoldenCrossDetection::test_golden_cross_detected -v

# Show print statements
pytest test_trading_agent.py -s

# Stop on first failure
pytest test_trading_agent.py -x

# With coverage
pytest test_trading_agent.py --cov=trading_agent_realtime --cov-report=html
```

---

## Understanding Test Results

### Successful Test Run

```
test_trading_agent.py::TestMovingAverageCalculations::test_calculate_moving_averages_basic PASSED
test_trading_agent.py::TestGoldenCrossDetection::test_golden_cross_detected PASSED
test_trading_agent.py::TestStopLossLogic::test_stop_loss_calculation PASSED
...
==================== 30 passed in 2.45s ====================
```

**All tests passed ✓** - Your trading logic is working correctly!

### Failed Test Run

```
test_trading_agent.py::TestGoldenCrossDetection::test_golden_cross_detected FAILED

FAILED test_trading_agent.py::TestGoldenCrossDetection::test_golden_cross_detected
AssertionError: Golden cross should be detected in uptrending data
```

**Test failed ✗** - There's a bug in the golden cross detection logic that needs fixing.

---

## Test Coverage

### View Coverage Report

```bash
# Generate HTML coverage report
./run_tests.sh -c

# Open the report (if on local machine with browser)
# open htmlcov/index.html

# View in terminal
pytest test_trading_agent.py --cov=trading_agent_realtime --cov-report=term-missing
```

### Coverage Goals

- **Minimum acceptable**: 70% coverage
- **Good**: 80% coverage
- **Excellent**: 90%+ coverage

**Critical functions that MUST be tested:**
- `calculate_moving_averages()`
- `evaluate_and_trade()` (via integration tests)
- Position sizing logic
- Stop-loss triggers

---

## Key Test Scenarios Explained

### 1. Golden Cross Test

**What it tests:**
```python
def test_golden_cross_detected(self):
    # Creates data where MA50 crosses above MA200
    # Verifies the crossover is detected
```

**Why it matters:** This is your BUY signal. If this test fails, you won't enter positions when you should.

### 2. Death Cross Test

**What it tests:**
```python
def test_death_cross_detected(self):
    # Creates data where MA50 crosses below MA200
    # Verifies the crossover is detected
```

**Why it matters:** This is your SELL signal. If this fails, you won't exit positions when you should.

### 3. Stop-Loss Test

**What it tests:**
```python
def test_stop_loss_triggered(self):
    # Simulates price dropping 5%
    # Verifies stop-loss trigger condition
```

**Why it matters:** Stop-loss protects you from large losses. This must work perfectly.

### 4. Integration Scenarios

**What they test:**
- Complete trading workflows from data fetch to signal detection
- Real-world market patterns (uptrend, downtrend, ranging)

**Why they matter:** Unit tests check individual pieces, but integration tests ensure everything works together.

---

## Adding New Tests

### When to Add Tests

Add tests whenever you:
- Modify trading logic
- Add new features
- Fix bugs (write a test that catches the bug first)
- Want to test a specific market scenario

### Test Template

```python
def test_your_scenario(self):
    """Clear description of what you're testing."""
    # 1. Arrange - set up test data
    data = create_test_data()

    # 2. Act - run the function
    result = function_under_test(data)

    # 3. Assert - verify the result
    assert result == expected_value, "Error message if fails"
```

### Example: Adding a Test for a New Feature

Let's say you want to add a "take profit" feature:

```python
class TestTakeProfitLogic:
    """Test take-profit functionality."""

    def test_take_profit_calculation(self):
        """Test that take-profit price is calculated correctly."""
        entry_price = 100.0
        take_profit_pct = 0.10  # 10%

        expected_tp_price = entry_price * (1 + take_profit_pct)
        assert expected_tp_price == 110.0

    def test_take_profit_triggered(self):
        """Test take-profit trigger condition."""
        entry_price = 100.0
        tp_price = 110.0
        current_price = 111.0

        should_sell = current_price >= tp_price
        assert should_sell is True
```

---

## Continuous Testing Workflow

### Before Committing Code

```bash
# Always run tests before committing
./run_tests.sh

# If tests pass, commit
git add .
git commit -m "Your change description"
```

### Before Deploying

```bash
# Run full test suite with coverage
./run_tests.sh -c

# Manually test the script
python3 trading_agent_realtime.py

# Deploy only if both pass
sudo ./setup_service.sh
```

### After Modifying Strategy

```bash
# Run tests
./run_tests.sh -v

# If tests fail, fix the code
# Run tests again until they pass
```

---

## Common Test Failures & Solutions

### Failure: "Golden cross should be detected"

**Cause:** Buy signal logic is broken
**Solution:** Check the crossover detection in `evaluate_and_trade()`:
```python
golden_cross = prev_ma50 < prev_ma200 and curr_ma50 > curr_ma200
```

### Failure: "AssertionError: assert 0 == 25"

**Cause:** Position sizing calculation is wrong
**Solution:** Verify the calculation:
```python
qty = int(invest_amount // current_price)
```

### Failure: "ModuleNotFoundError: No module named 'pytest'"

**Cause:** Test dependencies not installed
**Solution:**
```bash
pip3 install -r requirements.txt
```

### Failure: "ImportError: cannot import name 'agent'"

**Cause:** Environment variables not set for import
**Solution:** Tests automatically mock environment variables, but check:
```python
with patch.dict(os.environ, {
    'ALPACA_API_KEY': 'test_key',
    'ALPACA_SECRET_KEY': 'test_secret'
}):
```

---

## Mocking vs. Real API Calls

### Why We Mock

The test suite uses **mocks** instead of real API calls:

**Advantages:**
- ✅ Tests run instantly (no network delay)
- ✅ No API rate limits
- ✅ No need for internet connection
- ✅ Tests are deterministic (same result every time)
- ✅ Can simulate error conditions easily

**What we mock:**
- Alpaca API calls (`api.get_clock()`, `api.submit_order()`, etc.)
- Market data fetching
- Position queries

### Integration Testing with Real API

For final validation, you can also test with the real API:

```bash
# Set up real credentials in .env
# Run the script manually
python3 trading_agent_realtime.py

# Check Alpaca paper trading dashboard
# Verify orders, positions, etc.
```

---

## Best Practices

1. **Run tests frequently** - After every code change
2. **Keep tests fast** - Use mocks for external dependencies
3. **Test edge cases** - Not just happy paths
4. **Write descriptive test names** - `test_golden_cross_detected` not `test1`
5. **One assertion per test** - Makes failures easier to diagnose
6. **Keep tests independent** - Tests shouldn't depend on each other
7. **Document complex tests** - Add comments explaining the scenario

---

## Troubleshooting

### Tests are slow

**Cause:** Generating large datasets or making real API calls
**Solution:** Use smaller datasets in tests, ensure proper mocking

### Tests pass locally but fail in service

**Cause:** Different environment or missing dependencies
**Solution:** Ensure `.env` is configured, check systemd logs

### Flaky tests (sometimes pass, sometimes fail)

**Cause:** Using random data or timing-dependent logic
**Solution:** Use fixed random seeds or deterministic test data

---

## Next Steps

After all tests pass:

1. ✅ **Review test coverage** - Aim for 80%+
2. ✅ **Manual testing** - Run the script directly
3. ✅ **Paper trading validation** - Deploy and monitor for 1-2 weeks
4. ✅ **Add scenario-specific tests** - Based on your observations
5. ✅ **Update tests when strategy changes** - Keep tests in sync with code

---

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Python unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Testing Best Practices**: https://realpython.com/pytest-python-testing/

---

## Questions?

Review test failures carefully - they're catching bugs before they cost you money!
