"""
Machine Management Module
Handles creation, deletion, and management of trading machines (accounts/strategies)
"""

import uuid
import pandas as pd
from datetime import datetime
from scenario_engine import create_baseline_scenario

def create_machine(name, starting_capital, timeframe, status='simulated', trade_data=None, market_data=None):
    """
    Create a new machine (trading account/strategy)
    
    Parameters:
    - name: Machine name (e.g., "Conservative $50k (15min)")
    - starting_capital: Initial capital amount
    - timeframe: Trading timeframe ('5min', '15min', '1hr', etc.)
    - status: 'live' or 'simulated'
    - trade_data: Dict with 'MES' and 'MNQ' trade DataFrames
    - market_data: Dict with 'MES' and 'MNQ' market DataFrames for the timeframe
    
    Returns:
    - machine_dict: Dictionary containing machine configuration
    """
    
    machine_id = str(uuid.uuid4())
    
    # Create baseline scenario
    baseline = None
    if trade_data is not None and len(trade_data) > 0:
        combined_trades = pd.concat([trade_data.get('MES', pd.DataFrame()), 
                                     trade_data.get('MNQ', pd.DataFrame())])
        if not combined_trades.empty:
            baseline = create_baseline_scenario(combined_trades, starting_capital)
    
    machine = {
        'id': machine_id,
        'name': name,
        'starting_capital': starting_capital,
        'timeframe': timeframe,
        'status': status,  # 'live' or 'simulated'
        'trade_data': trade_data if trade_data is not None else {'MES': pd.DataFrame(), 'MNQ': pd.DataFrame()},
        'baseline': baseline,
        'scenarios': [],  # Max 10 additional scenarios
        'created_at': datetime.now().isoformat()
    }
    
    return machine


def get_machine_display_name(machine):
    """Get formatted display name for a machine"""
    status_icon = "🟢" if machine['status'] == 'live' else "⚪"
    return f"{status_icon} {machine['name']}"


def get_machine_color(machine):
    """Get color code for machine status"""
    return "#00ff00" if machine['status'] == 'live' else "#808080"


def validate_machine_name(name, existing_machines):
    """Check if machine name is unique"""
    existing_names = [m['name'] for m in existing_machines.values()]
    return name not in existing_names


def delete_machine(machines_dict, machine_id):
    """Delete a machine by ID"""
    if machine_id in machines_dict:
        del machines_dict[machine_id]
        return True
    return False


def get_active_machine(machines_dict, active_machine_id):
    """Get the currently active machine"""
    if active_machine_id and active_machine_id in machines_dict:
        return machines_dict[active_machine_id]
    return None


def get_machine_scenarios_count(machine):
    """Get count of scenarios in a machine"""
    baseline_count = 1 if machine.get('baseline') is not None else 0
    additional_scenarios = len(machine.get('scenarios', []))
    return baseline_count + additional_scenarios


def add_scenario_to_machine(machine, scenario):
    """Add a scenario to a machine (max 10 additional scenarios)"""
    if 'scenarios' not in machine:
        machine['scenarios'] = []
    
    MAX_ADDITIONAL_SCENARIOS = 10
    if len(machine['scenarios']) < MAX_ADDITIONAL_SCENARIOS:
        machine['scenarios'].append(scenario)
        return True
    return False


def get_all_scenarios_for_machine(machine):
    """Get all scenarios (baseline + additional) for a machine"""
    scenarios = []
    if machine.get('baseline'):
        scenarios.append(machine['baseline'])
    scenarios.extend(machine.get('scenarios', []))
    return scenarios
