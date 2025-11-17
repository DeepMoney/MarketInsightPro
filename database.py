"""
Database Layer for Trading Analysis Application
Handles all PostgreSQL operations for machines, scenarios, market data, and trades
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import pandas as pd
import json
from datetime import datetime

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.environ.get('PGHOST'),
        port=os.environ.get('PGPORT'),
        database=os.environ.get('PGDATABASE'),
        user=os.environ.get('PGUSER'),
        password=os.environ.get('PGPASSWORD')
    )

def _normalize_numeric_columns(df, numeric_cols):
    """
    Convert Decimal columns to float to avoid type errors in arithmetic operations.
    PostgreSQL DECIMAL columns come as decimal.Decimal objects via psycopg2.
    """
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def init_database():
    """Initialize database schema"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Market Data Table (shared across machines)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                instrument VARCHAR(10) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open DECIMAL(10, 2) NOT NULL,
                high DECIMAL(10, 2) NOT NULL,
                low DECIMAL(10, 2) NOT NULL,
                close DECIMAL(10, 2) NOT NULL,
                volume BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(instrument, timeframe, timestamp)
            )
        """)
        
        # Create index for fast queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_lookup 
            ON market_data(instrument, timeframe, timestamp)
        """)
        
        # Machines Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                starting_capital DECIMAL(12, 2) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('live', 'simulated')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trades Table (per machine)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
                trade_id VARCHAR(50) NOT NULL,
                instrument VARCHAR(10) NOT NULL,
                direction VARCHAR(10) NOT NULL CHECK (direction IN ('Long', 'Short')),
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                entry_price DECIMAL(10, 2) NOT NULL,
                exit_price DECIMAL(10, 2) NOT NULL,
                contracts INTEGER NOT NULL,
                pnl DECIMAL(12, 2) NOT NULL,
                initial_risk DECIMAL(12, 2),
                r_multiple DECIMAL(10, 2),
                holding_minutes DECIMAL(10, 2),
                entry_hour INTEGER,
                exit_hour INTEGER,
                outcome VARCHAR(20),
                stop_price DECIMAL(10, 2),
                timeframe VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(machine_id, trade_id)
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_machine 
            ON trades(machine_id)
        """)
        
        # Scenarios Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id SERIAL PRIMARY KEY,
                machine_id UUID NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                is_baseline BOOLEAN DEFAULT FALSE,
                parameters JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(machine_id, name)
            )
        """)
        
        # Scenario Results Table (caches computed metrics)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scenario_results (
                id SERIAL PRIMARY KEY,
                scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
                metrics JSONB NOT NULL,
                modified_trades JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(scenario_id)
            )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# ========== Machine CRUD Operations ==========

def create_machine_db(machine_id, name, starting_capital, timeframe, status):
    """Create a new machine in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO machines (id, name, starting_capital, timeframe, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (machine_id, name, starting_capital, timeframe, status))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_all_machines():
    """Get all machines"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, name, starting_capital, timeframe, status, created_at
            FROM machines
            ORDER BY created_at DESC
        """)
        machines = cur.fetchall()
        return [dict(m) for m in machines]
    finally:
        cur.close()
        conn.close()


def get_machine_by_id(machine_id):
    """Get a specific machine by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, name, starting_capital, timeframe, status, created_at
            FROM machines
            WHERE id = %s
        """, (machine_id,))
        machine = cur.fetchone()
        if machine:
            machine = dict(machine)
            # Convert Decimal to float
            machine['starting_capital'] = float(machine['starting_capital'])
        return machine
    finally:
        cur.close()
        conn.close()


def delete_machine_db(machine_id):
    """Delete a machine (cascades to trades and scenarios)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM machines WHERE id = %s", (machine_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# ========== Trade Data Operations ==========

