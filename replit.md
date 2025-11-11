# Trading Portfolio What-If Analysis System

## Overview

This is a trading analytics and scenario modeling application designed for analyzing Micro S&P 500 (MES) and Micro Nasdaq (MNQ) futures trading performance. The system enables traders to evaluate historical trading data, visualize performance metrics, and run "what-if" scenarios to optimize trading strategies. Built with Streamlit for the frontend and pandas/numpy for data processing, it provides comprehensive performance analytics and interactive visualizations.

**Status**: Production-ready with capital multiplier and UI fixes (November 11, 2025)

## Recent Changes

### November 11, 2025 - Capital Multiplier Feature and Critical Bug Fixes

**Capital Multiplier (11th What-If Parameter):**
- Added capital_multiplier parameter (0.1x to 10.0x range) for testing "what if I had more/less capital" scenarios
- Automatically scales contract quantities based on hypothetical capital amounts
- 2.0x multiplier doubles capital → doubles contracts → approximately doubles P&L
- Enables projection of strategy performance at different account sizes
- UI: Number input in "Capital & Position Sizing" section with helpful caption showing base capital

**Capital Allocation Bug Fix (Critical):**
- Fixed discrepancy between data_generator.py and scenario_engine.py capital allocation logic
- Previously: Data generator allocated capital to each instrument independently (double-counting)
- Now: Both modules use same formula: `capital_for_trade = starting_capital × allocation_pct × instrument_split_pct`
- Ensures capital multiplier scales P&L correctly and predictably
- Default 50/50 MES/MNQ split with 40% total allocation results in consistent contract sizing

**Slider UI Bug Fix:**
- Fixed issue where Stop Loss, Take Profit, and other parameter sliders didn't appear on first scenario creation
- Root cause: Streamlit forms don't re-render on checkbox state changes
- Solution: All sliders now always visible and interactive from the start
- Checkboxes control whether slider values are applied to scenario (not visibility)
- Improved UX: Users can configure all parameters upfront, then toggle which to apply

### November 6, 2025 - New What-If Parameters and Enhanced Analytics

**Time-of-Day Filtering (8th What-If Parameter):**
- Added trade_hours_start and trade_hours_end parameters to scenario engine
- Filters trades based on entry time hour (24-hour format)
- Supports standard intraday ranges (e.g., 10:00-14:00) and overnight ranges
- UI controls: "Limit Trading Hours" checkbox with Start/End hour inputs
- Enables testing strategies like "trade only during morning session"

**Slippage and Commission Parameters (9th & 10th What-If Parameters):**
- Added configurable slippage in ticks (0.25 per tick for MES/MNQ)
- Added round-trip commission cost per contract
- Slippage applied to both entry and exit prices (opposite directions for Long/Short)
- Commission applied as total round-trip cost (entry + exit)
- Trade fields track slippage_cost and commission_cost separately
- Enables realistic modeling of transaction costs impact on strategy performance

**Returns Distribution Visualization:**
- Comprehensive dollar P&L histogram with 40 bins and color-coded bars (red=loss, green=win)
- Statistical analysis: Mean, Median, Standard Deviation, Skewness, Kurtosis, Min/Max, Count
- Mean and Median lines overlaid on histogram for visual reference
- Integrated into Distribution tab alongside existing R-Multiple histogram
- Uses scipy.stats for advanced statistical metrics

**Earlier Bug Fixes (Production Release):**
- Added instrument-specific filtering in `simulate_trade_exit` to properly handle MES and MNQ trades separately
- Fixed exit reason labeling to correctly distinguish between "Max Hold Time" forced exits and "Original Exit" unmodified trades
- Implemented original exit price preservation - when no stop-loss or take-profit triggers hit, trades now correctly return their original exit prices
- Added intraperiod high/low checking for accurate stop-loss and take-profit triggering within 15-minute candles
- Added `total_trades` metric to comparison matrix display columns
- Fixed commission double-counting bug (was multiplying by 2 incorrectly)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Frontend Framework**: Streamlit-based web application with session state management for maintaining user data and scenarios across interactions. The main application (`app.py`) orchestrates the user interface and coordinates between data generation, analytics, scenario modeling, and visualization components.

**Modular Design Pattern**: The codebase follows a separation of concerns architecture with distinct modules:
- `data_generator.py` - Handles market data and trade data generation
- `analytics_engine.py` - Calculates performance metrics and statistical analysis
- `scenario_engine.py` - Implements what-if scenario modeling and trade modifications
- `visualizations.py` - Creates interactive charts and graphs using Plotly

**Rationale**: This modular approach allows independent development and testing of each component, making the system easier to maintain and extend. Each module has a clear responsibility boundary.

### Data Processing Architecture

**DataFrame-Centric Processing**: Uses pandas DataFrames as the primary data structure for both market data (OHLCV candlesticks) and trade records. All data transformations and calculations are performed using vectorized pandas operations.

