import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_market_data(instrument, start_date, end_date, base_price, volatility=0.02):
    """
    Generate 15-minute OHLCV candlestick data for futures instruments
    
    Parameters:
    - instrument: 'MES' or 'MNQ'
    - start_date: datetime object
    - end_date: datetime object
    - base_price: starting price for the instrument
    - volatility: daily volatility as decimal
    """
    
    timestamps = []
    current = start_date
    
    while current <= end_date:
        if current.weekday() < 5:
            trading_start = current.replace(hour=9, minute=30, second=0, microsecond=0)
            trading_end = current.replace(hour=16, minute=0, second=0, microsecond=0)
            
            time = trading_start
            while time <= trading_end:
                timestamps.append(time)
                time += timedelta(minutes=15)
        
        current += timedelta(days=1)
    
    data = []
    price = base_price
    
    for ts in timestamps:
        price_change = np.random.normal(0, volatility * price / np.sqrt(26 * 4))
        price = price + price_change
        
        high_offset = abs(np.random.normal(0, volatility * price * 0.3))
        low_offset = abs(np.random.normal(0, volatility * price * 0.3))
        
        open_price = price + np.random.normal(0, volatility * price * 0.1)
        close_price = price + np.random.normal(0, volatility * price * 0.1)
        high_price = max(open_price, close_price) + high_offset
        low_price = min(open_price, close_price) - low_offset
        
        volume = int(np.random.lognormal(10, 1))
        
        data.append({
            'instrument': instrument,
            'timestamp': ts,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    return df


def calculate_r_multiple(pnl, initial_risk):
    """Calculate R-multiple for a trade (PnL / Initial Risk)"""
    if initial_risk == 0 or pd.isna(initial_risk):
        return 0
    return round(pnl / abs(initial_risk), 2)


def generate_trade_data(instrument, market_df, trades_per_day_range=(2, 3), starting_capital=50000, allocation_pct=0.4):
    """
    Generate realistic trade data with long/short positions, R-multiples, and time analysis
    
    Parameters:
    - instrument: 'MES' or 'MNQ'
    - market_df: DataFrame with market OHLCV data
    - trades_per_day_range: tuple of (min, max) trades per day
    - starting_capital: initial capital
    - allocation_pct: percentage of capital to allocate
    """
    
    market_df['date'] = pd.to_datetime(market_df['timestamp']).dt.date
    unique_dates = market_df['date'].unique()
    
    trades = []
    trade_id = 1
    
    point_value = 5 if instrument == 'MES' else 2
    margin_requirement = 1000 if instrument == 'MES' else 1500
    
    for date in unique_dates:
        num_trades = random.randint(*trades_per_day_range)
        
        day_data = market_df[market_df['date'] == date].reset_index(drop=True)
        
        if len(day_data) < 10:
            continue
        
        for _ in range(num_trades):
            entry_idx = random.randint(0, len(day_data) - 5)
            exit_idx = random.randint(entry_idx + 1, min(entry_idx + 20, len(day_data) - 1))
            
            entry_row = day_data.iloc[entry_idx]
            exit_row = day_data.iloc[exit_idx]
            
            direction = random.choice(['Long', 'Short'])
            
            entry_price = round(entry_row['open'] + random.uniform(-0.5, 0.5), 2)
            exit_price = round(exit_row['close'] + random.uniform(-0.5, 0.5), 2)
            
            contracts = max(1, int((starting_capital * allocation_pct) / margin_requirement))
            
            stop_loss_pct = random.uniform(0.01, 0.03)
            if direction == 'Long':
                stop_price = entry_price * (1 - stop_loss_pct)
                initial_risk = (entry_price - stop_price) * point_value * contracts
            else:
                stop_price = entry_price * (1 + stop_loss_pct)
                initial_risk = (stop_price - entry_price) * point_value * contracts
            
            if direction == 'Long':
                pnl = (exit_price - entry_price) * point_value * contracts
            else:
                pnl = (entry_price - exit_price) * point_value * contracts
            
            pnl = round(pnl + random.uniform(-20, 20), 2)
            
            r_multiple = calculate_r_multiple(pnl, initial_risk)
            
            holding_minutes = (exit_idx - entry_idx) * 15
            
            entry_hour = entry_row['timestamp'].hour
            exit_hour = exit_row['timestamp'].hour
            
            outcome = 'Win' if pnl > 0 else ('Loss' if pnl < 0 else 'Breakeven')
            
            trades.append({
                'trade_id': f"{instrument}_{trade_id}",
                'instrument': instrument,
                'direction': direction,
                'entry_time': entry_row['timestamp'],
                'exit_time': exit_row['timestamp'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'contracts': contracts,
                'pnl': pnl,
                'initial_risk': round(initial_risk, 2),
                'r_multiple': r_multiple,
                'holding_minutes': holding_minutes,
                'entry_hour': entry_hour,
                'exit_hour': exit_hour,
                'outcome': outcome,
                'stop_price': round(stop_price, 2)
            })
            
            trade_id += 1
    
    return pd.DataFrame(trades)


def create_mock_data():
    """
    Create mock market and trade data for MES and MNQ from July 2024 to November 2025
    Returns a dictionary with market and trade DataFrames
    """
    start_date = datetime(2024, 7, 1)
    end_date = datetime(2025, 11, 6)
    
    print("Generating MES market data...")
    mes_market = generate_market_data('MES', start_date, end_date, base_price=5500, volatility=0.015)
    
    print("Generating MNQ market data...")
    mnq_market = generate_market_data('MNQ', start_date, end_date, base_price=19500, volatility=0.02)
    
    print("Generating MES trades...")
    mes_trades = generate_trade_data('MES', mes_market, trades_per_day_range=(2, 3))
    
    print("Generating MNQ trades...")
    mnq_trades = generate_trade_data('MNQ', mnq_market, trades_per_day_range=(2, 3))
    
    print(f"Generated {len(mes_market)} MES candles and {len(mes_trades)} MES trades")
    print(f"Generated {len(mnq_market)} MNQ candles and {len(mnq_trades)} MNQ trades")
    
    return {
        'MES_market': mes_market,
        'MNQ_market': mnq_market,
        'MES_trades': mes_trades,
        'MNQ_trades': mnq_trades
    }


if __name__ == "__main__":
    data = create_mock_data()
    
    data['MES_market'].to_csv('MES-2024-2025.csv', index=False)
    data['MNQ_market'].to_csv('MNQ-2024-2025.csv', index=False)
    data['MES_trades'].to_csv('MES-2024-2025-trades.csv', index=False)
    data['MNQ_trades'].to_csv('MNQ-2024-2025-trades.csv', index=False)
    
    print("\nMock data files created successfully!")
