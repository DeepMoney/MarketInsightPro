"""
Portfolio Management Module
Handles creation, deletion, and management of trading portfolios (multi-instrument strategies)
"""

import uuid
import pandas as pd
from datetime import datetime
from scenario_engine import create_baseline_scenario

def create_portfolio(name, starting_capital, timeframe, status='simulated', trade_data=None, market_data=None):
    """
    Create a new portfolio (trading strategy with one or more instruments)
    
    Parameters:
    - name: Portfolio name (e.g., "Conservative Multi-Market Strategy")
    - starting_capital: Initial capital amount
    - timeframe: Trading timeframe ('5min', '15min', '1hr', etc.)
    - status: 'live' or 'simulated'
    - trade_data: Dict with instrument trade DataFrames
    - market_data: Dict with instrument market DataFrames for the timeframe
    
    Returns:
    - portfolio_dict: Dictionary containing portfolio configuration
    """
    
    portfolio_id = str(uuid.uuid4())
    
    # Create baseline scenario
    baseline = None
    if trade_data is not None and len(trade_data) > 0:
        combined_trades = pd.concat([df for df in trade_data.values() if not df.empty])
        if not combined_trades.empty:
            baseline = create_baseline_scenario(combined_trades, starting_capital)
    
    portfolio = {
        'id': portfolio_id,
        'name': name,
        'starting_capital': starting_capital,
        'timeframe': timeframe,
        'status': status,  # 'live' or 'simulated'
        'trade_data': trade_data if trade_data is not None else {},
        'baseline': baseline,
        'scenarios': [],  # Max 10 additional scenarios
        'created_at': datetime.now().isoformat()
    }
    
    return portfolio


def get_portfolio_display_name(portfolio):
    """Get formatted display name for a portfolio"""
    status_icon = "🟢" if portfolio['status'] == 'live' else "⚪"
    return f"{status_icon} {portfolio['name']}"


def get_portfolio_color(portfolio):
    """Get color code for portfolio status"""
    return "#00ff00" if portfolio['status'] == 'live' else "#808080"


def validate_portfolio_name(name, existing_portfolios):
    """Check if portfolio name is unique"""
    existing_names = [p['name'] for p in existing_portfolios.values()]
    return name not in existing_names


def delete_portfolio(portfolios_dict, portfolio_id):
    """Delete a portfolio by ID"""
    if portfolio_id in portfolios_dict:
        del portfolios_dict[portfolio_id]
        return True
    return False


def get_active_portfolio(portfolios_dict, active_portfolio_id):
    """Get the currently active portfolio"""
    if active_portfolio_id and active_portfolio_id in portfolios_dict:
        return portfolios_dict[active_portfolio_id]
    return None


def get_portfolio_scenarios_count(portfolio):
    """Get count of scenarios in a portfolio"""
    baseline_count = 1 if portfolio.get('baseline') is not None else 0
    additional_scenarios = len(portfolio.get('scenarios', []))
    return baseline_count + additional_scenarios


def add_scenario_to_portfolio(portfolio, scenario):
    """Add a scenario to a portfolio (max 10 additional scenarios)"""
    if 'scenarios' not in portfolio:
        portfolio['scenarios'] = []
    
    MAX_ADDITIONAL_SCENARIOS = 10
    if len(portfolio['scenarios']) < MAX_ADDITIONAL_SCENARIOS:
        portfolio['scenarios'].append(scenario)
        return True
    return False


def get_all_scenarios_for_portfolio(portfolio):
    """Get all scenarios (baseline + additional) for a portfolio"""
    scenarios = []
    if portfolio.get('baseline'):
        scenarios.append(portfolio['baseline'])
    scenarios.extend(portfolio.get('scenarios', []))
    return scenarios
