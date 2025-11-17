# Trading Portfolio What-If Analysis System

## Overview

This system is a trading analytics and scenario modeling application for Micro S&P 500 (MES) and Micro Nasdaq (MNQ) futures. It allows traders to analyze historical data, visualize performance, and run "what-if" scenarios to optimize strategies. The application is built with Streamlit for the frontend and pandas/numpy for data processing, offering comprehensive analytics and interactive visualizations. It is designed to be production-ready and supports a machine-based architecture with PostgreSQL persistence for various trading accounts and strategies.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The application uses Streamlit for its frontend, orchestrating data generation, analytics, scenario modeling, and visualization. It follows a modular design pattern with distinct components: `data_generator.py` for data handling, `analytics_engine.py` for performance metrics, `scenario_engine.py` for what-if modeling, and `visualizations.py` for interactive charts. This modularity ensures independent development, testing, and ease of maintenance.

### System Design Choices

The system employs a hierarchical architecture with Market Data feeding into multiple "Machines" (representing trading accounts/strategies), each with its own "Scenarios." Machines are color-coded for live (green) or simulated (gray) status. Full PostgreSQL integration provides persistent storage for machines, trades, market data, scenarios, and scenario results, with proper indexing for efficient data retrieval. Multi-timeframe support allows machines to operate on various timeframes (5min, 15min, 30min, 1hr, 4hr, daily), with market data generated and shared across all timeframes.

### UI/UX Decisions

New UI components include a machine creator modal, a sidebar for selecting the active machine, and machine management features. All tabs (Comparison Matrix, Create Scenario, Equity Curves, Heatmaps, Charts, Time Analysis, Distribution, Trade Details) are machine-aware. The UI also incorporates a capital multiplier (0.1x to 10.0x) and a max concurrent positions parameter for advanced scenario testing. Slider UI elements are always visible, with checkboxes controlling their application, improving user experience.

### Technical Implementations

The core data processing relies on pandas DataFrames for market (OHLCV) and trade records, utilizing vectorized operations for efficiency. The analytics engine calculates over 16 performance metrics using pandas, NumPy, and SciPy. The scenario modeling system allows users to create up to 10 what-if scenarios with configurable parameters like stop loss, take profit, holding periods, day-of-week filters, capital allocation, and position sizing adjustments, comparing them against a baseline. Visualizations are built using Plotly, providing interactive charts with a clean, minimal design philosophy. A mock data generator creates synthetic market data for testing and demonstrations.

## External Dependencies

### Core Python Libraries

- **Pandas**: Data manipulation, DataFrame operations, time-series analysis.
- **NumPy**: Mathematical operations, array computations, random number generation.
- **SciPy**: Statistical analysis functions (e.g., `scipy.stats`).
- **Streamlit**: Web application framework for the user interface.
- **Plotly**: Interactive charting library for all visualizations.

### Data Storage

- **PostgreSQL**: Integrated for persistent storage of `machines`, `trades`, `market_data`, `scenarios`, and `scenario_results` tables. Configured via `DATABASE_URL` environment variable.

### External Services

The application is currently self-contained and does not rely on external APIs.

### Deployment Environment

- **Replit**: Designed to run within Replit's Python environment.