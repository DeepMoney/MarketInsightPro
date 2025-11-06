import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

def create_candlestick_chart(market_df, trades_df, title="Price Action with Trades"):
    """
    Create clean candlestick chart with trade entry/exit markers (NO indicators)
    """
    
    if market_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No market data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    market = market_df.copy()
    market['timestamp'] = pd.to_datetime(market['timestamp'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=market['timestamp'],
        open=market['open'],
        high=market['high'],
        low=market['low'],
        close=market['close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    if not trades_df.empty:
        trades = trades_df.copy()
        trades['entry_time'] = pd.to_datetime(trades['entry_time'])
        trades['exit_time'] = pd.to_datetime(trades['exit_time'])
        
        long_entries = trades[trades['direction'] == 'Long']
        short_entries = trades[trades['direction'] == 'Short']
        
        if not long_entries.empty:
            fig.add_trace(go.Scatter(
                x=long_entries['entry_time'],
                y=long_entries['entry_price'],
                mode='markers',
                name='Long Entry',
                marker=dict(symbol='circle', size=10, color='blue', line=dict(width=2, color='white'))
            ))
        
        if not short_entries.empty:
            fig.add_trace(go.Scatter(
                x=short_entries['entry_time'],
                y=short_entries['entry_price'],
                mode='markers',
                name='Short Entry',
                marker=dict(symbol='circle', size=10, color='orange', line=dict(width=2, color='white'))
            ))
        
        winning_exits = trades[trades['outcome'] == 'Win']
        losing_exits = trades[trades['outcome'] == 'Loss']
        
        if not winning_exits.empty:
            fig.add_trace(go.Scatter(
                x=winning_exits['exit_time'],
                y=winning_exits['exit_price'],
                mode='markers',
                name='Profitable Exit',
                marker=dict(symbol='triangle-up', size=10, color='green')
            ))
        
        if not losing_exits.empty:
            fig.add_trace(go.Scatter(
                x=losing_exits['exit_time'],
                y=losing_exits['exit_price'],
                mode='markers',
                name='Loss Exit',
                marker=dict(symbol='triangle-down', size=10, color='red')
            ))
        
        for _, trade in trades.iterrows():
            color = 'green' if trade['outcome'] == 'Win' else 'red'
            fig.add_trace(go.Scatter(
                x=[trade['entry_time'], trade['exit_time']],
                y=[trade['entry_price'], trade['exit_price']],
                mode='lines',
                line=dict(color=color, width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price',
        template='plotly_white',
        height=600,
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    return fig


def create_equity_curve(trades_df, starting_capital=50000, title="Equity Curve with Drawdown"):
    """
    Create equity curve with drawdown overlay and high water mark
    """
    
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No trade data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades = trades_df.copy()
    trades = trades.sort_values('exit_time')
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades['cumulative_pnl'] = trades['pnl'].cumsum()
    trades['equity'] = starting_capital + trades['cumulative_pnl']
    trades['high_water_mark'] = trades['equity'].expanding().max()
    trades['drawdown'] = trades['equity'] - trades['high_water_mark']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=trades['exit_time'],
        y=trades['equity'],
        mode='lines',
        name='Equity',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=trades['exit_time'],
        y=trades['high_water_mark'],
        mode='lines',
        name='High Water Mark',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=trades['exit_time'],
        y=trades['drawdown'],
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(color='red', width=1),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Equity ($)',
        yaxis2=dict(
            title='Drawdown ($)',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_weekly_pnl_heatmap(trades_df, title="Weekly P&L Heatmap"):
    """
    Create weekly PnL heatmap calendar
    """
    
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No trade data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades = trades_df.copy()
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades['date'] = trades['exit_time'].dt.date
    trades['weekday'] = trades['exit_time'].dt.day_name()
    trades['week'] = trades['exit_time'].dt.isocalendar().week
    trades['year'] = trades['exit_time'].dt.year
    
    daily_pnl = trades.groupby(['year', 'week', 'weekday', 'date'])['pnl'].sum().reset_index()
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_pnl['weekday'] = pd.Categorical(daily_pnl['weekday'], categories=weekday_order, ordered=True)
    
    pivot_data = daily_pnl.pivot_table(
        values='pnl',
        index='weekday',
        columns='week',
        aggfunc='sum',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn',
        zmid=0,
        text=pivot_data.values,
        texttemplate='$%{text:.0f}',
        textfont={"size": 10},
        colorbar=dict(title="P&L ($)")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Week Number',
        yaxis_title='Day of Week',
        template='plotly_white',
        height=400
    )
    
    return fig


def create_monthly_returns_grid(trades_df, title="Monthly Returns"):
    """
    Create monthly returns table/grid view
    """
    
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No trade data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades = trades_df.copy()
    trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    trades['year'] = trades['exit_time'].dt.year
    trades['month'] = trades['exit_time'].dt.month
    
    monthly = trades.groupby(['year', 'month'])['pnl'].sum().reset_index()
    
    pivot = monthly.pivot(index='month', columns='year', values='pnl').fillna(0)
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot.index = [month_names[i-1] for i in pivot.index]
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        zmid=0,
        text=pivot.values,
        texttemplate='$%{text:.0f}',
        textfont={"size": 12},
        colorbar=dict(title="Returns ($)")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Month',
        template='plotly_white',
        height=500
    )
    
    return fig


def create_time_of_day_heatmap(trades_df, title="Time-of-Day Performance"):
    """
    Create time-of-day performance heatmap
    """
    
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No trade data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades = trades_df.copy()
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])
    trades['hour'] = trades['entry_time'].dt.hour
    trades['weekday'] = trades['entry_time'].dt.day_name()
    
    hourly_pnl = trades.groupby(['weekday', 'hour'])['pnl'].agg(['mean', 'count']).reset_index()
    hourly_pnl = hourly_pnl[hourly_pnl['count'] >= 1]
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hourly_pnl['weekday'] = pd.Categorical(hourly_pnl['weekday'], categories=weekday_order, ordered=True)
    
    pivot = hourly_pnl.pivot(index='weekday', columns='hour', values='mean').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        zmid=0,
        text=pivot.values,
        texttemplate='$%{text:.1f}',
        textfont={"size": 10},
        colorbar=dict(title="Avg P&L ($)")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        template='plotly_white',
        height=400
    )
    
    return fig


def create_r_multiple_histogram(trades_df, title="R-Multiple Distribution"):
    """
    Create R-Multiple distribution histogram
    """
    
    if trades_df.empty or 'r_multiple' not in trades_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No R-multiple data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades = trades_df.copy()
    r_multiples = trades['r_multiple'].dropna()
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=r_multiples,
        nbinsx=30,
        marker=dict(
            color=r_multiples,
            colorscale='RdYlGn',
            cmid=0,
            showscale=False
        ),
        name='R-Multiple'
    ))
    
    mean_r = r_multiples.mean()
    fig.add_vline(x=mean_r, line_dash="dash", line_color="blue", annotation_text=f"Mean: {mean_r:.2f}R")
    fig.add_vline(x=0, line_dash="solid", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title=title,
        xaxis_title='R-Multiple',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400,
        showlegend=False
    )
    
    return fig


def create_comparison_bar_chart(comparison_df, metric='total_pnl', title="Scenario Comparison"):
    """
    Create bar chart comparing scenarios on a specific metric
    """
    
    if comparison_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No scenarios to compare", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    df = comparison_df.copy()
    
    colors = ['lightblue' if row['is_baseline'] else 'steelblue' for _, row in df.iterrows()]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['scenario_name'],
        y=df[metric],
        marker_color=colors,
        text=df[metric],
        texttemplate='%{text:.2f}',
        textposition='outside'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Scenario',
        yaxis_title=metric.replace('_', ' ').title(),
        template='plotly_white',
        height=400
    )
    
    return fig
