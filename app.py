import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

from data_generator import create_mock_data
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

MAX_SCENARIOS = 10

st.set_page_config(page_title="Trading What-If Analysis", layout="wide", initial_sidebar_state="expanded")

st.title("📊 Trading Portfolio What-If Analysis")
st.markdown("**Micro S&P 500 (MES) & Micro Nasdaq (MNQ) Futures Analysis**")

if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}
if 'trade_data' not in st.session_state:
    st.session_state.trade_data = {}
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'starting_capital' not in st.session_state:
    st.session_state.starting_capital = 50000

with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.session_state.starting_capital = st.number_input(
        "Starting Capital ($)", 
        min_value=10000, 
        max_value=1000000, 
        value=50000, 
        step=5000
    )
    
    st.divider()
    st.subheader("📁 Data Management")
    
    data_option = st.radio("Data Source:", ["Generate Mock Data", "Upload CSV Files"])
    
    if data_option == "Generate Mock Data":
        if st.button("🎲 Generate Mock Data", use_container_width=True):
            with st.spinner("Generating mock data... This may take a minute."):
                mock_data = create_mock_data()
                st.session_state.market_data = {
                    'MES': mock_data['MES_market'],
                    'MNQ': mock_data['MNQ_market']
                }
                st.session_state.trade_data = {
                    'MES': mock_data['MES_trades'],
                    'MNQ': mock_data['MNQ_trades']
                }
                st.session_state.data_loaded = True
                
                combined_trades = pd.concat([mock_data['MES_trades'], mock_data['MNQ_trades']])
                combined_market = pd.concat([mock_data['MES_market'], mock_data['MNQ_market']])
                
                baseline = create_baseline_scenario(combined_trades, st.session_state.starting_capital)
                st.session_state.scenarios = [baseline]
                
                st.success("✅ Mock data generated successfully!")
                st.rerun()
        
        if st.session_state.data_loaded:
            st.info(f"📊 Data loaded: {len(st.session_state.trade_data.get('MES', pd.DataFrame()))} MES trades, {len(st.session_state.trade_data.get('MNQ', pd.DataFrame()))} MNQ trades")
            
            if st.button("💾 Download Generated Data", use_container_width=True):
                st.write("Download CSVs:")
                for instrument in ['MES', 'MNQ']:
                    if instrument in st.session_state.market_data:
                        csv_market = st.session_state.market_data[instrument].to_csv(index=False)
                        st.download_button(
                            f"📥 {instrument}-market.csv",
                            csv_market,
                            f"{instrument}-2024-2025.csv",
                            "text/csv",
                            key=f"download_market_{instrument}"
                        )
                    
                    if instrument in st.session_state.trade_data:
                        csv_trades = st.session_state.trade_data[instrument].to_csv(index=False)
                        st.download_button(
                            f"📥 {instrument}-trades.csv",
                            csv_trades,
                            f"{instrument}-2024-2025-trades.csv",
                            "text/csv",
                            key=f"download_trades_{instrument}"
                        )
    
    else:
        st.write("Upload market and trade CSV files:")
        
        with st.expander("📥 Download CSV Templates", expanded=False):
            st.write("Download these templates to see the exact format required:")
            
            mes_market_template = pd.DataFrame({
                'timestamp': ['2024-07-01 09:30:00', '2024-07-01 09:45:00', '2024-07-01 10:00:00'],
                'open': [5500.25, 5502.50, 5505.00],
                'high': [5503.75, 5506.25, 5507.50],
                'low': [5499.50, 5501.00, 5503.75],
                'close': [5502.50, 5505.00, 5506.25],
                'volume': [1250, 1180, 1320],
                'instrument': ['MES', 'MES', 'MES']
            })
            
            mnq_market_template = pd.DataFrame({
                'timestamp': ['2024-07-01 09:30:00', '2024-07-01 09:45:00', '2024-07-01 10:00:00'],
                'open': [19500.50, 19510.25, 19520.00],
                'high': [19515.75, 19525.50, 19535.25],
                'low': [19495.00, 19505.75, 19515.50],
                'close': [19510.25, 19520.00, 19530.75],
                'volume': [2150, 2080, 2220],
                'instrument': ['MNQ', 'MNQ', 'MNQ']
            })
            
            mes_trades_template = pd.DataFrame({
                'trade_id': [1, 2],
                'instrument': ['MES', 'MES'],
                'direction': ['LONG', 'SHORT'],
                'entry_time': ['2024-07-01 10:00:00', '2024-07-01 14:30:00'],
                'exit_time': ['2024-07-01 11:15:00', '2024-07-01 15:45:00'],
                'entry_price': [5500.00, 5520.00],
                'exit_price': [5515.00, 5510.00],
                'contracts': [2, 2],
                'pnl': [150.00, 100.00],
                'initial_risk': [50.00, 50.00],
                'r_multiple': [3.0, 2.0],
                'holding_minutes': [75, 75],
                'entry_hour': [10, 14],
                'exit_hour': [11, 15],
                'outcome': ['Win', 'Win'],
                'stop_price': [5495.00, 5525.00]
            })
            
            mnq_trades_template = pd.DataFrame({
                'trade_id': [1, 2],
                'instrument': ['MNQ', 'MNQ'],
                'direction': ['LONG', 'SHORT'],
                'entry_time': ['2024-07-01 10:30:00', '2024-07-01 13:00:00'],
                'exit_time': ['2024-07-01 12:00:00', '2024-07-01 14:15:00'],
                'entry_price': [19500.00, 19550.00],
                'exit_price': [19550.00, 19525.00],
                'contracts': [1, 1],
                'pnl': [100.00, 50.00],
                'initial_risk': [50.00, 50.00],
                'r_multiple': [2.0, 1.0],
                'holding_minutes': [90, 75],
                'entry_hour': [10, 13],
                'exit_hour': [12, 14],
                'outcome': ['Win', 'Win'],
                'stop_price': [19450.00, 19575.00]
            })
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📄 MES Market Template",
                    mes_market_template.to_csv(index=False),
                    "MES_market_template.csv",
                    "text/csv",
                    key="template_mes_market"
                )
                st.download_button(
                    "📄 MES Trades Template",
                    mes_trades_template.to_csv(index=False),
                    "MES_trades_template.csv",
                    "text/csv",
                    key="template_mes_trades"
                )
            with col2:
                st.download_button(
                    "📄 MNQ Market Template",
                    mnq_market_template.to_csv(index=False),
                    "MNQ_market_template.csv",
                    "text/csv",
                    key="template_mnq_market"
                )
                st.download_button(
                    "📄 MNQ Trades Template",
                    mnq_trades_template.to_csv(index=False),
                    "MNQ_trades_template.csv",
                    "text/csv",
                    key="template_mnq_trades"
                )
            
            st.caption("💡 Tip: Download all 4 templates, replace the sample data with your real trading data, then upload them back.")
        
        st.divider()
        
        mes_market_file = st.file_uploader("MES Market Data", type=['csv'], key="mes_market")
        mnq_market_file = st.file_uploader("MNQ Market Data", type=['csv'], key="mnq_market")
        mes_trades_file = st.file_uploader("MES Trades Data", type=['csv'], key="mes_trades")
        mnq_trades_file = st.file_uploader("MNQ Trades Data", type=['csv'], key="mnq_trades")
        
        if st.button("📤 Load Uploaded Data", use_container_width=True):
            if all([mes_market_file, mnq_market_file, mes_trades_file, mnq_trades_file]):
                st.session_state.market_data = {
                    'MES': pd.read_csv(mes_market_file),
                    'MNQ': pd.read_csv(mnq_market_file)
                }
                st.session_state.trade_data = {
                    'MES': pd.read_csv(mes_trades_file),
                    'MNQ': pd.read_csv(mnq_trades_file)
                }
                st.session_state.data_loaded = True
                
                combined_trades = pd.concat([st.session_state.trade_data['MES'], st.session_state.trade_data['MNQ']])
                baseline = create_baseline_scenario(combined_trades, st.session_state.starting_capital)
                st.session_state.scenarios = [baseline]
                
                st.success("✅ Data loaded successfully!")
                st.rerun()
            else:
                st.error("⚠️ Please upload all 4 CSV files")
    
    st.divider()
    st.subheader("🎯 Scenario Management")
    
    num_scenarios = len(st.session_state.scenarios)
    st.metric("Active Scenarios", f"{num_scenarios}/{MAX_SCENARIOS}")
    
    if num_scenarios > 0:
        scenario_to_delete = st.selectbox(
            "Delete Scenario:",
            [s['name'] for s in st.session_state.scenarios if not s.get('is_baseline', False)],
            key="delete_scenario_select"
        )
        
        if scenario_to_delete and st.button("🗑️ Delete Selected Scenario", use_container_width=True):
            st.session_state.scenarios = [s for s in st.session_state.scenarios if s['name'] != scenario_to_delete]
            st.success(f"Deleted: {scenario_to_delete}")
            st.rerun()