def bulk_insert_trades(machine_id, trades_df):
    """Bulk insert trade data for a machine"""
    if trades_df.empty:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Convert DataFrame to list of tuples
        trades_data = []
        for _, row in trades_df.iterrows():
            trades_data.append((
                machine_id,
                row.get('trade_id'),
                row.get('instrument'),
                row.get('direction'),
                row.get('entry_time'),
                row.get('exit_time'),
                row.get('entry_price'),
                row.get('exit_price'),
                row.get('contracts'),
                row.get('pnl'),
                row.get('initial_risk'),
                row.get('r_multiple'),
                row.get('holding_minutes'),
                row.get('entry_hour'),
                row.get('exit_hour'),
                row.get('outcome'),
                row.get('stop_price'),
                row.get('timeframe', '15min')
            ))
        
        execute_values(cur, """
            INSERT INTO trades (
                machine_id, trade_id, instrument, direction, entry_time, exit_time,
                entry_price, exit_price, contracts, pnl, initial_risk, r_multiple,
                holding_minutes, entry_hour, exit_hour, outcome, stop_price, timeframe
            ) VALUES %s
            ON CONFLICT (machine_id, trade_id) DO NOTHING
        """, trades_data)
        
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_trades_for_machine(machine_id):
    """Get all trades for a machine"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT trade_id, instrument, direction, entry_time, exit_time,
                   entry_price, exit_price, contracts, pnl, initial_risk,
                   r_multiple, holding_minutes, entry_hour, exit_hour,
                   outcome, stop_price, timeframe
            FROM trades
            WHERE machine_id = %s
            ORDER BY entry_time
        """, (machine_id,))
        
        trades = cur.fetchall()
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame([dict(t) for t in trades])
        
        # Normalize numeric columns to float
        numeric_cols = ['entry_price', 'exit_price', 'pnl', 'initial_risk', 'r_multiple', 
                        'holding_minutes', 'stop_price', 'contracts']
        df = _normalize_numeric_columns(df, numeric_cols)
        
        return df
    finally:
        cur.close()
        conn.close()


# ========== Market Data Operations ==========

def bulk_insert_market_data(market_df):
    """Bulk insert market data"""
    if market_df.empty:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        market_data = []
        for _, row in market_df.iterrows():
            market_data.append((
                row.get('instrument'),
                row.get('timeframe'),
                row.get('timestamp'),
                row.get('open'),
                row.get('high'),
                row.get('low'),
                row.get('close'),
                row.get('volume')
            ))
        
        execute_values(cur, """
            INSERT INTO market_data (
                instrument, timeframe, timestamp, open, high, low, close, volume
            ) VALUES %s
            ON CONFLICT (instrument, timeframe, timestamp) DO NOTHING
        """, market_data)
        
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_market_data(instrument, timeframe):
    """Get market data for specific instrument and timeframe"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT instrument, timeframe, timestamp, open, high, low, close, volume
            FROM market_data
            WHERE instrument = %s AND timeframe = %s
            ORDER BY timestamp
        """, (instrument, timeframe))
        
        data = cur.fetchall()
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame([dict(d) for d in data])
        
        # Normalize numeric columns to float
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df = _normalize_numeric_columns(df, numeric_cols)
        
        return df
    finally:
        cur.close()
        conn.close()


def check_market_data_exists(instrument, timeframe):
    """Check if market data exists for given instrument and timeframe"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM market_data
            WHERE instrument = %s AND timeframe = %s
        """, (instrument, timeframe))
        count = cur.fetchone()[0]
        return count > 0
    finally:
        cur.close()
        conn.close()


# ========== Scenario Operations ==========

def save_scenario(machine_id, name, is_baseline, parameters, metrics=None, modified_trades=None):
    """Save a scenario and its results"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert scenario
        cur.execute("""
            INSERT INTO scenarios (machine_id, name, is_baseline, parameters)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (machine_id, name, is_baseline, json.dumps(parameters)))
        
        scenario_id = cur.fetchone()[0]
        
        # Insert results if provided
        if metrics:
            cur.execute("""
                INSERT INTO scenario_results (scenario_id, metrics, modified_trades)
                VALUES (%s, %s, %s)
            """, (scenario_id, json.dumps(metrics), json.dumps(modified_trades) if modified_trades else None))
        
        conn.commit()
        return scenario_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_scenarios_for_machine(machine_id):
    """Get all scenarios for a machine"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT s.id, s.name, s.is_baseline, s.parameters, s.created_at,
                   sr.metrics, sr.modified_trades
            FROM scenarios s
            LEFT JOIN scenario_results sr ON s.id = sr.scenario_id
            WHERE s.machine_id = %s
            ORDER BY s.is_baseline DESC, s.created_at
        """, (machine_id,))
        
        scenarios = cur.fetchall()
        return [dict(s) for s in scenarios]
    finally:
        cur.close()
        conn.close()


def delete_scenario(scenario_id):
    """Delete a scenario"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM scenarios WHERE id = %s", (scenario_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
