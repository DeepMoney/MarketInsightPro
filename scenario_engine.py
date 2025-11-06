import pandas as pd
import numpy as np
from analytics_engine import calculate_all_metrics

def apply_scenario(trades_df, market_df, scenario_params, starting_capital=50000):
    """
    Apply what-if scenario parameters to trades and recalculate PnL and metrics
    
    Parameters:
    - trades_df: Original trade data
    - market_df: Market OHLCV data (combined for all instruments)
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
    
    market_df = market_df.copy()
    market_df['timestamp'] = pd.to_datetime(market_df['timestamp'])
    
    stop_loss_pct = scenario_params.get('stop_loss_pct', None)
    take_profit_pct = scenario_params.get('take_profit_pct', None)
    min_hold_minutes = scenario_params.get('min_hold_minutes', None)
    max_hold_minutes = scenario_params.get('max_hold_minutes', None)
    exclude_days = scenario_params.get('exclude_days', [])
    capital_allocation_pct = scenario_params.get('capital_allocation_pct', 40)
    mes_split_pct = scenario_params.get('mes_split_pct', 50)
    trade_hours_start = scenario_params.get('trade_hours_start', None)
    trade_hours_end = scenario_params.get('trade_hours_end', None)
    slippage_ticks = scenario_params.get('slippage_ticks', 0)
    commission_per_contract = scenario_params.get('commission_per_contract', 0)
    
    mnq_split_pct = 100 - mes_split_pct
    
    filtered_trades = []
    
    for idx, trade in trades.iterrows():
        weekday = trade['entry_time'].strftime('%A')
        if weekday in exclude_days:
            continue
        
        entry_hour = trade['entry_time'].hour
        entry_minute = trade['entry_time'].minute
        entry_time_decimal = entry_hour + entry_minute / 60.0
        
        if trade_hours_start is not None and trade_hours_end is not None:
            if trade_hours_start < trade_hours_end:
                if not (trade_hours_start <= entry_time_decimal <= trade_hours_end):
                    continue
            else:
                if not (entry_time_decimal >= trade_hours_start or entry_time_decimal <= trade_hours_end):
                    continue
        
        holding_minutes = trade['holding_minutes']
        if min_hold_minutes is not None and holding_minutes < min_hold_minutes:
            continue
        
        modified_trade = trade.copy()
        
        instrument = trade['instrument']
        direction = trade['direction']
        entry_price = trade['entry_price']
        entry_time = trade['entry_time']
        original_exit_time = trade['exit_time']
        point_value = 5 if instrument == 'MES' else 2
        
        allocation_for_instrument = (mes_split_pct / 100) if instrument == 'MES' else (mnq_split_pct / 100)
        capital_for_trade = starting_capital * (capital_allocation_pct / 100) * allocation_for_instrument
        
        margin_requirement = 1000 if instrument == 'MES' else 1500
        contracts = max(1, int(capital_for_trade / margin_requirement))
        modified_trade['contracts'] = contracts
        
        forced_exit_time = original_exit_time
        if max_hold_minutes is not None and holding_minutes > max_hold_minutes:
            forced_exit_time = entry_time + pd.Timedelta(minutes=max_hold_minutes)
            modified_trade['holding_minutes'] = max_hold_minutes
        
        stop_price = None
        target_price = None
        
        if stop_loss_pct is not None:
            if direction == 'Long':
                stop_price = entry_price * (1 - stop_loss_pct / 100)
            else:
                stop_price = entry_price * (1 + stop_loss_pct / 100)
        
        if take_profit_pct is not None:
            if direction == 'Long':
                target_price = entry_price * (1 + take_profit_pct / 100)
            else:
                target_price = entry_price * (1 - take_profit_pct / 100)
        
        original_exit_price = trade['exit_price']
        
        exit_result = simulate_trade_exit(
            market_df, instrument, entry_time, forced_exit_time, entry_price,
            direction, stop_price, target_price, original_exit_time, original_exit_price
        )
        
        exit_price = exit_result['exit_price']
        exit_time = exit_result['exit_time']
        exit_reason = exit_result['exit_reason']
        
        tick_size = 0.25 if instrument == 'MES' else 0.25
        
        effective_entry_price = entry_price
        effective_exit_price = exit_price
        
        if slippage_ticks > 0:
            slippage_amount = slippage_ticks * tick_size
            if direction == 'Long':
                effective_entry_price = entry_price + slippage_amount
                effective_exit_price = exit_price - slippage_amount
            else:
                effective_entry_price = entry_price - slippage_amount
                effective_exit_price = exit_price + slippage_amount
        
        if direction == 'Long':
            new_pnl = (effective_exit_price - effective_entry_price) * point_value * contracts
        else:
            new_pnl = (effective_entry_price - effective_exit_price) * point_value * contracts
        
        total_commission = commission_per_contract * contracts
        new_pnl -= total_commission
        
        modified_trade['exit_time'] = exit_time
        modified_trade['exit_price'] = exit_price
        modified_trade['pnl'] = round(new_pnl, 2)
        modified_trade['outcome'] = 'Win' if new_pnl > 0 else ('Loss' if new_pnl < 0 else 'Breakeven')
        modified_trade['exit_reason'] = exit_reason
        if slippage_ticks > 0 or commission_per_contract > 0:
            modified_trade['slippage_cost'] = round((effective_entry_price - entry_price) * point_value * contracts + (exit_price - effective_exit_price) * point_value * contracts if direction == 'Long' else (entry_price - effective_entry_price) * point_value * contracts + (effective_exit_price - exit_price) * point_value * contracts, 2)
            modified_trade['commission_cost'] = round(total_commission, 2)
        
        actual_holding = (exit_time - entry_time).total_seconds() / 60
        modified_trade['holding_minutes'] = round(actual_holding, 2)
        
        initial_risk = trade.get('initial_risk', abs(new_pnl * 0.5))
        r_multiple = (new_pnl / abs(initial_risk)) if initial_risk != 0 else 0
        modified_trade['r_multiple'] = round(r_multiple, 2)
        
        filtered_trades.append(modified_trade)
    
    modified_trades_df = pd.DataFrame(filtered_trades)
    
    metrics = calculate_all_metrics(modified_trades_df, starting_capital)
    
    return modified_trades_df, metrics


def simulate_trade_exit(market_df, instrument, entry_time, max_exit_time, entry_price, 
                        direction, stop_price=None, target_price=None, original_exit_time=None,
                        original_exit_price=None):
    """
    Simulate trade exit by walking through candles and checking high/low for stop-loss and take-profit triggers
    
    Parameters:
    - market_df: Market OHLCV data (must have 'timestamp' column already converted to datetime)
    - instrument: 'MES' or 'MNQ'
    - entry_time: Trade entry timestamp
    - max_exit_time: Maximum exit time (original exit or forced by max hold)
    - entry_price: Entry price
    - direction: 'Long' or 'Short'
    - stop_price: Stop loss price (None if not set)
    - target_price: Take profit price (None if not set)
    - original_exit_time: Original exit time (to distinguish from max hold)
    - original_exit_price: Original exit price (used when no triggers are hit)
    
    Returns:
    - Dictionary with exit_price, exit_time, and exit_reason
    """
    
    if market_df.empty:
        return {
            'exit_price': original_exit_price if original_exit_price is not None else entry_price,
            'exit_time': max_exit_time,
            'exit_reason': 'No Market Data'
        }
    
    instrument_market = market_df[market_df['instrument'] == instrument] if 'instrument' in market_df.columns else market_df
    
    trade_candles = instrument_market[
        (instrument_market['timestamp'] >= entry_time) & 
        (instrument_market['timestamp'] <= max_exit_time)
    ].sort_values('timestamp')
    
    if trade_candles.empty:
        return {
            'exit_price': original_exit_price if original_exit_price is not None else entry_price,
            'exit_time': max_exit_time,
            'exit_reason': 'No Candles Found'
        }
    
    for idx, candle in trade_candles.iterrows():
        candle_time = candle['timestamp']
        candle_high = candle['high']
        candle_low = candle['low']
        candle_close = candle['close']
        
        if direction == 'Long':
            if stop_price is not None and candle_low <= stop_price:
                return {
                    'exit_price': stop_price,
                    'exit_time': candle_time,
                    'exit_reason': 'Stop Loss'
                }
            
            if target_price is not None and candle_high >= target_price:
                return {
                    'exit_price': target_price,
                    'exit_time': candle_time,
                    'exit_reason': 'Take Profit'
                }
        
        else:
            if stop_price is not None and candle_high >= stop_price:
                return {
                    'exit_price': stop_price,
                    'exit_time': candle_time,
                    'exit_reason': 'Stop Loss'
                }
            
            if target_price is not None and candle_low <= target_price:
                return {
                    'exit_price': target_price,
                    'exit_time': candle_time,
                    'exit_reason': 'Take Profit'
                }
    
    is_max_hold_exit = original_exit_time is not None and max_exit_time < original_exit_time
    
    if is_max_hold_exit:
        last_candle = trade_candles.iloc[-1]
        exit_price = last_candle['close']
        exit_time = last_candle['timestamp']
        exit_reason = 'Max Hold Time'
    else:
        exit_price = original_exit_price if original_exit_price is not None else trade_candles.iloc[-1]['close']
        exit_time = original_exit_time if original_exit_time is not None else trade_candles.iloc[-1]['timestamp']
        exit_reason = 'Original Exit'
    
    return {
        'exit_price': exit_price,
        'exit_time': exit_time,
        'exit_reason': exit_reason
    }


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
            'mes_split_pct': 50,
            'trade_hours_start': None,
            'trade_hours_end': None,
            'slippage_ticks': 0,
            'commission_per_contract': 0
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
            'trade_quality_score', 'trades_per_day', 'total_trades'
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
    if params.get('trade_hours_start') is not None and params.get('trade_hours_end') is not None:
        param_summary.append(f"Hours: {int(params['trade_hours_start'])}-{int(params['trade_hours_end'])}")
    if params.get('slippage_ticks', 0) > 0:
        param_summary.append(f"Slippage: {params['slippage_ticks']} ticks")
    if params.get('commission_per_contract', 0) > 0:
        param_summary.append(f"Commission: ${params['commission_per_contract']}/contract")
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