if not st.session_state.data_loaded:
    st.info("👈 Please generate mock data or upload CSV files to begin analysis")
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
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available. Create scenarios in the 'Create Scenario' tab.")
    else:
        comparison_df = get_comparison_matrix(st.session_state.scenarios)
        
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
    
    if len(st.session_state.scenarios) >= MAX_SCENARIOS:
        st.error(f"⚠️ Maximum {MAX_SCENARIOS} scenarios reached. Please delete a scenario to create a new one.")
    else:
        st.info(f"📊 Scenarios: {len(st.session_state.scenarios)}/{MAX_SCENARIOS}")
        
        with st.form("scenario_form"):
            scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(st.session_state.scenarios)}")
            
            st.subheader("What-If Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_stop_loss = st.checkbox("Apply Stop Loss")
                stop_loss_pct = st.slider("Stop Loss %", 0.5, 10.0, 2.0, 0.1) if use_stop_loss else None
                
                use_take_profit = st.checkbox("Apply Take Profit")
                take_profit_pct = st.slider("Take Profit %", 0.5, 20.0, 5.0, 0.5) if use_take_profit else None
                
                use_min_hold = st.checkbox("Minimum Hold Time")
                min_hold_minutes = st.number_input("Min Hold (minutes)", 0, 1440, 0, 15) if use_min_hold else None
                
                use_max_hold = st.checkbox("Maximum Hold Time")
                max_hold_minutes = st.number_input("Max Hold (minutes)", 15, 1440, 240, 15) if use_max_hold else None
            
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
                st.caption(f"💡 Base Capital: ${st.session_state.starting_capital:,.0f} (will be multiplied by your value above)")
            
            with col4:
                mes_split_pct = st.slider("MES / MNQ Split % (MES)", 0, 100, 50, 10)
                st.caption(f"MES: {mes_split_pct}% | MNQ: {100-mes_split_pct}%")
            
            submitted = st.form_submit_button("🚀 Create & Run Scenario", use_container_width=True)
            
            if submitted:
                params = {
                    'stop_loss_pct': stop_loss_pct,
                    'take_profit_pct': take_profit_pct,
                    'min_hold_minutes': min_hold_minutes if use_min_hold else None,
                    'max_hold_minutes': max_hold_minutes if use_max_hold else None,
                    'exclude_days': exclude_days,
                    'capital_allocation_pct': capital_allocation_pct,
                    'mes_split_pct': mes_split_pct,
                    'trade_hours_start': trade_hours_start if use_time_filter else None,
                    'trade_hours_end': trade_hours_end if use_time_filter else None,
                    'slippage_ticks': slippage_ticks,
                    'commission_per_contract': commission_per_contract,
                    'capital_multiplier': capital_multiplier
                }
                
                combined_trades = pd.concat([st.session_state.trade_data['MES'], st.session_state.trade_data['MNQ']])
                combined_market = pd.concat([st.session_state.market_data['MES'], st.session_state.market_data['MNQ']])
                
                new_scenario = create_scenario(
                    scenario_name,
                    params,
                    combined_trades,
                    combined_market,
                    st.session_state.starting_capital
                )
                
                st.session_state.scenarios.append(new_scenario)
                st.success(f"✅ Created scenario: {scenario_name}")
                st.rerun()

with tab3:
    st.header("Equity Curves")
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in st.session_state.scenarios],
            key="equity_scenario"
        )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
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
            
            fig = create_equity_curve(scenario['trades'], st.session_state.starting_capital, f"Equity Curve - {selected_scenario}")
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Performance Heatmaps")
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in st.session_state.scenarios],
            key="heatmap_scenario"
        )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
        if scenario and not scenario['trades'].empty:
            st.subheader("Weekly P&L Heatmap")
            fig_weekly = create_weekly_pnl_heatmap(scenario['trades'])
            st.plotly_chart(fig_weekly, use_container_width=True)
            
            st.subheader("Monthly Returns Grid")
            fig_monthly = create_monthly_returns_grid(scenario['trades'])
            st.plotly_chart(fig_monthly, use_container_width=True)

