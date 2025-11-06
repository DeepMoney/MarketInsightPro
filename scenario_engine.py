import pandas as pd
import numpy as np
from analytics_engine import calculate_all_metrics

def apply_scenario(trades_df, market_df, scenario_params, starting_capital=50000):
    """
    Apply what-if scenario parameters to trades and recalculate PnL and metrics
    
    Parameters:
    - trades_df: Original trade data
    - market_df: Market OHLCV data
    - scenario_params: Dictionary with scenario parameters
    - starting_capital: Initial capital
    
    Returns:
    - Modified trades DataFrame and metrics dictionary
    """
    
    if trades_df.empty:
        return trades_df.copy(), calculate_all_metrics(pd.DataFrame(), starting_capital)
    
    trades = trades_df.copy()
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    
    stop_loss_pct = scenario_params.get('stop_loss_pct', None)
    take_profit_pct = scenario_params.get('take_profit_pct', None)
    min_hold_minutes = scenario_params.get('min_hold_minutes', None)
    max_hold_minutes = scenario_params.get('max_hold_minutes', None)
    exclude_days = scenario_params.get('exclude_days', [])
    capital_allocation_pct = scenario_params.get('capital_allocation_pct', 40)
    mes_split_pct = scenario_params.get('mes_split_pct', 50)
    
    mnq_split_pct = 100 - mes_split_pct
    
    filtered_trades = []
    
    for idx, trade in trades.iterrows():
        weekday = trade['entry_time'].strftime('%A')
        if weekday in exclude_days:
            continue
        
        modified_trade = trade.copy()
        
        instrument = trade['instrument']
        direction = trade['direction']
        entry_price = trade['entry_price']
        original_exit_price = trade['exit_price']
        point_value = 5 if instrument == 'MES' else 2
        
        allocation_for_instrument = (mes_split_pct / 100) if instrument == 'MES' else (mnq_split_pct / 100)
        capital_for_trade = starting_capital * (capital_allocation_pct / 100) * allocation_for_instrument
        
        margin_requirement = 1000 if instrument == 'MES' else 1500
        contracts = max(1, int(capital_for_trade / margin_requirement))
        
        modified_trade['contracts'] = contracts
        
        exit_price = original_exit_price
        exit_reason = 'Original'
        
        if stop_loss_pct is not None:
            if direction == 'Long':
                stop_price = entry_price * (1 - stop_loss_pct / 100)
                if original_exit_price <= stop_price:
                    exit_price = stop_price
                    exit_reason = 'Stop Loss'
            else:
                stop_price = entry_price * (1 + stop_loss_pct / 100)
                if original_exit_price >= stop_price:
                    exit_price = stop_price
                    exit_reason = 'Stop Loss'
        
        if take_profit_pct is not None:
            if direction == 'Long':
                target_price = entry_price * (1 + take_profit_pct / 100)
                if original_exit_price >= target_price:
                    exit_price = target_price
                    exit_reason = 'Take Profit'
            else:
                target_price = entry_price * (1 - take_profit_pct / 100)
                if original_exit_price <= target_price:
                    exit_price = target_price
                    exit_reason = 'Take Profit'
        
        holding_minutes = trade['holding_minutes']
        
        if min_hold_minutes is not None and holding_minutes < min_hold_minutes:
            continue
        
        if max_hold_minutes is not None and holding_minutes > max_hold_minutes:
            time_delta = pd.Timedelta(minutes=max_hold_minutes)
            new_exit_time = trade['entry_time'] + time_delta
            
            exit_price = simulate_exit_price_at_time(
                market_df, instrument, trade['entry_time'], new_exit_time, original_exit_price
            )
            
            modified_trade['exit_time'] = new_exit_time
            modified_trade['holding_minutes'] = max_hold_minutes
            exit_reason = 'Max Hold Time'
        
        if direction == 'Long':
            new_pnl = (exit_price - entry_price) * point_value * contracts
        else:
            new_pnl = (entry_price - exit_price) * point_value * contracts
        
        modified_trade['exit_price'] = exit_price
        modified_trade['pnl'] = round(new_pnl, 2)
        modified_trade['outcome'] = 'Win' if new_pnl > 0 else ('Loss' if new_pnl < 0 else 'Breakeven')
        modified_trade['exit_reason'] = exit_reason
        
        initial_risk = trade.get('initial_risk', abs(new_pnl * 0.5))
        r_multiple = (new_pnl / abs(initial_risk)) if initial_risk != 0 else 0
        modified_trade['r_multiple'] = round(r_multiple, 2)
        
        filtered_trades.append(modified_trade)
    
    modified_trades_df = pd.DataFrame(filtered_trades)
    
    metrics = calculate_all_metrics(modified_trades_df, starting_capital)
    
    return modified_trades_df, metrics


