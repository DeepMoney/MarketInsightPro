import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats

def calculate_all_metrics(trades_df, starting_capital=50000):
    """
    Calculate all 16 performance metrics for a set of trades
    
    Parameters:
    - trades_df: DataFrame with trade data
    - starting_capital: initial capital
    
    Returns:
    - Dictionary with all 16 metrics
    """
    # Convert Decimal to float for arithmetic operations
    starting_capital = float(starting_capital) if starting_capital is not None else 50000
    
    if trades_df.empty:
        return get_empty_metrics()
    
    trades = trades_df.copy()
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    
    total_trades = len(trades)
    winning_trades = trades[trades['pnl'] > 0]
    losing_trades = trades[trades['pnl'] < 0]
    
    num_wins = len(winning_trades)
    num_losses = len(losing_trades)
    
    total_pnl = trades['pnl'].sum()
    
    win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0
    
    gross_profit = winning_trades['pnl'].sum() if num_wins > 0 else 0
    gross_loss = abs(losing_trades['pnl'].sum()) if num_losses > 0 else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
    
    avg_win = winning_trades['pnl'].mean() if num_wins > 0 else 0
    avg_loss = losing_trades['pnl'].mean() if num_losses > 0 else 0
    
    avg_pnl = trades['pnl'].mean() if total_trades > 0 else 0
    win_prob = win_rate / 100
    loss_prob = 1 - win_prob
    expectancy_dollar = (win_prob * avg_win) + (loss_prob * avg_loss) if total_trades > 0 else 0
    
    avg_r = trades['r_multiple'].mean() if total_trades > 0 and 'r_multiple' in trades.columns else 0
    expectancy_r = avg_r
    
    risk_of_ruin = calculate_risk_of_ruin(win_prob, avg_win, abs(avg_loss), starting_capital)
    
    trades_sorted = trades.sort_values('exit_time')
    # Convert pnl to float before cumsum to avoid Decimal issues
    trades_sorted['pnl'] = trades_sorted['pnl'].astype(float)
    trades_sorted['cumulative_pnl'] = trades_sorted['pnl'].cumsum()
    trades_sorted['equity'] = starting_capital + trades_sorted['cumulative_pnl']
    
    high_water_mark = trades_sorted['equity'].expanding().max()
    drawdown = trades_sorted['equity'] - high_water_mark
    max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
    max_drawdown_pct = (max_drawdown / starting_capital * 100) if starting_capital > 0 else 0
    
    hwm = high_water_mark.max() if len(high_water_mark) > 0 else starting_capital
    
    recovery_factor = (total_pnl / max_drawdown) if max_drawdown > 0 else 0
    
    returns = trades_sorted['pnl'] / starting_capital
    sharpe_ratio = calculate_sharpe_ratio(returns)
    
    win_streak, loss_streak = calculate_streaks(trades)
    
    avg_win_duration = winning_trades['holding_minutes'].mean() if num_wins > 0 else 0
    avg_loss_duration = losing_trades['holding_minutes'].mean() if num_losses > 0 else 0
    
    trade_quality_score = calculate_trade_quality_score(sharpe_ratio, expectancy_r, profit_factor)
    
    trades_sorted['date'] = trades_sorted['exit_time'].dt.date
    trades_per_day = trades_sorted.groupby('date').size().mean()
    
    drawdown_duration = calculate_drawdown_duration(trades_sorted, high_water_mark)
    
    metrics = {
        'total_pnl': round(total_pnl, 2),
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'expectancy_dollar': round(expectancy_dollar, 2),
        'expectancy_r': round(expectancy_r, 2),
        'risk_of_ruin': round(risk_of_ruin, 2),
        'recovery_factor': round(recovery_factor, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'avg_win_duration': round(avg_win_duration, 2),
        'avg_loss_duration': round(avg_loss_duration, 2),
        'max_drawdown': round(max_drawdown, 2),
        'max_drawdown_pct': round(max_drawdown_pct, 2),
        'high_water_mark': round(hwm, 2),
        'win_streak': win_streak,
        'loss_streak': loss_streak,
        'trade_quality_score': round(trade_quality_score, 2),
        'trades_per_day': round(trades_per_day, 2),
        'total_trades': total_trades,
        'num_wins': num_wins,
        'num_losses': num_losses,
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'drawdown_duration_days': drawdown_duration
    }
    
    return metrics


def calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
    """Calculate Sharpe Ratio"""
    if len(returns) < 2:
        return 0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    if excess_returns.std() == 0:
        return 0
    
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)
    return sharpe


def calculate_risk_of_ruin(win_prob, avg_win, avg_loss, capital):
    """
    Calculate Risk of Ruin using Kelly Criterion and drawdown probability
    Simplified formula based on win probability and payoff ratio
    """
    # Convert Decimal to float for arithmetic operations
    win_prob = float(win_prob) if win_prob is not None else 0
    avg_win = float(avg_win) if avg_win is not None else 0
    avg_loss = float(avg_loss) if avg_loss is not None else 0
    capital = float(capital) if capital is not None else 0
    
    if avg_loss == 0 or win_prob == 0:
        return 0
    
    payoff_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    
    if payoff_ratio == 0:
        return 100.0
    
    if win_prob >= 1:
        return 0
    
    q = 1 - win_prob
    
    if payoff_ratio == 1:
        ror = (q / win_prob) ** (capital / avg_loss) if win_prob > 0 else 100
    else:
        ror = ((q / win_prob) * payoff_ratio) ** (capital / avg_loss)
    
    ror_pct = min(ror * 100, 100)
    
    return ror_pct


