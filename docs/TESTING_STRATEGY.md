# Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the DMarket Telegram Bot project.

---

## Test Pyramid

```
        /\
       /  \
      / E2E \ (10-15%)
     /______\
    /        \
   / Integration \ (20-25%)
  /______________\
 /                \
/   Unit Tests     \ (60-70%)
\__________________/
```

---

## 1. Unit Tests (60-70% coverage)

### Purpose

Test individual functions and methods in isolation.

### Location

- `tests/unit/`

### Framework

- `pytest`
- `pytest-asyncio`
- `pytest-mock`

### Guidelines

- Test one thing per test
- Use AAA pattern (Arrange-Act-Assert)
- Mock external dependencies
- Test edge cases and error handling

### Example

```python
@pytest.mark.asyncio
async def test_calculate_profit_returns_correct_value():
    """Test profit calculation with standard inputs."""
    # Arrange
    buy_price = 10.00
    sell_price = 15.00
    commission = 7.0

    # Act
    profit = calculate_profit(buy_price, sell_price, commission)

    # Assert
    assert profit == 3.95
```

---

## 2. Integration Tests (20-25% coverage)

### Purpose

Test interactions between multiple components.

### Location

- `tests/integration/`

### What to Test

- API client with mocked HTTP responses
- Database operations
- Cache interactions
- Message queue processing

### Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_scanner_with_api():
    """Test scanner integrates correctly with API client."""
    # Arrange
    api_client = DMarketAPI(public_key="test", secret_key="test")
    scanner = ArbitrageScanner(api_client=api_client)

    # Mock API response
    with patch.object(api_client, 'get_market_items'):
        # Act
        results = await scanner.scan_level("standard", "csgo")

        # Assert
        assert len(results) > 0
```

---

## 3. E2E Tests (10-15% coverage)

### Purpose

Test complete user workflows from start to finish.

### Location

- `tests/e2e/`

### What to Test

- Complete arbitrage flow (scan → analyze → notify)
- Target management flow (create → monitor → execute)
- Notification delivery flow (trigger → queue → deliver)
- User settings flow (update → apply → verify)

### Example

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_arbitrage_workflow():
    """Test full arbitrage workflow."""
    # 1. Scan market
    opportunities = await scanner.scan_level("standard", "csgo")

    # 2. Select best opportunity
    best = max(opportunities, key=lambda x: x.profit_margin)

    # 3. Create target
    target = await target_manager.create_target(
        game="csgo",
        item_title=best.title,
        price=best.buy_price
    )

    # 4. Verify notification sent
    assert notification_queue.size() > 0
```

---

## 4. Contract Testing (Pact)

### Purpose

Verify API contracts between consumer and provider.

### Location

- `tests/contracts/`

### What to Test

- DMarket API responses match expected schema
- Telegram Bot API requests are correct
- WebSocket message formats

### Example

```python
@pytest.mark.contract
def test_dmarket_api_balance_contract():
    """Test DMarket balance endpoint contract."""
    pact.given("User has balance") \
        .upon_receiving("A balance request") \
        .with_request("GET", "/account/v1/balance") \
        .will_respond_with(200, body={
            "usd": Matcher("10000"),
            "dmc": Matcher("5000")
        })
```

---

## 5. Property-Based Testing (Hypothesis)

### Purpose

Test properties that should hold for all inputs.

### Location

- Mixed with unit tests

### Example

```python
from hypothesis import given, strategies as st

@given(
    buy_price=st.floats(min_value=0.01, max_value=10000),
    sell_price=st.floats(min_value=0.01, max_value=10000)
)
def test_profit_is_always_less_than_sell_price(buy_price, sell_price):
    """Property: profit should never exceed sell price."""
    if sell_price > buy_price:
        profit = calculate_profit(buy_price, sell_price, 7.0)
        assert profit < sell_price
```

---

## Test Execution

### Run All Tests

```bash
pytest tests/
```

### Run by Type

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -m integration

# E2E tests
pytest tests/e2e/ -m e2e

# Exclude slow tests
pytest -m "not e2e"
```

### With Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v

      - name: Run integration tests
        run: pytest tests/integration/ -m integration

      - name: Run E2E tests
        run: pytest tests/e2e/ -m e2e

      - name: Generate coverage
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Data Management

### Fixtures

- Use `conftest.py` for shared fixtures
- Create realistic test data
- Use factories for complex objects

### VCR.py

- Record HTTP interactions
- Replay in tests
- Located in `tests/cassettes/`

### Example

```python
@pytest.mark.vcr()
async def test_api_with_recorded_response():
    """Test using VCR recorded response."""
    api = DMarketAPI(public_key="test", secret_key="test")
    balance = await api.get_balance()
    assert balance is not None
```

---

## Performance Testing

### Load Testing

- Use `locust` for load testing
- Test API rate limits
- Verify scalability

### Profiling

- Use `py-spy` for profiling
- Monitor memory usage
- Identify bottlenecks

---

## Test Quality Metrics

### Target Coverage

- **Unit Tests**: 80-85%
- **Integration Tests**: 60-70%
- **E2E Tests**: 40-50%
- **Overall**: 85%+

### Test Quality Checks

- ✅ No flaky tests
- ✅ Fast execution (<5 minutes)
- ✅ Clear test names
- ✅ Independent tests
- ✅ Proper mocking

---

## Best Practices

### DO ✅

- Write tests before fixing bugs
- Keep tests simple and focused
- Use descriptive test names
- Test edge cases
- Mock external dependencies
- Clean up resources

### DON'T ❌

- Test implementation details
- Write interdependent tests
- Use magic numbers
- Skip error cases
- Leave commented code
- Ignore flaky tests

---

## Debugging Failed Tests

### Steps

1. **Read error message** - understand what failed
2. **Check recent changes** - what code changed?
3. **Reproduce locally** - run test in isolation
4. **Add logging** - use `logger.debug()` liberally
5. **Use debugger** - `pytest --pdb`
6. **Check fixtures** - verify test data is correct

### Example

```bash
# Run single test with verbose output
pytest tests/unit/test_arbitrage_scanner.py::test_scan_level -vv

# Run with debugger on failure
pytest tests/unit/ --pdb

# Run with print statements visible
pytest tests/unit/ -s
```

---

## Maintenance

### Regular Tasks

- **Weekly**: Review test coverage reports
- **Monthly**: Update test data
- **Quarterly**: Refactor slow tests
- **Annually**: Review testing strategy

### Test Cleanup

- Remove obsolete tests
- Update deprecated patterns
- Improve test performance
- Reduce duplication

---

## Resources

### Documentation

- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Hypothesis](https://hypothesis.readthedocs.io/)
- [Pact Python](https://github.com/pact-foundation/pact-python)

### Internal Docs

- `docs/TESTING_GUIDE.md` - detailed testing guide
- `docs/CONTRACT_TESTING.md` - contract testing guide
- `tests/README.md` - test suite overview

---

**Last Updated**: January 1, 2026
**Version**: 1.0.0
