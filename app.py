import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

from data_generator import create_mock_data, generate_market_data, generate_trade_data
from analytics_engine import (
    calculate_all_metrics, get_equity_curve, get_time_of_day_performance,
    get_r_multiple_distribution, get_weekly_pnl_heatmap_data, get_monthly_returns
)
from scenario_engine import (
    create_baseline_scenario, create_scenario, get_comparison_matrix, get_scenario_summary
)
from visualizations import (
    create_candlestick_chart, create_equity_curve, create_weekly_pnl_heatmap,
    create_monthly_returns_grid, create_time_of_day_heatmap, create_r_multiple_histogram,
    create_comparison_bar_chart, create_returns_distribution
)
from portfolio_manager import (
    create_portfolio, get_portfolio_display_name, get_portfolio_color, validate_portfolio_name,
    delete_portfolio, get_active_portfolio, add_scenario_to_portfolio, get_all_scenarios_for_portfolio,
    get_portfolio_scenarios_count
)
from datetime import datetime

MAX_SCENARIOS = 10

st.set_page_config(page_title="Trading What-If Analysis", layout="wide", initial_sidebar_state="expanded")

st.title("📊 Trading Portfolio What-If Analysis")
st.markdown("**Investor Platform for Market and Portfolio Analysis**")

if 'market_data' not in st.session_state:
    st.session_state.market_data = {}
if 'portfolios' not in st.session_state:
    st.session_state.portfolios = {}
if 'active_portfolio_id' not in st.session_state:
    st.session_state.active_portfolio_id = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'show_portfolio_creator' not in st.session_state:
    st.session_state.show_portfolio_creator = False
if 'show_portfolio_editor' not in st.session_state:
    st.session_state.show_portfolio_editor = False
if 'selected_market' not in st.session_state:
    st.session_state.selected_market = None
if 'selected_market_id' not in st.session_state:
    st.session_state.selected_market_id = None
if 'navigation_mode' not in st.session_state:
    st.session_state.navigation_mode = 'markets'  # markets, instruments, portfolios
if 'selected_instrument_id' not in st.session_state:
    st.session_state.selected_instrument_id = None
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'show_machine_creator' not in st.session_state:
    st.session_state.show_machine_creator = False
if 'active_machine_id' not in st.session_state:
    st.session_state.active_machine_id = None
if 'show_market_creator' not in st.session_state:
    st.session_state.show_market_creator = False
if 'show_instrument_creator' not in st.session_state:
    st.session_state.show_instrument_creator = False
if 'edit_market_id' not in st.session_state:
    st.session_state.edit_market_id = None
if 'edit_instrument_id' not in st.session_state:
    st.session_state.edit_instrument_id = None
if 'edit_portfolio_id' not in st.session_state:
    st.session_state.edit_portfolio_id = None
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None
if 'show_machine_editor' not in st.session_state:
    st.session_state.show_machine_editor = False

from database import (
    get_all_machines, create_machine_db, update_machine_db, bulk_insert_trades,
    get_trades_for_machine, get_scenarios_for_machine, init_database,
    get_market_data, bulk_insert_market_data, seed_initial_data, migrate_machines_to_portfolios,
    get_all_markets, get_instruments_by_market, get_all_portfolios, get_portfolio_by_id,
    create_portfolio_db, add_instrument_to_portfolio, get_portfolio_instruments, seed_portfolio_0,
    create_market, update_market, delete_market, get_market_by_id,
    create_instrument, update_instrument, delete_instrument, get_instrument_by_id,
    update_portfolio, delete_portfolio, get_portfolios_by_instrument,
    delete_market_data, delete_trades_for_portfolio
)
from data_generator import generate_market_data, generate_trade_data
import uuid as uuid_lib

if not st.session_state.db_initialized:
    try:
        init_database()
        seed_initial_data()  # Seed markets, instruments, and contract specs
        migrate_machines_to_portfolios()  # Migrate existing machines to portfolios
        seed_portfolio_0()  # Create Portfolio 0 with test trades for July 1, 2025
        st.session_state.db_initialized = True
        db_available = True
    except Exception as e:
        db_available = False
        st.error(f"⚠️ Database connection failed: {str(e)}")
        st.info("Please ensure PostgreSQL is running and DATABASE_URL environment variable is set.")
        st.stop()
else:
    db_available = True

# ========== Delete Confirmation Modal ==========
if st.session_state.confirm_delete:
    delete_type, delete_id, delete_name = st.session_state.confirm_delete
    
    st.warning(f"⚠️ **Confirm Delete: {delete_name}**")
    st.markdown(f"Are you sure you want to delete this {delete_type}? This action cannot be undone.")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    if col1.button("✅ Yes, Delete", type="primary", use_container_width=True):
        try:
            if delete_type == 'market':
                delete_market(delete_id)
                st.success(f"✅ Market '{delete_name}' deleted!")
            elif delete_type == 'instrument':
                delete_instrument(delete_id)
                st.success(f"✅ Instrument '{delete_name}' deleted!")
            elif delete_type == 'portfolio':
                delete_portfolio(delete_id)
                st.success(f"✅ Portfolio '{delete_name}' deleted!")
            elif delete_type == 'trades':
                count = delete_trades_for_portfolio(delete_id)
                st.success(f"✅ Deleted {count} trades!")
            
            st.session_state.confirm_delete = None
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.confirm_delete = None
    
    if col2.button("❌ Cancel", use_container_width=True):
        st.session_state.confirm_delete = None
        st.rerun()
    
    st.stop()

# ========== Breadcrumb Navigation Component ==========
def render_breadcrumb():
    """Render clickable breadcrumb navigation showing current location in hierarchy"""
    breadcrumb_parts = []
    breadcrumb_keys = []
    breadcrumb_modes = []

    # Always start with Markets
    breadcrumb_parts.append("🏠 Markets")
    breadcrumb_keys.append("bc_markets")
    breadcrumb_modes.append("markets")

    # Add selected market if exists
    if st.session_state.selected_market_id:
        try:
            market = get_market_by_id(st.session_state.selected_market_id)
            if market:
                breadcrumb_parts.append(f"📊 {market['name']}")
                breadcrumb_keys.append("bc_market")
                breadcrumb_modes.append("instruments")
        except:
            pass

    # Add selected instrument if exists
    if st.session_state.selected_instrument_id:
        try:
            instrument = get_instrument_by_id(st.session_state.selected_instrument_id)
            if instrument:
                breadcrumb_parts.append(f"📈 {instrument['symbol']} {instrument['timeframe']}")
                breadcrumb_keys.append("bc_instrument")
                breadcrumb_modes.append("portfolios")
        except:
            pass

    # Add current mode-specific label
    if st.session_state.navigation_mode == 'portfolios' and st.session_state.selected_instrument_id:
        breadcrumb_parts.append("💼 Portfolios")
        breadcrumb_keys.append("bc_portfolios")
        breadcrumb_modes.append("portfolios")

    if st.session_state.active_machine_id and st.session_state.navigation_mode == 'analytics':
        try:
            portfolio = get_portfolio_by_id(st.session_state.active_machine_id)
            if portfolio:
                breadcrumb_parts.append(f"💼 {portfolio['name']}")
                breadcrumb_keys.append("bc_portfolio")
                breadcrumb_modes.append("portfolios")
                breadcrumb_parts.append("📊 Analytics")
                breadcrumb_keys.append("bc_analytics")
                breadcrumb_modes.append("analytics")
        except:
            pass

    # Render breadcrumb with separators
    if len(breadcrumb_parts) > 0:
        num_parts = len(breadcrumb_parts)
        num_cols = num_parts * 2 - 1  # parts + separators
        cols = st.columns([1] * num_cols)

        for i in range(num_parts):
            with cols[i * 2]:
                if st.button(breadcrumb_parts[i], key=breadcrumb_keys[i], use_container_width=True):
                    # Handle breadcrumb navigation
                    if i == 0:  # Markets
                        st.session_state.navigation_mode = 'markets'
                        st.session_state.selected_market_id = None
                        st.session_state.selected_instrument_id = None
                        st.session_state.active_machine_id = None
                    elif breadcrumb_modes[i] == 'instruments':  # Market selected
                        st.session_state.navigation_mode = 'instruments'
                        st.session_state.selected_instrument_id = None
                        st.session_state.active_machine_id = None
                    elif breadcrumb_modes[i] == 'portfolios':  # Instrument or Portfolios
                        st.session_state.navigation_mode = 'portfolios'
                        st.session_state.active_machine_id = None
                    st.rerun()

            # Add separator except for last item
            if i < num_parts - 1:
                with cols[i * 2 + 1]:
                    st.markdown("<div style='text-align: center; padding-top: 8px;'>›</div>", unsafe_allow_html=True)

        st.divider()


