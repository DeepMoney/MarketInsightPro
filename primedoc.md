# Trading Portfolio What-If Analysis System
## Design and Requirements Document

**Version:** 1.0  
**Last Updated:** November 19, 2025  
**Project Type:** Web-based Financial Analytics Platform  
**Technology Stack:** Python, Streamlit, PostgreSQL

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Goals](#project-goals)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [System Architecture](#system-architecture)
6. [Database Design](#database-design)
7. [User Interface Design](#user-interface-design)
8. [Feature Specifications](#feature-specifications)
9. [Technology Stack](#technology-stack)
10. [Deployment Requirements](#deployment-requirements)

---

## Executive Summary

The Trading Portfolio What-If Analysis System is a comprehensive investor platform designed for market and portfolio analysis with hierarchical organization. The system provides traders and portfolio managers with tools to analyze historical trading data, visualize performance metrics, and conduct scenario-based modeling to optimize trading strategies.

The platform supports multiple markets (Index Futures, MT5 Forex, Crypto), multiple instruments with various timeframes, and unlimited portfolios, enabling users to manage diverse trading strategies across different asset classes.

---

## Project Goals

### Primary Objectives
1. **Hierarchical Data Organization**: Implement Markets → Instruments → Portfolios → Analytics navigation structure
2. **Full CRUD Management**: Provide complete Create, Read, Update, Delete operations for all entities
3. **Data Import/Export**: Support CSV-based data import for both trade data and market data (OHLCV)
4. **Scenario Modeling**: Enable "what-if" analysis with configurable parameters for strategy optimization
5. **Performance Analytics**: Calculate comprehensive trading metrics and visualize results
6. **Real Contract Specifications**: Use actual CME Group and Interactive Brokers margin requirements

### Secondary Objectives
1. Deploy to cloud infrastructure (AWS/other) via Docker
2. Support multi-timeframe analysis (5min, 15min, 30min, 1H, 4H, Daily)
3. Provide interactive visualizations with Plotly
4. Ensure data persistence with PostgreSQL
5. Enable safe data operations with confirmation dialogs

---

## Functional Requirements

### FR-1: Market Management
- **FR-1.1**: Users shall create new markets with unique IDs, names, and descriptions
- **FR-1.2**: Users shall edit existing market names and descriptions
- **FR-1.3**: Users shall delete markets (with cascade delete of associated instruments and portfolios)
- **FR-1.4**: Users shall view all markets in a card-based interface
- **FR-1.5**: System shall prevent duplicate market IDs and names
- **FR-1.6**: System shall display market statistics (instrument count, portfolio count)

### FR-2: Instrument Management
- **FR-2.1**: Users shall create instruments with symbol, timeframe, and contract specifications
- **FR-2.2**: Instrument IDs shall follow format: SYMBOL or SYMBOL_TIMEFRAME (e.g., MES, MES_5min)
- **FR-2.3**: Users shall edit instrument details (name, symbol, specs)
- **FR-2.4**: Users shall delete instruments (with cascade delete of associated portfolios)
- **FR-2.5**: System shall store contract specifications: tick value, margin requirements, commission
- **FR-2.6**: System shall filter instruments by selected market
- **FR-2.7**: System shall prevent duplicate instrument IDs

### FR-3: Portfolio Management
- **FR-3.1**: Users shall create portfolios with name, starting capital, and status (live/simulated)
- **FR-3.2**: Users shall edit portfolio details
- **FR-3.3**: Users shall delete portfolios (with confirmation)
- **FR-3.4**: System shall assign unique UUIDs to portfolios
- **FR-3.5**: System shall support unlimited portfolios per instrument
- **FR-3.6**: System shall display portfolio statistics (trade count, P&L, status)

### FR-4: Data Import/Export
- **FR-4.1**: Users shall upload trade data via CSV with required columns: instrument, direction, entry_time, exit_time, entry_price, exit_price, pnl
- **FR-4.2**: System shall auto-calculate optional fields: holding_minutes, r_multiple, outcome
- **FR-4.3**: Users shall upload market data (OHLCV) via CSV
- **FR-4.4**: Users shall delete all trades for a portfolio (with confirmation)
- **FR-4.5**: System shall validate CSV format and show clear error messages
- **FR-4.6**: System shall provide success feedback with record counts

### FR-5: Analytics and Visualization
- **FR-5.1**: System shall calculate performance metrics: win rate, profit factor, Sharpe ratio, max drawdown, etc.
- **FR-5.2**: System shall display equity curves with interactive Plotly charts
- **FR-5.3**: System shall show trade distribution histograms
- **FR-5.4**: System shall provide comparison matrices for multiple portfolios
- **FR-5.5**: System shall generate heatmaps for time-based analysis
- **FR-5.6**: System shall display individual trade details in tabular format

### FR-6: Scenario Modeling
- **FR-6.1**: Users shall create up to 10 scenario variations per portfolio
- **FR-6.2**: Scenario parameters shall include: stop loss, take profit, holding period, day-of-week filters, capital multiplier
- **FR-6.3**: System shall compare scenarios against baseline performance
- **FR-6.4**: System shall save scenario results to database
- **FR-6.5**: System shall visualize scenario performance with comparison charts

### FR-7: Safety and Validation
- **FR-7.1**: System shall show confirmation dialogs for all delete operations
- **FR-7.2**: System shall validate required fields in all forms
- **FR-7.3**: System shall prevent duplicate entries
- **FR-7.4**: System shall show clear success/error messages
- **FR-7.5**: System shall maintain data integrity with CASCADE constraints

---

## Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1**: Page load time shall be under 3 seconds
- **NFR-1.2**: Analytics calculations shall complete within 5 seconds for datasets up to 10,000 trades
- **NFR-1.3**: Database queries shall use proper indexing for efficient retrieval

### NFR-2: Usability
- **NFR-2.1**: UI shall follow Streamlit best practices with clean, minimal design
- **NFR-2.2**: Navigation shall be intuitive with clear back buttons
- **NFR-2.3**: Forms shall provide inline validation and helpful error messages
- **NFR-2.4**: Charts shall be interactive with zoom, pan, and hover capabilities

### NFR-3: Reliability
- **NFR-3.1**: System shall handle database connection failures gracefully
- **NFR-3.2**: System shall validate all user inputs before database operations
- **NFR-3.3**: System shall use transaction management for data consistency

### NFR-4: Scalability
- **NFR-4.1**: System shall support 100+ portfolios without performance degradation
- **NFR-4.2**: Database schema shall support efficient queries with proper foreign keys
- **NFR-4.3**: System shall handle CSV imports of 10,000+ rows

### NFR-5: Maintainability
- **NFR-5.1**: Code shall be modular with separate files for database, analytics, visualization, and data generation
- **NFR-5.2**: Database migrations shall be idempotent
- **NFR-5.3**: Code shall include error handling and logging

### NFR-6: Security
- **NFR-6.1**: Database credentials shall use environment variables
- **NFR-6.2**: SQL queries shall use parameterized statements to prevent injection
- **NFR-6.3**: Destructive operations shall require explicit confirmation

---

## System Architecture

### Architecture Pattern
The system follows a **modular monolithic architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│                        (app.py)                          │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Database    │    │  Analytics   │    │Visualization │
│   Layer      │    │   Engine     │    │   Engine     │
│(database.py) │    │(analytics.py)│    │(viz.py)      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │Data Generator│
│   Database   │    │(data_gen.py) │
└──────────────┘    └──────────────┘
```

### Component Descriptions

**1. Frontend Layer (app.py)**
- Streamlit-based UI with hierarchical navigation
- Session state management
- Form handling and validation
- CRUD operation triggers

**2. Database Layer (database.py)**
- PostgreSQL connection management
- CRUD operations for all entities
- Data seeding and migration functions
- Query optimization with proper indexing

**3. Analytics Engine (analytics_engine.py)**
- Performance metric calculations
- Statistical analysis (Sharpe ratio, Sortino ratio)
- Drawdown analysis
- Trade classification

**4. Visualization Engine (visualizations.py)**
- Plotly chart generation
- Equity curves, heatmaps, distributions
- Interactive chart configurations

**5. Scenario Engine (scenario_engine.py)**
- What-if analysis logic
- Parameter application
- Scenario comparison
- Results storage

**6. Data Generator (data_generator.py)**
- Mock market data generation (OHLCV)
- Mock trade data generation
- CSV parsing and validation

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────┐
│   markets   │
│─────────────│
│ id (PK)     │
│ name        │
│ description │
└─────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│   instruments    │
│──────────────────│
│ id (PK)          │
│ market_id (FK)   │──────┐
│ symbol           │      │
│ timeframe        │      │
│ name             │      │
│ tick_value       │      │
│ margin           │      │
│ commission       │      │
└──────────────────┘      │
       │                  │
       │ 1:N              │
       ▼                  │
┌──────────────────┐      │
│   portfolios     │      │
│──────────────────│      │
│ id (PK)          │      │
│ instrument_id(FK)│──────┘
│ name             │
│ starting_capital │
│ status           │
│ created_at       │
└──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│     trades       │
│──────────────────│
│ id (PK)          │
│ machine_id (FK)  │─────→ portfolios.id
│ instrument       │
│ direction        │
│ entry_time       │
│ exit_time        │
│ entry_price      │
│ exit_price       │
│ pnl              │
│ holding_minutes  │
│ r_multiple       │
└──────────────────┘
```

### Table Schemas

**markets**
```sql
CREATE TABLE markets (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);
```

**instruments**
```sql
CREATE TABLE instruments (
    id VARCHAR(50) PRIMARY KEY,
    market_id VARCHAR(50) REFERENCES markets(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tick_value DECIMAL(10,2),
    margin_requirement DECIMAL(10,2),
    commission_per_contract DECIMAL(10,2)
);
```

**portfolios**
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id VARCHAR(50) REFERENCES instruments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    starting_capital DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'simulated',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**trades**
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    machine_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    instrument VARCHAR(10),
    direction VARCHAR(10),
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    entry_price DECIMAL(15,4),
    exit_price DECIMAL(15,4),
    pnl DECIMAL(15,2),
    holding_minutes INTEGER,
    r_multiple DECIMAL(10,2)
);
```

### Cascade Delete Strategy
- Deleting a **Market** cascades to all **Instruments** and **Portfolios**
- Deleting an **Instrument** cascades to all **Portfolios**
- Deleting a **Portfolio** cascades to all **Trades**

---

## User Interface Design

### Navigation Hierarchy

```
Markets View (Landing)
    ├─→ [View] → Instruments View (filtered by market)
    │               ├─→ [View Portfolios] → Portfolios View
    │               │                          ├─→ [Analytics] → Analytics View
    │               │                          │                     ├─ Tabs: Comparison, Scenarios, Curves, etc.
    │               │                          │                     └─ Sidebar: Data Management
    │               │                          ├─→ [← Back] → Portfolios View
    │               │                          └─→ [Create/Edit/Delete Portfolio]
    │               ├─→ [← Back] → Instruments View
    │               └─→ [Create/Edit/Delete Instrument]
    ├─→ [← Markets] → Markets View
    └─→ [Create/Edit/Delete Market]
```

### UI Components

**1. Market Cards**
- Visual card-based layout
- Display: market name, description, instrument count
- Actions: View, Edit, Delete

**2. Instrument List**
- Tabular display with columns: ID, Symbol, Timeframe, Margin
- Actions: Edit, Delete (icon buttons)
- Create button in sidebar

**3. Portfolio List**
- Card-based layout
- Display: name, capital, status, trade count
- Actions: Analytics, Edit, Delete

**4. Analytics Tabs**
- Tab navigation for different analysis views
- Interactive Plotly charts
- Expandable data management section

**5. Forms**
- Inline validation
- Required field indicators
- Clear submit/cancel buttons
- Success/error messaging

**6. Confirmation Dialogs**
- Warning message with entity name
- Two-button choice: "Yes, Delete" / "Cancel"
- Modal overlay style

---

## Feature Specifications

### Feature 1: Market CRUD Operations

**Create Market**
- Input: Market ID (alphanumeric, unique), Name (unique), Description (optional)
- Validation: Check for duplicates, required fields
- Success: Create market record, show success message, refresh view
- Error: Display specific error message

**Edit Market**
- Pre-fill form with existing values
- Allow editing name and description (ID immutable)
- Validation: Check name uniqueness
- Success: Update record, show success message

**Delete Market**
- Show confirmation dialog with market name
- On confirm: Delete market and cascade to instruments/portfolios
- Success: Remove from list, show count of deleted items

### Feature 2: Instrument CRUD Operations

**Create Instrument**
- Input: Symbol, Timeframe, Contract specs (tick value, margin, commission)
- Auto-generate ID: SYMBOL for 15min, SYMBOL_TIMEFRAME for others
- Assign to current market
- Validation: Duplicate ID check
- Success: Create record, refresh instrument list

**Edit Instrument**
- Pre-fill all fields
- Allow editing all fields except ID and market_id
- Success: Update record

**Delete Instrument**
- Confirmation required
- Cascade to portfolios
- Success: Remove from list

### Feature 3: Portfolio CRUD Operations

**Create Portfolio**
- Input: Name, Starting Capital, Status (live/simulated), Description
- Auto-assign UUID
- Optional: Upload trade data CSV
- Success: Create portfolio, import trades if provided

**Edit Portfolio**
- Pre-fill form
- Allow editing name, capital, status, description
- Warning: Changing capital affects scenario calculations
- Success: Update record

**Delete Portfolio**
- Confirmation required
- Cascade to trades and scenarios
- Success: Remove from list

### Feature 4: CSV Data Import

**Trade Data Import**
- Required columns: instrument, direction, entry_time, exit_time, entry_price, exit_price, pnl
- Optional columns: holding_minutes, r_multiple
- Auto-calculate missing fields
- Validation: Column presence, data types
- Success: Bulk insert, show record count

**Market Data Import**
- Required columns: timestamp, open, high, low, close, volume
- Associate with current portfolio
- Success: Insert candles, show count

### Feature 5: Analytics Dashboard

**Comparison Matrix**
- Display all portfolios in current instrument
- Metrics: Win rate, profit factor, Sharpe ratio, max drawdown, etc.
- Sortable columns
- Color coding for performance

**Equity Curves**
- Plot cumulative P&L over time
- Multiple portfolios overlaid
- Interactive zoom/pan
- Hover tooltips with details

**Heatmaps**
- Day-of-week vs hour performance
- Color gradient from red (loss) to green (profit)
- Show average P&L per cell

**Trade Distribution**
- Histogram of P&L values
- Win/loss coloring
- Statistical overlays

### Feature 6: Scenario Modeling

**Create Scenario**
- Name scenario
- Configure parameters:
  - Stop loss (% or $)
  - Take profit (% or $)
  - Holding period (max minutes)
  - Day-of-week filter
  - Capital multiplier
  - Position sizing adjustment
- Apply to baseline trades
- Calculate modified results
- Save to database

**Scenario Comparison**
- Compare up to 10 scenarios
- Side-by-side metrics
- Equity curve overlay
- Highlight best/worst performers

---

## Technology Stack

### Backend
- **Python 3.11+**: Core programming language
- **Streamlit 1.x**: Web application framework
- **PostgreSQL 14+**: Relational database
- **psycopg2-binary**: PostgreSQL adapter

### Data Processing
- **Pandas**: DataFrame operations, time-series analysis
- **NumPy**: Mathematical operations, array computations
- **SciPy**: Statistical functions (scipy.stats)

### Visualization
- **Plotly**: Interactive charts and graphs
- **Matplotlib**: Supplementary plotting (if needed)
- **Seaborn**: Statistical visualizations (if needed)

### Environment
- **python-dotenv**: Environment variable management
- **Replit**: Development and hosting platform
- **Docker** (future): Containerization for cloud deployment

### Version Control
- **Git**: Source code management
- **GitHub**: Repository hosting

---

## Deployment Requirements

### Environment Variables
```
DATABASE_URL=postgresql://user:password@host:port/database
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=password
PGDATABASE=trading_analytics
SESSION_SECRET=random_secret_key
```

### System Requirements
- **RAM**: Minimum 2GB, Recommended 4GB
- **Storage**: Minimum 1GB for application + database
- **CPU**: 2+ cores recommended for concurrent users

### Docker Deployment

**Dockerfile Example**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]
```

**Docker Compose with PostgreSQL**
```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_analytics
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  app:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/trading_analytics

volumes:
  postgres_data:
```

### Cloud Deployment Options

**AWS Deployment**
- **Compute**: ECS Fargate or EC2 instance
- **Database**: RDS PostgreSQL
- **Storage**: S3 for backup exports
- **Load Balancer**: Application Load Balancer for HTTPS

**Azure Deployment**
- **Compute**: Azure Container Instances or App Service
- **Database**: Azure Database for PostgreSQL
- **Storage**: Azure Blob Storage

**Google Cloud Deployment**
- **Compute**: Cloud Run or GKE
- **Database**: Cloud SQL for PostgreSQL
- **Storage**: Cloud Storage

### Monitoring and Logging
- Application logs via Streamlit console
- Database query logging
- Performance monitoring with APM tools (optional)
- Error tracking with Sentry (optional)

---

## Future Enhancements

### Planned Features
1. **Multi-user Support**: User authentication and role-based access
2. **Real-time Data**: Integration with live market data feeds
3. **Advanced Analytics**: Machine learning-based pattern recognition
4. **API Access**: REST API for programmatic access
5. **Mobile Responsive**: Optimized mobile UI
6. **Export Reports**: PDF/Excel report generation
7. **Backtesting Engine**: Automated strategy backtesting
8. **Alert System**: Email/SMS notifications for portfolio events

### Technical Improvements
1. **Caching**: Redis for query result caching
2. **Background Jobs**: Celery for long-running calculations
3. **WebSockets**: Real-time chart updates
4. **GraphQL API**: Alternative to REST API
5. **Testing**: Comprehensive unit and integration tests
6. **CI/CD Pipeline**: Automated testing and deployment

---

## Appendix

### Glossary
- **Market**: A trading venue or asset class (e.g., Index Futures, Forex)
- **Instrument**: A tradable security with specific timeframe (e.g., MES_15min)
- **Portfolio**: A trading account or strategy with associated trades
- **Scenario**: A what-if analysis with modified parameters
- **OHLCV**: Open, High, Low, Close, Volume candlestick data
- **P&L**: Profit and Loss
- **Drawdown**: Peak-to-trough decline in equity

### References
- CME Group Contract Specifications: https://www.cmegroup.com/
- Interactive Brokers Margin Requirements: https://www.interactivebrokers.com/
- Streamlit Documentation: https://docs.streamlit.io/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

### Change Log
- **v1.0 (Nov 19, 2025)**: Initial design document created

---

**Document Prepared By**: AI Development Team  
**Project Owner**: User  
**Status**: Active Development