**Time-Series Data Model**: Market data is stored as 15-minute interval candlesticks with timestamps, supporting intraday trading analysis. Trade data includes entry/exit times, prices, directions (Long/Short), and calculated PnL metrics.

**Rationale**: Pandas provides efficient vectorized operations for financial time-series data and integrates seamlessly with NumPy for statistical calculations. This approach is industry-standard for quantitative trading analysis.

### Session State Management

**Streamlit Session State**: Persistent storage of application state including:
- `scenarios` - List of configured what-if scenarios
- `market_data` - Generated or uploaded OHLCV data
- `trade_data` - Historical trade records
- `starting_capital` - User-configured initial capital
- `data_loaded` - Flag to track data availability

**Rationale**: Streamlit's session state enables multi-page interactions and scenario comparisons without requiring a backend database for temporary analysis sessions.

### Analytics Engine Design

**Metrics Calculation System**: Computes 16+ trading performance metrics including:
- Win rate and profit factor
- Expectancy (dollar and R-multiple based)
- Average win/loss statistics
- Equity curve generation
- Time-based performance analysis (time of day, weekly patterns)
- R-multiple distribution analysis

**Statistical Analysis**: Uses SciPy for statistical calculations and NumPy for mathematical operations. The system calculates both absolute dollar metrics and risk-adjusted metrics (R-multiples).

**Rationale**: Comprehensive metrics provide traders with multiple perspectives on strategy performance, supporting data-driven decision making.

### Scenario Modeling System

**What-If Scenario Engine**: Allows users to create up to 10 scenarios with configurable parameters:
- Stop loss and take profit percentages
- Minimum/maximum holding periods
- Day-of-week filters
- Capital allocation splits between MES and MNQ
- Position sizing adjustments

**Baseline Comparison**: Establishes a baseline scenario from original trade data, enabling comparative analysis of modified strategies against actual performance.

**Trade Modification Logic**: Applies scenario parameters to historical trades, recalculating PnL based on hypothetical exit rules and filters. The system respects market data constraints when simulating modified exits.

**Rationale**: This approach enables backtesting of strategy variations without requiring actual trading or complex backtesting infrastructure. Traders can quickly evaluate "what if I had used different exit rules" scenarios.

### Visualization Architecture

**Plotly-Based Charting**: All visualizations use Plotly for interactive, professional-grade charts:
- Candlestick charts with trade markers
- Equity curves
- Heatmaps (weekly PnL, time-of-day performance)
- Histograms (R-multiple distribution)
- Comparison bar charts for scenario analysis

**Chart Design Philosophy**: Clean, minimal visualizations focusing on actionable data. Candlestick charts intentionally exclude technical indicators to reduce noise.

**Rationale**: Plotly provides interactive charts with hover details, zoom capabilities, and professional aesthetics suitable for trading analysis. The library integrates well with Streamlit and pandas DataFrames.

### Data Generation System

**Mock Data Generator**: Creates realistic synthetic market data and trade records for testing and demonstration:
- Generates 15-minute OHLCV bars with configurable volatility
- Simulates market hours (9:30 AM - 4:00 PM, weekdays only)
- Creates random walk price movements with realistic intraday patterns
- Generates trade records with varied outcomes and holding periods

**Rationale**: Enables users to explore the system without requiring real trading data, supporting demos and testing scenarios.

## External Dependencies

### Core Python Libraries

**Pandas**: DataFrame operations, time-series analysis, and data manipulation. Used extensively throughout all modules for data processing.

**NumPy**: Mathematical operations, random number generation, and array computations. Powers the statistical calculations and data generation algorithms.

**SciPy**: Statistical analysis functions (scipy.stats) used in the analytics engine for advanced metrics calculation.

**Streamlit**: Web application framework providing the user interface, session management, and interactive widgets. The primary frontend technology.

**Plotly**: Interactive charting library (plotly.graph_objects and plotly.express) for all visualizations.

### Data Storage

**No Database**: The application currently operates entirely in-memory using Streamlit session state and pandas DataFrames. No persistent storage layer is implemented.

**Future Consideration**: The architecture could accommodate a database (such as PostgreSQL with Drizzle ORM) for persistent storage of scenarios, trade history, and user configurations if needed for multi-user deployments.

### External Services

**No External APIs**: The current implementation is self-contained with no external service dependencies. All market data is either generated synthetically or uploaded by users.

**Potential Integrations**: The architecture could support integration with:
- Market data providers (e.g., Alpha Vantage, IEX Cloud) for real price data
- Brokerage APIs for importing actual trade history
- Cloud storage for scenario backup/sharing

### Deployment Environment

**Replit Compatibility**: Designed to run in Replit's Python environment with standard scientific computing libraries. Uses Streamlit's built-in server for deployment.