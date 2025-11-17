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
                instrument VARCHAR(10) NOT NULL DEFAULT 'MES',
                starting_capital DECIMAL(12, 2) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('live', 'simulated')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing machines table to add instrument column if missing
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'machines' AND column_name = 'instrument'
                ) THEN
                    ALTER TABLE machines ADD COLUMN instrument VARCHAR(10) NOT NULL DEFAULT 'MES';
                END IF;
            END $$;
        """)
        
        # Markets Table (new architecture)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Instruments Table (assets within markets)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                id VARCHAR(50) PRIMARY KEY,
                market_id VARCHAR(50) NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
                symbol VARCHAR(20) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(market_id, symbol)
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_instruments_market 
            ON instruments(market_id)
        """)
        
        # Portfolios Table (renamed from machines, multi-instrument support)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                starting_capital DECIMAL(12, 2) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('live', 'simulated')),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Portfolio-Instruments Junction Table (many-to-many)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_instruments (
                id SERIAL PRIMARY KEY,
                portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
                instrument_id VARCHAR(50) NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
                timeframe VARCHAR(10) NOT NULL,
                allocation_percent DECIMAL(5, 2) DEFAULT 100.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(portfolio_id, instrument_id, timeframe)
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_instruments_portfolio 
            ON portfolio_instruments(portfolio_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_instruments_instrument 
            ON portfolio_instruments(instrument_id)
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

def create_machine_db(machine_id, name, instrument, starting_capital, timeframe, status):
    """Create a new machine in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO machines (id, name, instrument, starting_capital, timeframe, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (machine_id, name, instrument, starting_capital, timeframe, status))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_all_machines(instrument=None):
    """Get all machines, optionally filtered by instrument"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if instrument:
            cur.execute("""
                SELECT id, name, instrument, starting_capital, timeframe, status, created_at
                FROM machines
                WHERE instrument = %s
                ORDER BY created_at DESC
            """, (instrument,))
        else:
            cur.execute("""
                SELECT id, name, instrument, starting_capital, timeframe, status, created_at
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
            SELECT id, name, instrument, starting_capital, timeframe, status, created_at
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


def update_machine_db(machine_id, name=None, instrument=None, starting_capital=None, timeframe=None, status=None):
    """Update an existing machine's properties"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if instrument is not None:
            updates.append("instrument = %s")
            params.append(instrument)
        if starting_capital is not None:
            updates.append("starting_capital = %s")
            params.append(starting_capital)
        if timeframe is not None:
            updates.append("timeframe = %s")
            params.append(timeframe)
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return False
        
        params.append(machine_id)
        query = f"UPDATE machines SET {', '.join(updates)} WHERE id = %s"
        
        cur.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
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


# ========== NEW ARCHITECTURE: Markets, Instruments, Portfolios ==========

def seed_initial_data():
    """Seed initial markets and instruments with all timeframe combinations"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Seed Markets
        markets = [
            ('index_futures', 'Index Futures', 'Micro futures contracts for major indices'),
            ('mt5', 'MT5 (Forex)', 'MetaTrader 5 Forex trading pairs'),
            ('crypto', 'Crypto', 'Cryptocurrency trading pairs')
        ]
        
        for market_id, name, description in markets:
            cur.execute("""
                INSERT INTO markets (id, name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (market_id, name, description))
        
        # Base symbols with their markets
        base_symbols = [
            # Index Futures
            ('MES', 'index_futures', 'Micro E-mini S&P 500'),
            ('MNQ', 'index_futures', 'Micro E-mini Nasdaq-100'),
            # MT5 Forex
            ('EURUSD', 'mt5', 'Euro vs US Dollar'),
            ('USDJPY', 'mt5', 'US Dollar vs Japanese Yen'),
            ('USDCAD', 'mt5', 'US Dollar vs Canadian Dollar'),
            # Crypto
            ('BTCUSDT', 'crypto', 'Bitcoin vs Tether'),
            ('ETHUSDT', 'crypto', 'Ethereum vs Tether'),
            ('LTCUSDT', 'crypto', 'Litecoin vs Tether'),
        ]
        
        # Timeframes
        timeframes = ['5min', '15min', '30min', '1H', '4H', 'Daily']
        
        # Create instrument for each symbol-timeframe combination
        for base_symbol, market_id, base_name in base_symbols:
            for timeframe in timeframes:
                instrument_id = f"{base_symbol}_{timeframe}"
                instrument_name = f"{base_name} - {timeframe}"
                
                cur.execute("""
                    INSERT INTO instruments (id, market_id, symbol, timeframe, name, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (instrument_id, market_id, base_symbol, timeframe, instrument_name, f"{base_name} at {timeframe} timeframe"))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def migrate_machines_to_portfolios():
    """Migrate existing machines to new portfolio structure (idempotent)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all existing machines
        cur.execute("SELECT * FROM machines")
        machines = cur.fetchall()
        
        if not machines:
            conn.commit()
            return 0
        
        migrated_count = 0
        for machine in machines:
            machine_id = machine['id']
            
            # Check if already migrated (idempotent - safe to run multiple times)
            cur.execute("SELECT id FROM portfolios WHERE id = %s", (machine_id,))
            if cur.fetchone():
                continue
            
            # Create portfolio from machine
            cur.execute("""
                INSERT INTO portfolios (id, name, starting_capital, status, description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    starting_capital = EXCLUDED.starting_capital,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                machine_id,
                machine['name'],
                machine['starting_capital'],
                machine['status'],
                f"Migrated from machine: {machine['name']}"
            ))
            
            # Link portfolio to instrument using composite ID (symbol_timeframe)
            base_symbol = machine.get('instrument', 'MES')
            timeframe = machine.get('timeframe', '15min')
            instrument_id = f"{base_symbol}_{timeframe}"  # e.g., "MES_15min"
            
            cur.execute("""
                INSERT INTO portfolio_instruments (portfolio_id, instrument_id, allocation_percent)
                VALUES (%s, %s, %s)
                ON CONFLICT (portfolio_id, instrument_id) DO UPDATE SET
                    allocation_percent = EXCLUDED.allocation_percent
            """, (machine_id, instrument_id, 100.00))
            
            migrated_count += 1
        
        conn.commit()
        return migrated_count
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# ========== Portfolio CRUD Operations (New) ==========

def create_portfolio_db(portfolio_id, name, starting_capital, status, description=None):
    """Create a new portfolio in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO portfolios (id, name, starting_capital, status, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (portfolio_id, name, starting_capital, status, description))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def add_instrument_to_portfolio(portfolio_id, instrument_id, allocation_percent=100.00):
    """Add an instrument to a portfolio (instrument_id includes timeframe, e.g., MES_15min)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO portfolio_instruments (portfolio_id, instrument_id, allocation_percent)
            VALUES (%s, %s, %s)
            ON CONFLICT (portfolio_id, instrument_id) DO UPDATE
            SET allocation_percent = EXCLUDED.allocation_percent
        """, (portfolio_id, instrument_id, allocation_percent))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_all_portfolios():
    """Get all portfolios"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, name, starting_capital, status, description, created_at
            FROM portfolios
            ORDER BY created_at DESC
        """)
        portfolios = cur.fetchall()
        return [dict(p) for p in portfolios]
    finally:
        cur.close()
        conn.close()


def get_portfolio_by_id(portfolio_id):
    """Get a specific portfolio by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, name, starting_capital, status, description, created_at
            FROM portfolios
            WHERE id = %s
        """, (portfolio_id,))
        portfolio = cur.fetchone()
        if portfolio:
            portfolio = dict(portfolio)
            portfolio['starting_capital'] = float(portfolio['starting_capital'])
        return portfolio
    finally:
        cur.close()
        conn.close()


def get_portfolio_instruments(portfolio_id):
    """Get all instruments in a portfolio"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT pi.instrument_id, pi.allocation_percent,
                   i.symbol, i.timeframe, i.name, i.market_id, m.name as market_name
            FROM portfolio_instruments pi
            JOIN instruments i ON pi.instrument_id = i.id
            JOIN markets m ON i.market_id = m.id
            WHERE pi.portfolio_id = %s
            ORDER BY i.market_id, i.symbol, i.timeframe
        """, (portfolio_id,))
        instruments = cur.fetchall()
        return [dict(inst) for inst in instruments]
    finally:
        cur.close()
        conn.close()


def get_all_markets():
    """Get all markets"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, name, description, created_at
            FROM markets
            ORDER BY name
        """)
        markets = cur.fetchall()
        return [dict(m) for m in markets]
    finally:
        cur.close()
        conn.close()


def get_instruments_by_market(market_id):
    """Get all instruments for a specific market"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, symbol, name, description, created_at
            FROM instruments
            WHERE market_id = %s
            ORDER BY symbol
        """, (market_id,))
        instruments = cur.fetchall()
        return [dict(i) for i in instruments]
    finally:
        cur.close()
        conn.close()


def get_all_instruments():
    """Get all instruments across all markets"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT i.id, i.symbol, i.name, i.description, i.market_id,
                   m.name as market_name
            FROM instruments i
            JOIN markets m ON i.market_id = m.id
            ORDER BY m.name, i.symbol
        """)
        instruments = cur.fetchall()
        return [dict(i) for i in instruments]
    finally:
        cur.close()
        conn.close()
