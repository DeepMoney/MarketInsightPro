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
    create_comparison_bar_chart
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
                
                capital_allocation_pct = st.slider("Capital Allocation %", 10, 100, 40, 5)
                
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
                    'mes_split_pct': mes_split_pct
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
    st.header("R-Multiple Distribution")
    
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
            fig_r = create_r_multiple_histogram(scenario['trades'])
            st.plotly_chart(fig_r, use_container_width=True)
            
            st.subheader("R-Multiple Statistics")
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