# ========== NEW NAVIGATION: Markets → Instruments → Portfolios ==========

# Navigation Mode: Markets
if st.session_state.navigation_mode == 'markets':
    render_breadcrumb()
    st.header("📈 Markets")
    st.markdown("Select a market to view its instruments and portfolios:")
    
    # Sidebar management buttons
    with st.sidebar:
        st.subheader("Market Management")
        if st.button("➕ Create Market", use_container_width=True):
            st.session_state.show_market_creator = True
            st.session_state.edit_market_id = None
            st.rerun()
    
    # Show Create Market Form
    if st.session_state.show_market_creator and st.session_state.edit_market_id is None:
        st.markdown("### ➕ Create New Market")
        with st.form("create_market_form"):
            market_id = st.text_input("Market ID", placeholder="e.g., commodities", help="Lowercase, no spaces (use underscore)")
            market_name = st.text_input("Market Name", placeholder="e.g., Commodities")
            market_desc = st.text_area("Description", placeholder="Brief description of this market")
            
            col1, col2 = st.columns(2)
            create_btn = col1.form_submit_button("✅ Create", use_container_width=True, type="primary")
            cancel_btn = col2.form_submit_button("❌ Cancel", use_container_width=True)
            
            if create_btn and market_id and market_name:
                try:
                    create_market(market_id, market_name, market_desc)
                    st.success(f"✅ Market '{market_name}' created successfully!")
                    st.session_state.show_market_creator = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating market: {str(e)}")
            elif cancel_btn:
                st.session_state.show_market_creator = False
                st.rerun()
        st.divider()
    
    # Show Edit Market Form
    if st.session_state.edit_market_id:
        markets = get_all_markets()
        edit_market = next((m for m in markets if m['id'] == st.session_state.edit_market_id), None)
        
        if edit_market:
            st.markdown(f"### ✏️ Edit Market: {edit_market['name']}")
            with st.form("edit_market_form"):
                st.caption(f"Market ID: `{edit_market['id']}` (cannot be changed)")
                new_name = st.text_input("Market Name", value=edit_market['name'])
                new_desc = st.text_area("Description", value=edit_market.get('description', ''))
                
                col1, col2 = st.columns(2)
                update_btn = col1.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                cancel_btn = col2.form_submit_button("❌ Cancel", use_container_width=True)
                
                if update_btn and new_name:
                    try:
                        update_market(edit_market['id'], new_name, new_desc)
                        st.success(f"✅ Market '{new_name}' updated successfully!")
                        st.session_state.edit_market_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating market: {str(e)}")
                elif cancel_btn:
                    st.session_state.edit_market_id = None
                    st.rerun()
            st.divider()
    
    # Get all markets from database
    markets = get_all_markets()
    
    # Display market cards
    cols = st.columns(min(len(markets), 3))
    for idx, market in enumerate(markets):
        with cols[idx % 3]:
            # Market icon mapping
            icons = {'index_futures': '📈', 'mt5': '💱', 'crypto': '₿'}
            market_icon = icons.get(market['id'], '📊')
            
            st.markdown(f"### {market_icon} {market['name']}")
            st.caption(market.get('description', ''))
            
            # Count instruments and portfolios for this market
            instruments = get_instruments_by_market(market['id'])
            # Count unique base symbols (not timeframes)
            unique_symbols = len(set([inst['symbol'] for inst in instruments]))
            
            st.metric("Instruments", f"{unique_symbols} symbols × 6 timeframes")
            
            # Action buttons
            col_view, col_edit, col_del = st.columns([2, 1, 1])
            if col_view.button(f"View", use_container_width=True, type="primary", key=f"select_market_{market['id']}"):
                st.session_state.selected_market_id = market['id']
                st.session_state.navigation_mode = 'instruments'
                st.rerun()
            
            if col_edit.button("✏️", use_container_width=True, key=f"edit_market_{market['id']}", help="Edit market"):
                st.session_state.edit_market_id = market['id']
                st.session_state.show_market_creator = False
                st.rerun()
            
            if col_del.button("🗑️", use_container_width=True, key=f"delete_market_{market['id']}", help="Delete market"):
                st.session_state.confirm_delete = ('market', market['id'], market['name'])
                st.rerun()
    
    st.stop()

