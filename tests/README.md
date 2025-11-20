# Tests

This directory contains the test suite for MarketInsightPro.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Shared pytest fixtures
├── test_analytics_engine.py # Tests for analytics calculations
├── test_data_generator.py  # Tests for data generation
└── README.md               # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov
```

### Run specific test file
```bash
pytest tests/test_analytics_engine.py
```

### Run specific test
```bash
pytest tests/test_analytics_engine.py::TestCalculateAllMetrics::test_metrics_with_valid_data
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Categories

Tests are marked with the following categories:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (may require DB)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.database` - Tests requiring database connection

## Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_trades_df` - Sample trade data for testing
- `sample_winning_trades_df` - All winning trades
- `sample_market_data` - OHLCV market data
- `sample_portfolio_data` - Portfolio configuration
- `sample_instrument_data` - Instrument configuration
- `sample_scenario_params` - Scenario parameters
- `mock_db_connection` - Mock database connection

## Writing New Tests

1. Create test file with `test_` prefix
2. Import required modules and fixtures
3. Organize tests into classes by functionality
4. Use descriptive test names
5. Follow AAA pattern: Arrange, Act, Assert

Example:
```python
def test_feature_with_valid_input(sample_trades_df):
    # Arrange
    input_data = sample_trades_df

    # Act
    result = my_function(input_data)

    # Assert
    assert result is not None
    assert result['key'] == expected_value
```

## TODO

- [ ] Add tests for database.py
- [ ] Add tests for scenario_engine.py
- [ ] Add tests for visualizations.py
- [ ] Add tests for portfolio_manager.py
- [ ] Add integration tests with real PostgreSQL
- [ ] Add UI tests for Streamlit app
- [ ] Increase coverage to 80%+
