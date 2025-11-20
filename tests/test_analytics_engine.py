"""
Unit tests for analytics_engine.py
"""

import pytest
import pandas as pd
import numpy as np
from analytics_engine import (
    calculate_all_metrics,
    get_equity_curve,
    get_time_of_day_performance,
    get_r_multiple_distribution
)


class TestCalculateAllMetrics:
    """Test suite for calculate_all_metrics function"""

    def test_metrics_with_valid_data(self, sample_trades_df):
        """Test metric calculation with valid trade data"""
        metrics = calculate_all_metrics(sample_trades_df)

        # Check that all expected keys are present
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'total_pnl' in metrics
        assert 'avg_win' in metrics
        assert 'avg_loss' in metrics
        assert 'max_drawdown' in metrics

        # Check value types and ranges
        assert metrics['total_trades'] == len(sample_trades_df)
        assert 0 <= metrics['win_rate'] <= 100
        assert metrics['profit_factor'] >= 0

    def test_metrics_with_all_winning_trades(self, sample_winning_trades_df):
        """Test metrics when all trades are winners"""
        metrics = calculate_all_metrics(sample_winning_trades_df)

        assert metrics['win_rate'] == 100.0
        assert metrics['total_pnl'] > 0
        assert metrics['avg_loss'] == 0

    def test_metrics_with_empty_dataframe(self):
        """Test that empty DataFrame is handled gracefully"""
        empty_df = pd.DataFrame()

        with pytest.raises((ValueError, KeyError)):
            calculate_all_metrics(empty_df)

    def test_metrics_with_missing_columns(self, sample_trades_df):
        """Test that missing required columns raise appropriate errors"""
        incomplete_df = sample_trades_df.drop(columns=['pnl'])

        with pytest.raises((ValueError, KeyError)):
            calculate_all_metrics(incomplete_df)


class TestGetEquityCurve:
    """Test suite for get_equity_curve function"""

    def test_equity_curve_basic(self, sample_trades_df):
        """Test equity curve generation with valid data"""
        starting_capital = 10000.0
        equity_df = get_equity_curve(sample_trades_df, starting_capital)

        assert isinstance(equity_df, pd.DataFrame)
        assert 'equity' in equity_df.columns
        assert len(equity_df) == len(sample_trades_df)

        # Check that equity starts at starting_capital
        # (first trade equity = starting_capital + first trade pnl)
        assert equity_df['equity'].iloc[0] == starting_capital + sample_trades_df['pnl'].iloc[0]

    def test_equity_curve_is_cumulative(self, sample_trades_df):
        """Test that equity curve accumulates P&L correctly"""
        starting_capital = 10000.0
        equity_df = get_equity_curve(sample_trades_df, starting_capital)

        # Final equity should be starting capital + total P&L
        expected_final = starting_capital + sample_trades_df['pnl'].sum()
        assert abs(equity_df['equity'].iloc[-1] - expected_final) < 0.01


class TestGetTimeOfDayPerformance:
    """Test suite for get_time_of_day_performance function"""

    def test_time_of_day_performance(self, sample_trades_df):
        """Test time-of-day performance analysis"""
        result = get_time_of_day_performance(sample_trades_df)

        assert isinstance(result, (pd.DataFrame, dict))

    @pytest.mark.skip(reason="Implementation details may vary")
    def test_time_of_day_with_timezone(self, sample_trades_df):
        """Test handling of timezone-aware timestamps"""
        # This test would need timezone-aware sample data
        pass


class TestGetRMultipleDistribution:
    """Test suite for get_r_multiple_distribution function"""

    def test_r_multiple_distribution(self, sample_trades_df):
        """Test R-multiple distribution calculation"""
        result = get_r_multiple_distribution(sample_trades_df)

        assert isinstance(result, (pd.Series, pd.DataFrame, dict))

    def test_r_multiple_with_missing_column(self, sample_trades_df):
        """Test handling when r_multiple column is missing"""
        df_no_r = sample_trades_df.drop(columns=['r_multiple'])

        # Should either calculate r_multiple or handle gracefully
        # Implementation detail depends on actual function behavior
        try:
            result = get_r_multiple_distribution(df_no_r)
        except (ValueError, KeyError):
            pass  # Expected if function requires r_multiple column


# Integration test example
@pytest.mark.integration
def test_full_analytics_pipeline(sample_trades_df):
    """Test complete analytics workflow"""
    starting_capital = 10000.0

    # Calculate metrics
    metrics = calculate_all_metrics(sample_trades_df)

    # Generate equity curve
    equity_df = get_equity_curve(sample_trades_df, starting_capital)

    # Get time analysis
    time_perf = get_time_of_day_performance(sample_trades_df)

    # All should complete without errors
    assert metrics is not None
    assert equity_df is not None
    assert time_perf is not None