def calculate_streaks(trades_df):
    """Calculate maximum consecutive wins and losses"""
    if trades_df.empty:
        return 0, 0
    
    trades = trades_df.sort_values('exit_time').copy()
    trades['is_win'] = trades['pnl'] > 0
    
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for is_win in trades['is_win']:
        if is_win:
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
    
    return max_win_streak, max_loss_streak


def calculate_trade_quality_score(sharpe, expectancy_r, profit_factor):
    """
    Calculate Trade Quality Score as a composite metric
    Combines Sharpe ratio, expectancy, and profit factor
    Score range: 0-100
    """
    sharpe_component = min(sharpe / 3 * 33.33, 33.33) if sharpe > 0 else 0
    
    expectancy_component = min(expectancy_r / 2 * 33.33, 33.33) if expectancy_r > 0 else 0
    
    profit_factor_component = min((profit_factor - 1) / 2 * 33.33, 33.33) if profit_factor > 1 else 0
    
    quality_score = sharpe_component + expectancy_component + profit_factor_component
    
    return quality_score


def calculate_drawdown_duration(trades_df, high_water_mark):
    """Calculate the longest drawdown duration in days"""
    if trades_df.empty:
        return 0
    
    trades = trades_df.copy()
    trades['is_underwater'] = trades['equity'] < high_water_mark
    
    max_duration = 0
    current_duration = 0
    prev_date = None
    
    for idx, row in trades.iterrows():
        if row['is_underwater']:
            if prev_date is None:
                current_duration = 1
            else:
                days_diff = (row['exit_time'].date() - prev_date).days
                current_duration += max(days_diff, 1)
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0
        
        prev_date = row['exit_time'].date()
    
    return max_duration


def get_empty_metrics():
    """Return empty metrics dictionary"""
    return {
        'total_pnl': 0,
        'win_rate': 0,
        'profit_factor': 0,
        'sharpe_ratio': 0,
        'expectancy_dollar': 0,
        'expectancy_r': 0,
        'risk_of_ruin': 0,
        'recovery_factor': 0,
        'avg_win': 0,
        'avg_loss': 0,
        'avg_win_duration': 0,
        'avg_loss_duration': 0,
        'max_drawdown': 0,
        'max_drawdown_pct': 0,
        'high_water_mark': 0,
        'win_streak': 0,
        'loss_streak': 0,
        'trade_quality_score': 0,
        'trades_per_day': 0,
        'total_trades': 0,
        'num_wins': 0,
        'num_losses': 0,
        'gross_profit': 0,
        'gross_loss': 0,
        'drawdown_duration_days': 0
    }


def get_equity_curve(trades_df, starting_capital=50000):
    """
    Generate equity curve data with drawdown information
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    trades = trades_df.sort_values('exit_time').copy()
    trades['cumulative_pnl'] = trades['pnl'].cumsum()
    trades['equity'] = starting_capital + trades['cumulative_pnl']
    trades['high_water_mark'] = trades['equity'].expanding().max()
    trades['drawdown'] = trades['equity'] - trades['high_water_mark']
    trades['drawdown_pct'] = (trades['drawdown'] / trades['high_water_mark'] * 100)
    
    return trades[['exit_time', 'equity', 'high_water_mark', 'drawdown', 'drawdown_pct']]


def get_time_of_day_performance(trades_df):
    """
    Calculate performance by hour of day
    Returns DataFrame with hour and avg PnL
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    trades = trades_df.copy()
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    trades['hour'] = trades['entry_time'].dt.hour
    
    hour_perf = trades.groupby('hour').agg({
        'pnl': ['mean', 'sum', 'count'],
        'outcome': lambda x: (x == 'Win').sum() / len(x) * 100 if len(x) > 0 else 0
    }).reset_index()
    
    hour_perf.columns = ['hour', 'avg_pnl', 'total_pnl', 'num_trades', 'win_rate']
    
    return hour_perf


def get_r_multiple_distribution(trades_df):
    """
    Get R-multiple distribution for histogram
    """
    if trades_df.empty or 'r_multiple' not in trades_df.columns:
        return pd.DataFrame()
    
    return trades_df[['r_multiple']].copy()


def get_weekly_pnl_heatmap_data(trades_df):
    """
    Prepare data for weekly PnL heatmap
    Returns DataFrame with week, weekday, and PnL
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    trades = trades_df.copy()
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades['date'] = trades['exit_time'].dt.date
    trades['week'] = trades['exit_time'].dt.isocalendar().week
    trades['year'] = trades['exit_time'].dt.year
    trades['weekday'] = trades['exit_time'].dt.day_name()
    
    daily_pnl = trades.groupby(['year', 'week', 'weekday', 'date'])['pnl'].sum().reset_index()
    
    return daily_pnl


def get_monthly_returns(trades_df):
    """
    Calculate monthly returns grid
    Returns DataFrame with year, month, and returns
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    trades = trades_df.copy()
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades['year'] = trades['exit_time'].dt.year
    trades['month'] = trades['exit_time'].dt.month
    trades['month_name'] = trades['exit_time'].dt.strftime('%b')
    
    monthly = trades.groupby(['year', 'month', 'month_name'])['pnl'].sum().reset_index()
    monthly.columns = ['year', 'month', 'month_name', 'returns']
    
    return monthly