# Navigation Mode: Instruments
if st.session_state.navigation_mode == 'instruments':
    render_breadcrumb()

    # Sidebar navigation
    with st.sidebar:
        if st.button("← Back to Markets"):
            st.session_state.navigation_mode = 'markets'
            st.session_state.selected_market_id = None
            st.rerun()
        
        st.divider()
        st.subheader("Instrument Management")
        if st.button("➕ Create Instrument", use_container_width=True):
            st.session_state.show_instrument_creator = True
            st.session_state.edit_instrument_id = None
            st.rerun()
    
    # Get selected market
    markets = get_all_markets()
    current_market = next((m for m in markets if m['id'] == st.session_state.selected_market_id), None)
    
    if not current_market:
        st.error("Market not found")
        st.stop()
    
    st.header(f"📊 {current_market['name']} - Instruments")
    st.markdown(f"*{current_market.get('description', '')}*")
    
    # Show Create Instrument Form
    if st.session_state.show_instrument_creator and st.session_state.edit_instrument_id is None:
        st.markdown("### ➕ Create New Instrument")
        st.info("💡 Select multiple timeframes to create them all at once")

        with st.form("create_instrument_form"):
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Symbol*", placeholder="e.g., MES, AAPL")
                name = st.text_input("Name*", placeholder="e.g., Micro E-mini S&P 500")
            with col2:
                timeframes = st.multiselect(
                    "Timeframes* (select multiple)",
                    options=['5min', '15min', '30min', '1H', '4H', 'Daily'],
                    default=['15min'],
                    help="Select all timeframes you want to create for this instrument"
                )
                description = st.text_input("Description (optional)")

            col_create, col_cancel = st.columns(2)
            create_btn = col_create.form_submit_button("✅ Create", use_container_width=True, type="primary")
            cancel_btn = col_cancel.form_submit_button("❌ Cancel", use_container_width=True)

            if create_btn and symbol and name and timeframes:
                created_count = 0
                errors = []

                for timeframe in timeframes:
                    instrument_id = f"{symbol}_{timeframe}" if timeframe != '15min' else symbol
                    try:
                        create_instrument(instrument_id, current_market['id'], symbol, timeframe, name, description)
                        created_count += 1
                    except Exception as e:
                        errors.append(f"{timeframe}: {str(e)}")

                if created_count > 0:
                    st.success(f"✅ Created {created_count} instrument(s) for {symbol}!")
                if errors:
                    st.warning(f"⚠️ Some timeframes failed:\n" + "\n".join(errors))

                if created_count > 0:
                    st.session_state.show_instrument_creator = False
                    st.rerun()
            elif cancel_btn:
                st.session_state.show_instrument_creator = False
                st.rerun()
        st.divider()
    
    # Get instruments for this market
    instruments = get_instruments_by_market(current_market['id'])
    
    # Group by symbol
    symbols_dict = {}
    for inst in instruments:
        symbol = inst['symbol']
        if symbol not in symbols_dict:
            symbols_dict[symbol] = {'name': inst['name'].split(' - ')[0], 'instruments': []}
        symbols_dict[symbol]['instruments'].append(inst)
    
    st.subheader(f"Available Instruments ({len(symbols_dict)} symbols)")
    
    # Display in columns
    cols = st.columns(2)
    for idx, (symbol, data) in enumerate(sorted(symbols_dict.items())):
        with cols[idx % 2]:
            with st.expander(f"**{symbol}** - {data['name']}", expanded=False):
                for inst in sorted(data['instruments'], key=lambda x: x['timeframe']):
                    st.markdown(f"#### ⏱️ {inst['timeframe']}")

                    # Get portfolio count for this instrument
                    portfolio_count = len(get_portfolios_by_instrument(inst['id']))
                    st.caption(f"📊 {portfolio_count} portfolios")

                    col_view, col_edit, col_del = st.columns([2, 1, 1])

                    if col_view.button(f"📊 Portfolios", key=f"view_port_{inst['id']}", use_container_width=True):
                        st.session_state.selected_instrument_id = inst['id']
                        st.session_state.navigation_mode = 'portfolios'
                        st.rerun()

                    if col_edit.button("✏️", key=f"edit_inst_{inst['id']}", help="Edit", use_container_width=True):
                        st.session_state.edit_instrument_id = inst['id']
                        st.session_state.show_instrument_creator = False
                        st.rerun()

                    if col_del.button("🗑️", key=f"del_inst_{inst['id']}", help="Delete", use_container_width=True):
                        st.session_state.confirm_delete = ('instrument', inst['id'], inst['name'])
                        st.rerun()

                    st.divider()

    st.divider()

    # Market Data Management Section
    st.subheader("📊 Market Data Management")
    st.markdown("Upload OHLCV candlestick data for instruments in this market. Market data is shared across all portfolios using the same instrument.")

    # Select instrument for market data upload
    if instruments:
        with st.expander("📤 Upload Market Data (OHLCV)", expanded=False):
            selected_inst_for_data = st.selectbox(
                "Select Instrument",
                options=instruments,
                format_func=lambda x: f"{x['symbol']} ({x['timeframe']})",
                key="market_data_instrument_select"
            )

            st.caption("**Required CSV columns:** timestamp, open, high, low, close, volume")

            market_csv = st.file_uploader(
                "Upload Market Data CSV",
                type=['csv'],
                help="Upload OHLCV candlestick data",
                key="upload_market_data_csv"
            )

            if market_csv:
                try:
                    preview_df = pd.read_csv(market_csv, nrows=10)
                    st.success(f"✅ CSV loaded: {len(preview_df)} rows previewed")
                    st.dataframe(preview_df, use_container_width=True)

                    # Check required columns
                    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    missing_cols = [col for col in required_cols if col not in preview_df.columns]
                    if missing_cols:
                        st.warning(f"⚠️ Missing required columns: {', '.join(missing_cols)}")
                    else:
                        st.info("✅ All required columns found")

                        if st.button("Import Market Data", type="primary"):
                            try:
                                market_csv.seek(0)
                                market_df = pd.read_csv(market_csv)
                                # Add instrument_id to the dataframe
                                market_df['instrument_id'] = selected_inst_for_data['id']
                                bulk_insert_market_data(market_df)
                                st.success(f"✅ Imported {len(market_df)} candles for {selected_inst_for_data['symbol']} {selected_inst_for_data['timeframe']}!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error importing market data: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {str(e)}")

        with st.expander("🗑️ Delete Market Data", expanded=False):
            if instruments:
                delete_inst = st.selectbox(
                    "Select Instrument to Delete Market Data",
                    options=instruments,
                    format_func=lambda x: f"{x['symbol']} ({x['timeframe']})",
                    key="delete_market_data_select"
                )

                if st.button("🗑️ Delete All Market Data for This Instrument", type="secondary"):
                    try:
                        delete_market_data(delete_inst['id'])
                        st.success(f"✅ Market data deleted for {delete_inst['symbol']} {delete_inst['timeframe']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    st.divider()

    st.stop()

# Navigation Mode: Portfolios
if st.session_state.navigation_mode == 'portfolios':
    render_breadcrumb()

    # Sidebar navigation
    with st.sidebar:
        if st.button("← Back to Instruments"):
            st.session_state.navigation_mode = 'instruments'
            st.rerun()
        
        st.divider()
        st.subheader("Portfolio Management")
        if st.button("➕ Create Portfolio", use_container_width=True):
            st.session_state.show_portfolio_creator = True
            st.session_state.edit_portfolio_id = None
            st.rerun()
    
    # Get selected market for context
    markets = get_all_markets()
    current_market = next((m for m in markets if m['id'] == st.session_state.selected_market_id), None)
    
    st.header("💼 Portfolios")
    if current_market:
        st.markdown(f"**Market Filter:** {current_market['name']}")
    
    # Show Create Portfolio Form
    if st.session_state.show_portfolio_creator and st.session_state.edit_portfolio_id is None:
        st.markdown("### ➕ Create New Portfolio")
        st.markdown(f"**For instrument:** {instrument['symbol']} {instrument['timeframe']}")

        with st.form("create_portfolio_form"):
            col1, col2 = st.columns(2)
            with col1:
                portfolio_name = st.text_input("Portfolio Name*", placeholder="e.g., Growth Portfolio")
                starting_capital = st.number_input("Starting Capital ($)*", min_value=1000, value=100000, step=1000)
            with col2:
                status = st.selectbox("Status*", ['live', 'simulated'])
                description = st.text_area("Description (optional)", placeholder="Brief description")

            st.divider()
            st.subheader("📤 Import Initial Trade Data (Optional)")
            st.caption("Upload a CSV file with your trade history to populate this portfolio")
            trades_csv = st.file_uploader(
                "Upload Trades CSV",
                type=['csv'],
                help="Required columns: entry_time, exit_time, entry_price, exit_price, pnl, direction, instrument",
                key="create_portfolio_csv"
            )

            # Show CSV preview if uploaded
            if trades_csv:
                try:
                    preview_df = pd.read_csv(trades_csv, nrows=10)
                    st.success(f"✅ CSV loaded: {len(preview_df)} rows previewed (showing first 10)")
                    st.dataframe(preview_df, use_container_width=True)

                    # Check required columns
                    required_cols = ['entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction', 'instrument']
                    missing_cols = [col for col in required_cols if col not in preview_df.columns]
                    if missing_cols:
                        st.warning(f"⚠️ Missing required columns: {', '.join(missing_cols)}")
                    else:
                        st.info("✅ All required columns found")
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {str(e)}")

            col_create, col_cancel = st.columns(2)
            create_btn = col_create.form_submit_button("✅ Create Portfolio", use_container_width=True, type="primary")
            cancel_btn = col_cancel.form_submit_button("❌ Cancel", use_container_width=True)

            if create_btn and portfolio_name:
                portfolio_id = str(uuid_lib.uuid4())
                try:
                    # Create portfolio
                    create_portfolio_db(portfolio_id, portfolio_name, starting_capital, status, description)

                    # Link portfolio to instrument
                    add_instrument_to_portfolio(portfolio_id, st.session_state.selected_instrument_id, 100.0)

                    # Import trades if CSV provided
                    if trades_csv:
                        trades_csv.seek(0)  # Reset file pointer
                        trades_df = pd.read_csv(trades_csv)
                        bulk_insert_trades(portfolio_id, trades_df)
                        st.success(f"✅ Portfolio '{portfolio_name}' created with {len(trades_df)} trades!")
                    else:
                        st.success(f"✅ Portfolio '{portfolio_name}' created!")

                    st.session_state.show_portfolio_creator = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creating portfolio: {str(e)}")
            elif cancel_btn:
                st.session_state.show_portfolio_creator = False
                st.rerun()
        st.divider()
    
    # Show Edit Portfolio Form
    if st.session_state.edit_portfolio_id:
        all_portfolios = get_all_portfolios()
        edit_port = next((p for p in all_portfolios if p['id'] == st.session_state.edit_portfolio_id), None)
        
        if edit_port:
            st.markdown(f"### ✏️ Edit Portfolio: {edit_port['name']}")
            with st.form("edit_portfolio_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Portfolio Name", value=edit_port['name'])
                    new_capital = st.number_input("Starting Capital ($)", value=float(edit_port['starting_capital']), min_value=1000.0, step=1000.0)
                with col2:
                    new_status = st.selectbox("Status", ['live', 'simulated'], index=0 if edit_port['status']=='live' else 1)
                    new_desc = st.text_area("Description", value=edit_port.get('description', ''))
                
                col_save, col_cancel = st.columns(2)
                save_btn = col_save.form_submit_button("💾 Save", use_container_width=True, type="primary")
                cancel_btn = col_cancel.form_submit_button("❌ Cancel", use_container_width=True)
                
                if save_btn and new_name:
                    try:
                        update_portfolio(edit_port['id'], new_name, new_capital, new_status, new_desc)
                        st.success(f"✅ Portfolio '{new_name}' updated!")
                        st.session_state.edit_portfolio_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                elif cancel_btn:
                    st.session_state.edit_portfolio_id = None
                    st.rerun()
            st.divider()

    # Ensure instrument is selected
    if not st.session_state.selected_instrument_id:
        st.error("⚠️ No instrument selected. Please select an instrument first.")
        if st.button("← Go Back to Instruments"):
            st.session_state.navigation_mode = 'instruments'
            st.rerun()
        st.stop()

    # Get portfolios for selected instrument
    instrument = get_instrument_by_id(st.session_state.selected_instrument_id)
    if not instrument:
        st.error("⚠️ Instrument not found.")
        st.stop()

    st.header(f"💼 Portfolios for {instrument['symbol']} {instrument['timeframe']}")
    all_portfolios = get_portfolios_by_instrument(st.session_state.selected_instrument_id)

    if not all_portfolios:
        st.info(f"📊 No portfolios found for {instrument['symbol']} {instrument['timeframe']}.")
        st.markdown(f"**Create your first portfolio** for this instrument to get started!")
    else:
        st.markdown(f"**Total Portfolios:** {len(all_portfolios)}")
        st.divider()
        
        # Display portfolios
        for portfolio in all_portfolios:
            with st.expander(f"{'🟢' if portfolio['status'] == 'live' else '⚪'} {portfolio['name']}", expanded=(portfolio['name'] == 'Portfolio 0')):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Starting Capital", f"${portfolio['starting_capital']:,.0f}")
                with col2:
                    st.metric("Status", portfolio['status'].title())
                with col3:
                    # Get number of trades (returns DataFrame)
                    trades_df = get_trades_for_machine(portfolio['id'])
                    if not trades_df.empty:
                        total_pnl = trades_df['pnl'].sum()
                        st.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{len(trades_df)} trades")
                    else:
                        st.metric("Trades", "0")
                
                # Show instruments in this portfolio
                instruments = get_portfolio_instruments(portfolio['id'])
                if instruments:
                    st.write("**Instruments:**")
                    for inst in instruments:
                        st.write(f"- {inst['symbol']} ({inst['timeframe']}) - {inst['allocation_percent']}% allocation")
                
                # Show trades summary if available
                if not trades_df.empty:
                    st.write(f"**Recent Trades:** ({len(trades_df)} total)")
                    recent_trades = trades_df.head(5)[['instrument', 'direction', 'entry_time', 'exit_time', 'pnl']]
                    st.dataframe(recent_trades, use_container_width=True, hide_index=True)
                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                if col_btn1.button(f"📊 Analytics", key=f"view_{portfolio['id']}", use_container_width=True, type="primary"):
                    st.session_state.active_machine_id = portfolio['id']
                    st.session_state.navigation_mode = 'analytics'
                    st.rerun()
                
                if col_btn2.button("✏️ Edit", key=f"edit_port_{portfolio['id']}", use_container_width=True):
                    st.session_state.edit_portfolio_id = portfolio['id']
                    st.session_state.show_portfolio_creator = False
                    st.rerun()
                
                if col_btn3.button("🗑️ Delete", key=f"delete_{portfolio['id']}", use_container_width=True):
                    st.session_state.confirm_delete = ('portfolio', portfolio['id'], portfolio['name'])
                    st.rerun()
    
    st.stop()

# Navigation Mode: Analytics (all the existing features)
if st.session_state.navigation_mode == 'analytics':
    render_breadcrumb()

    # Sidebar navigation
    with st.sidebar:
        if st.button("← Back to Portfolios"):
            st.session_state.navigation_mode = 'portfolios'
            st.rerun()
        
        st.divider()
        st.subheader("📁 Data Management")
        
        # Trade Data Upload
        with st.expander("📤 Add More Trades"):
            st.caption("Upload additional trade data to append to this portfolio")
            trades_csv = st.file_uploader("Upload Trades CSV", type=['csv'], key="import_trades_csv")

            if trades_csv:
                try:
                    preview_df = pd.read_csv(trades_csv, nrows=10)
                    st.success(f"✅ CSV loaded: {len(preview_df)} rows previewed")
                    st.dataframe(preview_df, use_container_width=True)

                    if st.button("Import Trades", key="import_trades_btn", type="primary"):
                        trades_csv.seek(0)
                        trades_df = pd.read_csv(trades_csv)
                        bulk_insert_trades(st.session_state.active_machine_id, trades_df)
                        st.success(f"✅ Imported {len(trades_df)} trades!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # Delete Data
        with st.expander("🗑️ Delete Data"):
            if st.button("🗑️ Delete All Trades", key="del_trades_btn", use_container_width=True, type="secondary"):
                st.session_state.confirm_delete = ('trades', st.session_state.active_machine_id, 'all trades')
                st.rerun()

    # Get portfolio and trades
    portfolio = get_portfolio_by_id(st.session_state.active_machine_id)
    if not portfolio:
        st.error("⚠️ Portfolio not found")
        st.stop()

    trades_df = get_trades_for_machine(st.session_state.active_machine_id)

    # Empty State - No Trades Yet
    if trades_df.empty:
        st.info("📊 No Trade Data Yet")
        st.markdown(f"""
        ### Get Started with Analytics

        Portfolio **{portfolio['name']}** doesn't have any trade data yet.

        **To see analytics, you need to:**
        1. Download your trade history from your broker
        2. Format it as a CSV file with required columns
        3. Upload it using the sidebar

        **Required CSV columns:**
        - `entry_time` - Trade entry timestamp
        - `exit_time` - Trade exit timestamp
        - `entry_price` - Entry price
        - `exit_price` - Exit price
        - `pnl` - Profit/Loss for the trade
        - `direction` - Trade direction (Long/Short)
        - `instrument` - Instrument symbol

        ---
        """)

        # Large upload area for better UX
        st.subheader("📤 Upload Your Trade History")
        trades_csv_empty = st.file_uploader(
            "Drop your trades CSV file here",
            type=['csv'],
            help="Upload your trade history to see analytics",
            key="empty_state_csv_upload"
        )

        if trades_csv_empty:
            try:
                preview_df = pd.read_csv(trades_csv_empty, nrows=10)
                st.success(f"✅ CSV loaded successfully!")
                st.markdown("**Preview (first 10 rows):**")
                st.dataframe(preview_df, use_container_width=True)

                # Check required columns
                required_cols = ['entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction', 'instrument']
                missing_cols = [col for col in required_cols if col not in preview_df.columns]

                if missing_cols:
                    st.warning(f"⚠️ Missing required columns: {', '.join(missing_cols)}")
                    st.info("Please update your CSV file to include all required columns.")
                else:
                    st.success("✅ All required columns found!")

                    if st.button("Import Trades and View Analytics", type="primary", use_container_width=True):
                        trades_csv_empty.seek(0)
                        full_df = pd.read_csv(trades_csv_empty)
                        bulk_insert_trades(st.session_state.active_machine_id, full_df)
                        st.success(f"🎉 Successfully imported {len(full_df)} trades!")
                        st.balloons()
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")

        st.stop()  # Don't show analytics tabs if no data

    # Continue with all the existing analytics features below...
    # (Let the rest of the app.py code run normally)

if st.session_state.show_machine_creator:
    st.markdown(f"### ➕ Create New Machine for {st.session_state.selected_market}")
    
    with st.form("machine_creator_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            machine_name = st.text_input("Machine Name", placeholder=f"e.g., {st.session_state.selected_market} Live $100k (15min)")
            starting_capital = st.number_input("Starting Capital ($)", min_value=10000, max_value=10000000, value=50000, step=5000)
            timeframe = st.selectbox("Timeframe", options=['5min', '15min', '30min', '1hr', '4hr', 'daily'], index=1)
        
        with col2:
            st.info(f"**Market:** {st.session_state.selected_market}")
            status = st.selectbox("Status", options=['live', 'simulated'], format_func=lambda x: f"🟢 Live" if x == 'live' else "⚪ Simulated")
            data_source = st.radio("Trade Data Source:", ["Generate Mock Data", "Upload CSV Files"])
        
        csv_file = None
        if data_source == "Upload CSV Files":
            st.markdown("**CSV Format Requirements:**")
            st.caption("Required columns: `instrument`, `direction`, `entry_time`, `exit_time`, `entry_price`, `exit_price`, `pnl`")
            st.caption("Optional columns: `contracts`, `initial_risk`, `r_multiple`, `holding_minutes`, `stop_price`")
            csv_file = st.file_uploader("Upload Trade CSV", type=['csv'], key="trade_csv_upload")
        
        col_btn1, col_btn2 = st.columns(2)
        create_btn = col_btn1.form_submit_button("✅ Create Machine", use_container_width=True, type="primary")
        cancel_btn = col_btn2.form_submit_button("❌ Cancel", use_container_width=True)
        
        if create_btn:
            if machine_name:
                machine_id = str(uuid_lib.uuid4())
                
                with st.spinner("Creating machine and generating data..."):
                    try:
                        selected_instrument = st.session_state.selected_market
                        create_machine_db(machine_id, machine_name, selected_instrument, starting_capital, timeframe, status)
                        
                        if data_source == "Generate Mock Data":
                            # Step 1: Generate or load market data for this timeframe
                            from datetime import datetime, timedelta
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=365 * 2)  # 2 years of data
                            
                            market_df = get_market_data(selected_instrument, timeframe)
                            if market_df.empty:
                                base_price = 5500 if selected_instrument == 'MES' else 19500
                                volatility = 0.015 if selected_instrument == 'MES' else 0.02
                                market_df = generate_market_data(selected_instrument, start_date, end_date, base_price=base_price, volatility=volatility, timeframe=timeframe)
                                bulk_insert_market_data(market_df)
                            
                            # Step 2: Generate trades using the market data
                            trades_df = generate_trade_data(selected_instrument, market_df, trades_per_day_range=(2, 3), starting_capital=starting_capital)
                            
                            # Step 3: Insert trades into database
                            bulk_insert_trades(machine_id, trades_df)
                        
                        elif data_source == "Upload CSV Files" and csv_file is not None:
                            # Parse and validate CSV file
                            import pandas as pd
                            trades_df = pd.read_csv(csv_file)
                            
                            # Validate required columns
                            required_cols = ['instrument', 'direction', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl']
                            missing_cols = [col for col in required_cols if col not in trades_df.columns]
                            
                            if missing_cols:
                                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
                            
                            # Add optional columns with defaults if not present
                            if 'trade_id' not in trades_df.columns:
                                trades_df['trade_id'] = [f"{row['instrument']}_{i+1}" for i, row in trades_df.iterrows()]
                            if 'contracts' not in trades_df.columns:
                                trades_df['contracts'] = 1
                            if 'timeframe' not in trades_df.columns:
                                trades_df['timeframe'] = timeframe
                            
                            # Calculate optional fields if not present
                            if 'holding_minutes' not in trades_df.columns:
                                trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
                                trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
                                trades_df['holding_minutes'] = (trades_df['exit_time'] - trades_df['entry_time']).dt.total_seconds() / 60
                            
                            if 'entry_hour' not in trades_df.columns:
                                trades_df['entry_hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
                            if 'exit_hour' not in trades_df.columns:
                                trades_df['exit_hour'] = pd.to_datetime(trades_df['exit_time']).dt.hour
                            
                            if 'outcome' not in trades_df.columns:
                                trades_df['outcome'] = trades_df['pnl'].apply(lambda x: 'Win' if x > 0 else ('Loss' if x < 0 else 'Breakeven'))
                            
                            if 'initial_risk' not in trades_df.columns:
                                trades_df['initial_risk'] = abs(trades_df['pnl'] * 0.5)  # Rough estimate
                            
                            if 'r_multiple' not in trades_df.columns:
                                trades_df['r_multiple'] = trades_df['pnl'] / trades_df['initial_risk'].replace(0, 1)
                            
                            if 'stop_price' not in trades_df.columns:
                                trades_df['stop_price'] = trades_df['entry_price'] * 0.98  # Default 2% stop
                            
                            # Insert trades into database
                            bulk_insert_trades(machine_id, trades_df)
                            st.info(f"✅ Imported {len(trades_df)} trades from CSV")
                        
                        st.session_state.show_machine_creator = False
                        st.session_state.active_machine_id = machine_id
                        st.success(f"✅ Machine '{machine_name}' created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating machine: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.error("Please provide a machine name")
        
        if cancel_btn:
            st.session_state.show_machine_creator = False
            st.rerun()
    
    st.stop()

if st.session_state.show_machine_editor and st.session_state.active_machine_id:
    from database import get_machine_by_id
    machine_to_edit = get_machine_by_id(st.session_state.active_machine_id)
    
    if machine_to_edit:
        st.markdown("### ✏️ Edit Machine")
        
        with st.form("machine_editor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input("Machine Name", value=machine_to_edit['name'])
                edit_capital = st.number_input("Starting Capital ($)", 
                                               min_value=10000, 
                                               max_value=10000000, 
                                               value=int(machine_to_edit['starting_capital']), 
                                               step=5000)
                edit_timeframe = st.selectbox("Timeframe", 
                                             options=['5min', '15min', '30min', '1hr', '4hr', 'daily'],
                                             index=['5min', '15min', '30min', '1hr', '4hr', 'daily'].index(machine_to_edit['timeframe']))
            
            with col2:
                edit_status = st.selectbox("Status", 
                                          options=['live', 'simulated'],
                                          index=0 if machine_to_edit['status'] == 'live' else 1,
                                          format_func=lambda x: f"🟢 Live" if x == 'live' else "⚪ Simulated")
            
            st.warning("⚠️ Changing timeframe or capital will affect scenario calculations. Consider re-creating scenarios after updating.")
            
            col_btn1, col_btn2 = st.columns(2)
            save_btn = col_btn1.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            cancel_btn = col_btn2.form_submit_button("❌ Cancel", use_container_width=True)
            
            if save_btn:
                try:
                    update_machine_db(
                        st.session_state.active_machine_id,
                        name=edit_name,
                        starting_capital=edit_capital,
                        timeframe=edit_timeframe,
                        status=edit_status
                    )
                    st.session_state.show_machine_editor = False
                    st.success(f"✅ Machine '{edit_name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating machine: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            
            if cancel_btn:
                st.session_state.show_machine_editor = False
                st.rerun()
    
    st.stop()

active_machine = None
active_scenarios = []

if st.session_state.active_machine_id:
    from database import get_machine_by_id
    active_machine = get_machine_by_id(st.session_state.active_machine_id)
    
    if active_machine:
        st.info(f"**Active Machine**: {'🟢' if active_machine['status'] == 'live' else '⚪'} {active_machine['name']} | ${active_machine['starting_capital']:,.0f} | {active_machine['timeframe']}")
        
        active_scenarios = get_scenarios_for_machine(st.session_state.active_machine_id)
        
        if not active_scenarios:
            trades_df = get_trades_for_machine(st.session_state.active_machine_id)
            if not trades_df.empty:
                from scenario_engine import create_baseline_scenario
                from database import save_scenario
                
                baseline = create_baseline_scenario(trades_df, active_machine['starting_capital'])
                scenario_id = save_scenario(
                    st.session_state.active_machine_id,
                    baseline['name'],
                    True,
                    baseline['params'],  # Fixed: was 'parameters', should be 'params'
                    baseline.get('metrics'),
                    baseline.get('modified_trades')
                )
                active_scenarios = get_scenarios_for_machine(st.session_state.active_machine_id)
    else:
        st.warning("Selected machine not found in database")
        st.session_state.active_machine_id = None

with st.sidebar:
    if st.session_state.selected_market:
        st.markdown(f"### 📍 {st.session_state.selected_market} Market")
        
        if st.button("← Back to Markets", use_container_width=True):
            st.session_state.selected_market = None
            st.session_state.active_machine_id = None
            st.rerun()
        
        st.divider()
        st.header("🤖 Machine Management")
        
        from database import get_all_machines, create_machine_db, delete_machine_db, bulk_insert_trades, get_trades_for_machine
        from database import init_database, get_market_data, check_market_data_exists, bulk_insert_market_data
        
        init_database()
        
        db_machines = get_all_machines(instrument=st.session_state.selected_market)
        
        if db_machines:
            machine_options = {m['id']: f"{'🟢' if m['status'] == 'live' else '⚪'} {m['name']}" for m in db_machines}
            
            selected_machine_id = st.selectbox(
                "Select Machine:",
                options=list(machine_options.keys()),
                format_func=lambda x: machine_options[x],
                index=list(machine_options.keys()).index(st.session_state.active_machine_id) if st.session_state.active_machine_id in machine_options else 0
            )
            
            if selected_machine_id != st.session_state.active_machine_id:
                st.session_state.active_machine_id = selected_machine_id
                st.rerun()
            
            st.info(f"**Machines**: {len(db_machines)} for {st.session_state.selected_market}")
        else:
            st.warning(f"No machines created for {st.session_state.selected_market} yet. Create your first machine below!")
            st.session_state.active_machine_id = None
        
        st.divider()
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("➕ Create", use_container_width=True):
        st.session_state.show_machine_creator = True
        st.rerun()
    
    if col_btn2.button("✏️ Edit", use_container_width=True, disabled=not st.session_state.active_machine_id):
        st.session_state.show_machine_editor = True
        st.rerun()
    
    if st.session_state.active_machine_id:
        if st.button("🗑️ Delete Selected Machine", use_container_width=True, type="secondary"):
            delete_machine_db(st.session_state.active_machine_id)
            st.session_state.active_machine_id = None
            st.success("Machine deleted!")
            st.rerun()
    
        st.divider()
        st.subheader(f"📁 Market Data for {st.session_state.selected_market}")
        
        if st.button(f"🎲 Generate Data (All Timeframes)", use_container_width=True):
            with st.spinner(f"Generating market data for {st.session_state.selected_market}..."):
                from data_generator import generate_market_data
                
                timeframes = ['5min', '15min', '30min', '1hr', '4hr', 'daily']
                total_inserted = 0
                
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365 * 2)
                
                instrument = st.session_state.selected_market
                for timeframe in timeframes:
                    if not check_market_data_exists(instrument, timeframe):
                        base_price = 5500 if instrument == 'MES' else 19500
                        volatility = 0.015 if instrument == 'MES' else 0.02
                        market_df = generate_market_data(instrument, start_date, end_date, base_price, volatility, timeframe)
                        inserted = bulk_insert_market_data(market_df)
                        total_inserted += inserted
                
                st.success(f"✅ Generated {total_inserted} market data rows for {st.session_state.selected_market}!")
                st.rerun()
        
        
        st.caption(f"💡 Market data for {st.session_state.selected_market} is automatically generated when creating machines")

if not st.session_state.active_machine_id or not active_machine:
    st.info("👈 Please create a machine to begin analysis")
    st.stop()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Comparison Matrix",
    "🎛️ Create Scenario",
    "📈 Equity Curves",
    "🗓️ Heatmaps",
    "📉 Charts",
    "🕐 Time Analysis",
    "📊 Distribution",
    "🔍 Trade Details"
])

with tab1:
    st.header("Scenario Comparison Matrix")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available for this machine. Create scenarios in the 'Create Scenario' tab.")
    else:
        scenarios_for_comparison = [
            {
                'name': s['name'],
                'is_baseline': s['is_baseline'],
                'parameters': s['parameters'],
                'metrics': s['metrics'],
                'modified_trades': s['modified_trades']
            } for s in active_scenarios
        ]
        comparison_df = get_comparison_matrix(scenarios_for_comparison)
        
        st.subheader("Key Metrics Comparison")
        
        display_cols = ['scenario_name', 'total_pnl', 'win_rate', 'sharpe_ratio', 'profit_factor', 
                       'expectancy_r', 'risk_of_ruin', 'recovery_factor', 'max_drawdown', 
                       'trade_quality_score', 'total_trades']
        
        display_df = comparison_df[display_cols].copy()
        display_df.columns = ['Scenario', 'Total P&L', 'Win Rate %', 'Sharpe', 'Profit Factor',
                             'Expectancy (R)', 'Risk of Ruin %', 'Recovery Factor', 'Max DD', 
                             'Quality Score', 'Total Trades']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.subheader("Extended Metrics")
        extended_cols = ['scenario_name', 'avg_win', 'avg_loss', 'avg_win_duration', 'avg_loss_duration',
                        'win_streak', 'loss_streak', 'trades_per_day']
        
        extended_df = comparison_df[extended_cols].copy()
        extended_df.columns = ['Scenario', 'Avg Win', 'Avg Loss', 'Avg Win Duration (min)', 
                              'Avg Loss Duration (min)', 'Max Win Streak', 'Max Loss Streak', 'Trades/Day']
        
        st.dataframe(extended_df, use_container_width=True, hide_index=True)
        
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            "📥 Export Comparison Matrix (CSV)",
            csv,
            "scenario_comparison.csv",
            "text/csv",
            key='download_comparison'
        )
        
        st.subheader("Visual Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pnl = create_comparison_bar_chart(comparison_df, 'total_pnl', 'Total P&L Comparison')
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            fig_sharpe = create_comparison_bar_chart(comparison_df, 'sharpe_ratio', 'Sharpe Ratio Comparison')
            st.plotly_chart(fig_sharpe, use_container_width=True)

with tab2:
    st.header("Create What-If Scenario")
    
    baseline_count = len([s for s in active_scenarios if s['is_baseline']])
    additional_scenarios_count = len([s for s in active_scenarios if not s['is_baseline']])
    
    if additional_scenarios_count >= MAX_SCENARIOS:
        st.error(f"⚠️ Maximum {MAX_SCENARIOS} additional scenarios reached for this machine. Please delete a scenario to create a new one.")
    else:
        st.info(f"📊 Scenarios: {baseline_count} baseline + {additional_scenarios_count}/{MAX_SCENARIOS} additional")
        
        with st.form("scenario_form"):
            scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(active_scenarios)}")
            
            st.subheader("What-If Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_stop_loss = st.checkbox("Apply Stop Loss", help="Enable to apply stop loss to all trades")
                stop_loss_pct = st.slider("Stop Loss %", 0.5, 10.0, 2.0, 0.1)
                
                use_take_profit = st.checkbox("Apply Take Profit", help="Enable to apply take profit to all trades")
                take_profit_pct = st.slider("Take Profit %", 0.5, 20.0, 5.0, 0.5)
                
                use_min_hold = st.checkbox("Minimum Hold Time", help="Enable to set minimum holding period")
                min_hold_minutes = st.number_input("Min Hold (minutes)", 0, 1440, 0, 15)
                
                use_max_hold = st.checkbox("Maximum Hold Time", help="Enable to set maximum holding period")
                max_hold_minutes = st.number_input("Max Hold (minutes)", 15, 1440, 240, 15)
            
            with col2:
                exclude_days = st.multiselect(
                    "Exclude Trading Days",
                    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    default=[]
                )
                
                use_time_filter = st.checkbox("Limit Trading Hours")
                if use_time_filter:
                    time_col1, time_col2 = st.columns(2)
                    with time_col1:
                        trade_hours_start = st.number_input("Start Hour (24h)", 0, 23, 9, 1)
                    with time_col2:
                        trade_hours_end = st.number_input("End Hour (24h)", 0, 23, 16, 1)
                else:
                    trade_hours_start = None
                    trade_hours_end = None
                
                slippage_ticks = st.number_input("Slippage (ticks)", 0, 20, 0, 1, help="Slippage in ticks (0.25 per tick)")
                commission_per_contract = st.number_input("Commission ($ per contract)", 0.0, 50.0, 0.0, 0.5, help="Round-trip commission cost")
                
                use_position_limit = st.checkbox("Limit Concurrent Positions", help="Block new trades when position limit reached")
                max_concurrent_positions = st.number_input("Max Positions", 1, 10, 1, 1, help="Maximum number of trades open at the same time (1 = only one trade at a time)")
            
            st.subheader("Capital & Position Sizing")
            col3, col4 = st.columns(2)
            
            with col3:
                capital_allocation_pct = st.slider("Capital Allocation %", 10, 100, 40, 5)
                
                capital_multiplier = st.number_input(
                    "Capital Multiplier", 
                    min_value=0.1, 
                    max_value=10.0, 
                    value=1.0, 
                    step=0.1,
                    help="Multiply your capital to test larger/smaller position sizes. 2.0 = double capital & contracts, 0.5 = half"
                )
                st.caption(f"💡 Base Capital: ${active_machine['starting_capital']:,.0f} (will be multiplied by your value above)")
            
            with col4:
                mes_split_pct = st.slider("MES / MNQ Split % (MES)", 0, 100, 50, 10)
                st.caption(f"MES: {mes_split_pct}% | MNQ: {100-mes_split_pct}%")
            
            submitted = st.form_submit_button("🚀 Create & Run Scenario", use_container_width=True)
            
            if submitted:
                params = {
                    'stop_loss_pct': stop_loss_pct if use_stop_loss else None,
                    'take_profit_pct': take_profit_pct if use_take_profit else None,
                    'min_hold_minutes': min_hold_minutes if use_min_hold else None,
                    'max_hold_minutes': max_hold_minutes if use_max_hold else None,
                    'exclude_days': exclude_days,
                    'capital_allocation_pct': capital_allocation_pct,
                    'mes_split_pct': mes_split_pct,
                    'trade_hours_start': trade_hours_start if use_time_filter else None,
                    'trade_hours_end': trade_hours_end if use_time_filter else None,
                    'slippage_ticks': slippage_ticks,
                    'commission_per_contract': commission_per_contract,
                    'capital_multiplier': capital_multiplier,
                    'max_concurrent_positions': max_concurrent_positions if use_position_limit else None
                }
                
                trades_df = get_trades_for_machine(st.session_state.active_machine_id)
                
                mes_market_df = get_market_data('MES', active_machine['timeframe'])
                mnq_market_df = get_market_data('MNQ', active_machine['timeframe'])
                combined_market = pd.concat([mes_market_df, mnq_market_df])
                
                new_scenario = create_scenario(
                    scenario_name,
                    params,
                    trades_df,
                    combined_market,
                    active_machine['starting_capital']
                )
                
                from database import save_scenario
                scenario_id = save_scenario(
                    st.session_state.active_machine_id,
                    new_scenario['name'],
                    False,
                    new_scenario['parameters'],
                    new_scenario.get('metrics'),
                    new_scenario.get('modified_trades')
                )
                
                st.success(f"✅ Created scenario: {scenario_name}")
                st.rerun()

with tab3:
    st.header("Equity Curves")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in active_scenarios],
            key="equity_scenario"
        )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total P&L", f"${scenario['metrics']['total_pnl']:,.2f}")
            with col2:
                st.metric("Sharpe Ratio", f"{scenario['metrics']['sharpe_ratio']:.2f}")
            with col3:
                st.metric("Max Drawdown", f"${scenario['metrics']['max_drawdown']:,.2f}")
            with col4:
                st.metric("Recovery Factor", f"{scenario['metrics']['recovery_factor']:.2f}")
            
            scenario_trades = pd.DataFrame(scenario['modified_trades']) if scenario['modified_trades'] else pd.DataFrame()
            fig = create_equity_curve(scenario_trades, active_machine['starting_capital'], f"Equity Curve - {selected_scenario}")
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Performance Heatmaps")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in active_scenarios],
            key="heatmap_scenario"
        )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            trades_df = pd.DataFrame(scenario['modified_trades']) if scenario.get('modified_trades') else pd.DataFrame()
            
            if not trades_df.empty:
                st.subheader("Weekly P&L Heatmap")
                fig_weekly = create_weekly_pnl_heatmap(trades_df)
                st.plotly_chart(fig_weekly, use_container_width=True)
                
                st.subheader("Monthly Returns Grid")
                fig_monthly = create_monthly_returns_grid(trades_df)
                st.plotly_chart(fig_monthly, use_container_width=True)

with tab5:
    st.header("Price Charts with Trades")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_instrument = st.selectbox("Instrument:", ['MES', 'MNQ'], key="chart_instrument")
        
        with col2:
            selected_scenario = st.selectbox(
                "Scenario:",
                [s['name'] for s in active_scenarios],
                key="chart_scenario"
            )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            all_trades = pd.DataFrame(scenario['modified_trades']) if scenario.get('modified_trades') else pd.DataFrame()
            trades = all_trades[all_trades['instrument'] == selected_instrument] if not all_trades.empty else pd.DataFrame()
            
            market = get_market_data(selected_instrument, active_machine['timeframe'])
            
            if not market.empty:
                market['timestamp'] = pd.to_datetime(market['timestamp'])
                date_range = st.date_input(
                    "Date Range:",
                    value=(market['timestamp'].min().date(), market['timestamp'].max().date()),
                    key="chart_date_range"
                )
            else:
                st.warning(f"No market data available for {selected_instrument} on {active_machine['timeframe']} timeframe. Please generate market data first.")
                st.stop()
            
            if len(date_range) == 2:
                filtered_market = market[
                    (market['timestamp'].dt.date >= date_range[0]) &
                    (market['timestamp'].dt.date <= date_range[1])
                ]
                
                if not trades.empty:
                    filtered_trades = trades[
                        (pd.to_datetime(trades['entry_time']).dt.date >= date_range[0]) &
                        (pd.to_datetime(trades['entry_time']).dt.date <= date_range[1])
                    ]
                else:
                    filtered_trades = pd.DataFrame()
                
                fig = create_candlestick_chart(
                    filtered_market,
                    filtered_trades,
                    f"{selected_instrument} - {selected_scenario}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption(f"Showing {len(filtered_trades)} trades on {len(filtered_market)} candles")

with tab6:
    st.header("Time-of-Day Analysis")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in active_scenarios],
            key="time_scenario"
        )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            trades_df = pd.DataFrame(scenario['modified_trades']) if scenario.get('modified_trades') else pd.DataFrame()
            
            if not trades_df.empty:
                fig_time = create_time_of_day_heatmap(trades_df)
                st.plotly_chart(fig_time, use_container_width=True)
                
                st.subheader("Hourly Performance Table")
                hour_perf = get_time_of_day_performance(trades_df)
                if not hour_perf.empty:
                    st.dataframe(hour_perf, use_container_width=True, hide_index=True)

