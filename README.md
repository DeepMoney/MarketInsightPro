# MarketInsightPro

> Trading Portfolio What-If Analysis System

A comprehensive web-based financial analytics platform for traders and portfolio managers to analyze historical trading data, visualize performance metrics, and conduct scenario-based modeling to optimize trading strategies.

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Hierarchical Data Organization**: Markets → Instruments → Portfolios → Analytics
- **Full CRUD Management**: Create, Read, Update, Delete operations for all entities
- **CSV Import/Export**: Upload trade data and market data (OHLCV)
- **Scenario Modeling**: Conduct "what-if" analysis with configurable parameters
- **Performance Analytics**: Comprehensive trading metrics and visualizations
- **Real Contract Specifications**: Actual CME Group and Interactive Brokers margin requirements
- **Multi-Timeframe Support**: 5min, 15min, 30min, 1H, 4H, Daily
- **Interactive Visualizations**: Plotly-powered charts with zoom, pan, and hover

## Technology Stack

- **Frontend**: Streamlit 1.51.0
- **Backend**: Python 3.11+
- **Database**: PostgreSQL 14+
- **Data Processing**: Pandas, NumPy, SciPy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Deployment**: Docker-ready

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- pip or uv package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MarketInsightPro
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

4. Initialize the database:
```bash
# The database will be automatically initialized on first run
```

5. Run the application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:5000`

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t market-insight-pro:latest .

# Run with PostgreSQL
docker run -p 5000:5000 \
  -e PGHOST=your-db-host \
  -e PGPORT=5432 \
  -e PGDATABASE=trading_analytics \
  -e PGUSER=postgres \
  -e PGPASSWORD=your-password \
  market-insight-pro:latest
```

### Docker Compose

See [DEPLOYMENT.md](DEPLOYMENT.md) for full Docker Compose configuration with PostgreSQL.

## Project Structure

```
MarketInsightPro/
├── app.py                  # Main Streamlit application (1,260 lines)
├── database.py             # PostgreSQL database layer (1,339 lines)
├── analytics_engine.py     # Performance metrics calculations (352 lines)
├── scenario_engine.py      # What-if analysis logic (405 lines)
├── visualizations.py       # Plotly chart generation (455 lines)
├── data_generator.py       # Mock data & CSV parsing (216 lines)
├── portfolio_manager.py    # Portfolio management utilities (108 lines)
├── machine_manager.py      # Machine/portfolio state (109 lines)
├── primedoc.md            # Comprehensive design document
├── DEPLOYMENT.md          # Deployment guide
├── requirements.txt       # Python dependencies
├── Dockerfile            # Production container config
└── .streamlit/           # Streamlit configuration
    └── config.toml
```

## Database Schema

### Entity Relationship

```
Markets (Index Futures, MT5 Forex, Crypto)
   ↓ 1:N
Instruments (MES, MNQ, EUR/USD with timeframes)
   ↓ 1:N
Portfolios (Trading accounts/strategies)
   ↓ 1:N
Trades (Individual trade records)
```

### Key Tables

- **markets**: Trading venues and asset classes
- **instruments**: Tradable securities with contract specifications
- **portfolios**: Trading accounts with starting capital and status
- **trades**: Individual trade records with P&L
- **market_data**: OHLCV candlestick data
- **scenarios**: What-if analysis results

## Core Features

### 1. Market Management
- Create and manage trading markets (Index Futures, Forex, Crypto)
- Edit market details and descriptions
- Delete markets with cascade to instruments and portfolios

### 2. Instrument Management
- Define instruments with contract specifications
- Set tick values, margin requirements, and commissions
- Support multiple timeframes per instrument

### 3. Portfolio Management
- Create unlimited portfolios per instrument
- Track live vs simulated trading strategies
- Import trade data via CSV
- Calculate comprehensive performance metrics

### 4. Analytics Dashboard
- **Comparison Matrix**: Compare multiple portfolios side-by-side
- **Equity Curves**: Visualize cumulative P&L over time
- **Heatmaps**: Day-of-week vs hour performance analysis
- **Trade Distribution**: Histogram of P&L values
- **Performance Metrics**:
  - Win rate & profit factor
  - Sharpe ratio & Sortino ratio
  - Maximum drawdown
  - R-multiple distribution

### 5. Scenario Modeling
- Create up to 10 scenarios per portfolio
- Configure parameters:
  - Stop loss & take profit
  - Holding period limits
  - Day-of-week filters
  - Capital multipliers
- Compare scenarios against baseline

## Environment Variables

See `.env.example` for all configuration options:

```bash
# PostgreSQL Configuration
PGHOST=localhost
PGPORT=5432
PGDATABASE=trading_analytics
PGUSER=postgres
PGPASSWORD=your-password

# Application Settings
SESSION_SECRET=your-random-secret-key
```

## Documentation

- [primedoc.md](primedoc.md) - Comprehensive design and requirements document
- [DEPLOYMENT.md](DEPLOYMENT.md) - Cloud deployment guide (AWS, GCP, Azure)
- [replit.md](replit.md) - Replit-specific setup instructions

## Development

### Running Tests

```bash
# Tests not yet implemented
# TODO: Add pytest configuration
```

### Code Style

The project follows a modular architecture with clear separation of concerns:
- Database layer (`database.py`)
- Analytics engine (`analytics_engine.py`)
- Visualization engine (`visualizations.py`)
- Scenario engine (`scenario_engine.py`)
- Frontend layer (`app.py`)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

### Planned Features
- [ ] Multi-user support with authentication
- [ ] Real-time data integration
- [ ] Machine learning pattern recognition
- [ ] REST API for programmatic access
- [ ] Mobile-responsive UI
- [ ] PDF/Excel report generation
- [ ] Automated strategy backtesting
- [ ] Alert system (email/SMS)

### Technical Improvements
- [ ] Add comprehensive unit tests (pytest)
- [ ] Implement Redis caching
- [ ] Add Celery for background jobs
- [ ] Set up CI/CD pipeline
- [ ] Add GraphQL API option

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Review the documentation in `primedoc.md`
- Check deployment guide in `DEPLOYMENT.md`

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Contract specifications from [CME Group](https://www.cmegroup.com/)
- Margin requirements from [Interactive Brokers](https://www.interactivebrokers.com/)

---

**Version**: 1.0
**Last Updated**: November 19, 2025
**Status**: Active Development