def simulate_exit_price_at_time(market_df, instrument, entry_time, exit_time, original_exit_price):
    """
    Simulate what the exit price would be at a specific time using market data
    Falls back to original exit price if market data not available
    """
    if market_df.empty:
        return original_exit_price
    
    market_df['timestamp'] = pd.to_datetime(market_df['timestamp'])
    
    matching_candles = market_df[
        (market_df['timestamp'] >= entry_time) & 
        (market_df['timestamp'] <= exit_time)
    ]
    
    if matching_candles.empty:
        return original_exit_price
    
    last_candle = matching_candles.iloc[-1]
    return last_candle['close']


def create_baseline_scenario(trades_df, starting_capital=50000):
    """
    Create baseline (actual) scenario with original trades
    """
    metrics = calculate_all_metrics(trades_df, starting_capital)
    
    return {
        'name': 'Baseline (Actual)',
        'params': {
            'stop_loss_pct': None,
            'take_profit_pct': None,
            'min_hold_minutes': None,
            'max_hold_minutes': None,
            'exclude_days': [],
            'capital_allocation_pct': 40,
            'mes_split_pct': 50
        },
        'trades': trades_df,
        'metrics': metrics,
        'is_baseline': True
    }


def create_scenario(name, params, trades_df, market_df, starting_capital=50000):
    """
    Create a new what-if scenario
    """
    modified_trades, metrics = apply_scenario(trades_df, market_df, params, starting_capital)
    
    return {
        'name': name,
        'params': params,
        'trades': modified_trades,
        'metrics': metrics,
        'is_baseline': False
    }


def get_comparison_matrix(scenarios, metric_keys=None):
    """
    Create comparison matrix DataFrame from multiple scenarios
    
    Parameters:
    - scenarios: List of scenario dictionaries
    - metric_keys: List of metric keys to include (None = all)
    
    Returns:
    - DataFrame with scenarios as rows and metrics as columns
    """
    
    if not scenarios:
        return pd.DataFrame()
    
    if metric_keys is None:
        metric_keys = [
            'total_pnl', 'win_rate', 'sharpe_ratio', 'profit_factor', 
            'expectancy_dollar', 'expectancy_r', 'risk_of_ruin', 'recovery_factor',
            'avg_win', 'avg_loss', 'avg_win_duration', 'avg_loss_duration',
            'max_drawdown', 'high_water_mark', 'win_streak', 'loss_streak',
            'trade_quality_score', 'trades_per_day'
        ]
    
    comparison_data = []
    
    for scenario in scenarios:
        row = {
            'scenario_name': scenario['name'],
            'is_baseline': scenario.get('is_baseline', False)
        }
        
        for key in metric_keys:
            row[key] = scenario['metrics'].get(key, 0)
        
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    
    if len(df) > 1:
        baseline_idx = df[df['is_baseline'] == True].index
        if len(baseline_idx) > 0:
            baseline_row = df.loc[baseline_idx[0]]
            
            for key in metric_keys:
                if key in df.columns:
                    df[f'{key}_delta'] = df[key] - baseline_row[key]
                    if baseline_row[key] != 0:
                        df[f'{key}_delta_pct'] = (df[f'{key}_delta'] / abs(baseline_row[key])) * 100
                    else:
                        df[f'{key}_delta_pct'] = 0
    
    return df


def get_scenario_summary(scenario):
    """
    Get a summary of scenario parameters and key metrics
    """
    params = scenario['params']
    metrics = scenario['metrics']
    
    param_summary = []
    if params.get('stop_loss_pct') is not None:
        param_summary.append(f"Stop Loss: {params['stop_loss_pct']}%")
    if params.get('take_profit_pct') is not None:
        param_summary.append(f"Take Profit: {params['take_profit_pct']}%")
    if params.get('min_hold_minutes') is not None:
        param_summary.append(f"Min Hold: {params['min_hold_minutes']} min")
    if params.get('max_hold_minutes') is not None:
        param_summary.append(f"Max Hold: {params['max_hold_minutes']} min")
    if params.get('exclude_days'):
        param_summary.append(f"Exclude: {', '.join(params['exclude_days'])}")
    if params.get('capital_allocation_pct') != 40:
        param_summary.append(f"Capital: {params['capital_allocation_pct']}%")
    if params.get('mes_split_pct') != 50:
        param_summary.append(f"MES/MNQ: {params['mes_split_pct']}/{100-params['mes_split_pct']}")
    
    return {
        'name': scenario['name'],
        'parameters': ', '.join(param_summary) if param_summary else 'Baseline',
        'total_pnl': metrics['total_pnl'],
        'win_rate': metrics['win_rate'],
        'sharpe_ratio': metrics['sharpe_ratio'],
        'total_trades': metrics['total_trades']
    }