with tab7:
    st.header("Returns & R-Multiple Distribution")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in active_scenarios],
            key="dist_scenario"
        )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            trades_df = pd.DataFrame(scenario['modified_trades']) if scenario.get('modified_trades') else pd.DataFrame()
            
            if not trades_df.empty:
                st.subheader("Dollar Returns Distribution")
                fig_returns, return_stats = create_returns_distribution(trades_df, f"Returns Distribution - {selected_scenario}")
                st.plotly_chart(fig_returns, use_container_width=True)
                
                if return_stats:
                    st.subheader("Statistical Analysis")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Mean", f"${return_stats['mean']:.2f}")
                    with col2:
                        st.metric("Median", f"${return_stats['median']:.2f}")
                    with col3:
                        st.metric("Std Dev", f"${return_stats['std']:.2f}")
                    with col4:
                        st.metric("Skewness", f"{return_stats['skewness']:.3f}")
                    with col5:
                        st.metric("Kurtosis", f"{return_stats['kurtosis']:.3f}")
                    
                    col6, col7, col8 = st.columns(3)
                    with col6:
                        st.metric("Min", f"${return_stats['min']:.2f}")
                    with col7:
                        st.metric("Max", f"${return_stats['max']:.2f}")
                    with col8:
                        st.metric("Total Trades", f"{return_stats['count']}")
                
                st.divider()
                st.subheader("R-Multiple Distribution")
                fig_r = create_r_multiple_histogram(trades_df)
                st.plotly_chart(fig_r, use_container_width=True)
                
                if 'r_multiple' in trades_df.columns:
                    r_stats = trades_df['r_multiple'].describe()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Mean R", f"{r_stats['mean']:.2f}R")
                    with col2:
                        st.metric("Median R", f"{r_stats['50%']:.2f}R")
                    with col3:
                        st.metric("Max R", f"{r_stats['max']:.2f}R")
                    with col4:
                        st.metric("Min R", f"{r_stats['min']:.2f}R")

with tab8:
    st.header("Trade Details")
    
    if len(active_scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in active_scenarios],
            key="detail_scenario"
        )
        
        scenario = next((s for s in active_scenarios if s['name'] == selected_scenario), None)
        
        if scenario:
            trades_df = pd.DataFrame(scenario['modified_trades']) if scenario.get('modified_trades') else pd.DataFrame()
            
            if not trades_df.empty:
                st.subheader("All Trades")
                
                display_trades = trades_df.copy()
                display_trades['entry_time'] = pd.to_datetime(display_trades['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
                display_trades['exit_time'] = pd.to_datetime(display_trades['exit_time']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(display_trades, use_container_width=True, hide_index=True)
                
                csv_trades = display_trades.to_csv(index=False)
                st.download_button(
                    "📥 Download Trades CSV",
                    csv_trades,
                    f"{selected_scenario}_trades.csv",
                    "text/csv"
                )

st.sidebar.divider()
st.sidebar.caption("Trading What-If Analysis v2.0")
st.sidebar.caption("Machine-Based Architecture | Multi-Timeframe Support")
