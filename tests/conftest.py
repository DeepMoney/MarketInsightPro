"""
Pytest configuration and shared fixtures for MarketInsightPro tests
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.fixture
def sample_trades_df():
    """
    Create a sample DataFrame of trades for testing.

    Returns:
        pd.DataFrame: Sample trade data with typical columns
    """
    np.random.seed(42)
    n_trades = 100

    # Generate sample trade data
    entry_times = [datetime(2025, 1, 1) + timedelta(hours=i) for i in range(n_trades)]
    exit_times = [entry_time + timedelta(hours=np.random.randint(1, 24))
                  for entry_time in entry_times]

    data = {
        'id': range(1, n_trades + 1),
        'instrument': ['MES'] * n_trades,
        'direction': np.random.choice(['long', 'short'], n_trades),
        'entry_time': entry_times,
        'exit_time': exit_times,
        'entry_price': 4500 + np.random.randn(n_trades) * 10,
        'exit_price': 4500 + np.random.randn(n_trades) * 10,
        'pnl': np.random.randn(n_trades) * 100 + 10,  # Slightly positive expectancy
        'holding_minutes': np.random.randint(60, 1440, n_trades),
        'r_multiple': np.random.randn(n_trades) * 2
    }

    df = pd.DataFrame(data)
    df['exit_price'] = df.apply(
        lambda row: row['entry_price'] + (row['pnl'] / 5) if row['direction'] == 'long'
        else row['entry_price'] - (row['pnl'] / 5),
        axis=1
    )

    return df


@pytest.fixture
def sample_winning_trades_df():
    """
    Create a DataFrame with only winning trades for testing.

    Returns:
        pd.DataFrame: Sample winning trade data
    """
    n_trades = 50
    entry_times = [datetime(2025, 1, 1) + timedelta(hours=i) for i in range(n_trades)]
    exit_times = [entry_time + timedelta(hours=2) for entry_time in entry_times]

    data = {
        'id': range(1, n_trades + 1),
        'instrument': ['MES'] * n_trades,
        'direction': ['long'] * n_trades,
        'entry_time': entry_times,
        'exit_time': exit_times,
        'entry_price': [4500.0] * n_trades,
        'exit_price': [4510.0] * n_trades,
        'pnl': [50.0] * n_trades,
        'holding_minutes': [120] * n_trades,
        'r_multiple': [1.5] * n_trades
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_market_data():
    """
    Create sample OHLCV market data for testing.

    Returns:
        pd.DataFrame: Sample market data
    """
    dates = pd.date_range(start='2025-01-01', periods=100, freq='15min')

    data = {
        'timestamp': dates,
        'open': 4500 + np.random.randn(100) * 5,
        'high': 4505 + np.random.randn(100) * 5,
        'low': 4495 + np.random.randn(100) * 5,
        'close': 4500 + np.random.randn(100) * 5,
        'volume': np.random.randint(1000, 10000, 100)
    }

    df = pd.DataFrame(data)

    # Ensure OHLC relationships are valid
    df['high'] = df[['open', 'close']].max(axis=1) + np.abs(np.random.randn(100) * 2)
    df['low'] = df[['open', 'close']].min(axis=1) - np.abs(np.random.randn(100) * 2)

    return df


@pytest.fixture
def sample_portfolio_data():
    """
    Create sample portfolio configuration for testing.

    Returns:
        dict: Sample portfolio configuration
    """
    return {
        'id': 'test-portfolio-uuid',
        'name': 'Test Portfolio',
        'instrument_id': 'MES',
        'starting_capital': 10000.0,
        'status': 'simulated',
        'description': 'Test portfolio for unit tests',
        'created_at': datetime(2025, 1, 1)
    }


@pytest.fixture
def sample_instrument_data():
    """
    Create sample instrument configuration for testing.

    Returns:
        dict: Sample instrument configuration
    """
    return {
        'id': 'MES',
        'market_id': 'index_futures',
        'symbol': 'MES',
        'timeframe': '15min',
        'name': 'Micro E-mini S&P 500',
        'tick_value': 1.25,
        'margin_requirement': 1200.0,
        'commission_per_contract': 0.62
    }


@pytest.fixture
def sample_scenario_params():
    """
    Create sample scenario parameters for testing.

    Returns:
        dict: Sample scenario parameters
    """
    return {
        'name': 'Test Scenario',
        'stop_loss_pct': 2.0,
        'take_profit_pct': 3.0,
        'max_holding_minutes': 480,
        'day_filter': [1, 2, 3, 4, 5],  # Mon-Fri
        'capital_multiplier': 1.0,
        'position_size_multiplier': 1.0
    }


@pytest.fixture
def mock_db_connection(monkeypatch):
    """
    Mock database connection for tests that don't need real DB.

    This fixture can be expanded based on specific testing needs.
    """
    class MockConnection:
        def cursor(self):
            return MockCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    class MockCursor:
        def execute(self, query, params=None):
            pass

        def fetchall(self):
            return []

        def fetchone(self):
            return None

        def close(self):
            pass

    def mock_get_connection():
        return MockConnection()

    # This would be used with monkeypatch in actual tests
    return mock_get_connection