with tab5:
    st.header("Price Charts with Trades")
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_instrument = st.selectbox("Instrument:", ['MES', 'MNQ'], key="chart_instrument")
        
        with col2:
            selected_scenario = st.selectbox(
                "Scenario:",
                [s['name'] for s in st.session_state.scenarios],
                key="chart_scenario"
            )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
        if scenario and selected_instrument in st.session_state.market_data:
            market = st.session_state.market_data[selected_instrument]
            trades = scenario['trades'][scenario['trades']['instrument'] == selected_instrument]
            
            market['timestamp'] = pd.to_datetime(market['timestamp'])
            date_range = st.date_input(
                "Date Range:",
                value=(market['timestamp'].min().date(), market['timestamp'].max().date()),
                key="chart_date_range"
            )
            
            if len(date_range) == 2:
                filtered_market = market[
                    (market['timestamp'].dt.date >= date_range[0]) &
                    (market['timestamp'].dt.date <= date_range[1])
                ]
                
                filtered_trades = trades[
                    (pd.to_datetime(trades['entry_time']).dt.date >= date_range[0]) &
                    (pd.to_datetime(trades['entry_time']).dt.date <= date_range[1])
                ]
                
                fig = create_candlestick_chart(
                    filtered_market,
                    filtered_trades,
                    f"{selected_instrument} - {selected_scenario}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption(f"Showing {len(filtered_trades)} trades on {len(filtered_market)} candles")

with tab6:
    st.header("Time-of-Day Analysis")
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in st.session_state.scenarios],
            key="time_scenario"
        )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
        if scenario and not scenario['trades'].empty:
            fig_time = create_time_of_day_heatmap(scenario['trades'])
            st.plotly_chart(fig_time, use_container_width=True)
            
            st.subheader("Hourly Performance Table")
            hour_perf = get_time_of_day_performance(scenario['trades'])
            if not hour_perf.empty:
                st.dataframe(hour_perf, use_container_width=True, hide_index=True)

with tab7:
    st.header("Returns & R-Multiple Distribution")
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in st.session_state.scenarios],
            key="dist_scenario"
        )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
        if scenario and not scenario['trades'].empty:
            st.subheader("Dollar Returns Distribution")
            fig_returns, return_stats = create_returns_distribution(scenario['trades'], f"Returns Distribution - {selected_scenario}")
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
            fig_r = create_r_multiple_histogram(scenario['trades'])
            st.plotly_chart(fig_r, use_container_width=True)
            
            if 'r_multiple' in scenario['trades'].columns:
                r_stats = scenario['trades']['r_multiple'].describe()
                
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
    
    if len(st.session_state.scenarios) == 0:
        st.warning("No scenarios available.")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario:",
            [s['name'] for s in st.session_state.scenarios],
            key="detail_scenario"
        )
        
        scenario = next((s for s in st.session_state.scenarios if s['name'] == selected_scenario), None)
        
        if scenario and not scenario['trades'].empty:
            st.subheader("All Trades")
            
            display_trades = scenario['trades'].copy()
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
st.sidebar.caption("Trading What-If Analysis v1.0")
st.sidebar.caption("MES & MNQ Futures | 15-Min Candles")
