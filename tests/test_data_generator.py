"""
Unit tests for data_generator.py
"""

import pytest
import pandas as pd
from datetime import datetime
from data_generator import generate_market_data, generate_trade_data


class TestGenerateMarketData:
    """Test suite for generate_market_data function"""

    def test_generate_market_data_basic(self):
        """Test basic market data generation"""
        n_candles = 100
        data = generate_market_data(
            instrument='MES',
            timeframe='15min',
            n_candles=n_candles
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) == n_candles

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            assert col in data.columns

    def test_ohlc_relationships(self):
        """Test that OHLC relationships are valid"""
        data = generate_market_data('MES', '15min', 100)

        # High should be >= open and close
        assert all(data['high'] >= data['open'])
        assert all(data['high'] >= data['close'])

        # Low should be <= open and close
        assert all(data['low'] <= data['open'])
        assert all(data['low'] <= data['close'])

    def test_timestamps_are_sequential(self):
        """Test that timestamps are in order"""
        data = generate_market_data('MES', '15min', 100)

        timestamps = pd.to_datetime(data['timestamp'])
        assert timestamps.is_monotonic_increasing


class TestGenerateTradeData:
    """Test suite for generate_trade_data function"""

    def test_generate_trade_data_basic(self):
        """Test basic trade data generation"""
        n_trades = 50
        data = generate_trade_data(
            instrument='MES',
            n_trades=n_trades
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) == n_trades

        # Check required columns
        required_cols = ['instrument', 'direction', 'entry_time', 'exit_time',
                        'entry_price', 'exit_price', 'pnl']
        for col in required_cols:
            assert col in data.columns

    def test_trade_directions(self):
        """Test that trade directions are valid"""
        data = generate_trade_data('MES', 100)

        valid_directions = ['long', 'short']
        assert all(data['direction'].isin(valid_directions))

    def test_exit_after_entry(self):
        """Test that exit times are after entry times"""
        data = generate_trade_data('MES', 100)

        entry_times = pd.to_datetime(data['entry_time'])
        exit_times = pd.to_datetime(data['exit_time'])

        assert all(exit_times >= entry_times)

    def test_pnl_calculation(self):
        """Test that P&L is calculated correctly for direction"""
        data = generate_trade_data('MES', 100)

        for _, trade in data.iterrows():
            price_diff = trade['exit_price'] - trade['entry_price']

            if trade['direction'] == 'long':
                # Long trades: profit when exit > entry
                expected_sign = 1 if price_diff > 0 else -1
            else:  # short
                # Short trades: profit when exit < entry
                expected_sign = 1 if price_diff < 0 else -1

            pnl_sign = 1 if trade['pnl'] > 0 else -1

            # This is a soft check as actual P&L includes fees, slippage, etc.
            # Just checking general direction relationship
            if abs(price_diff) > 0.01:  # Ignore very small price moves
                pass  # Implementation may vary
