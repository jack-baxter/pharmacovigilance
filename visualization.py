import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict

#plot adverse event time series with forecast
def plot_forecast(df: pd.DataFrame, forecast: pd.DataFrame, drug_name: str, save_path: str = None):
    fig = go.Figure()
    
    #actual data
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines+markers',
        name='actual reports',
        line=dict(color='blue', width=2)
    ))
    
    if not forecast.empty:
        #forecast line
        future_forecast = forecast[forecast['ds'] > df['ds'].max()]
        
        fig.add_trace(go.Scatter(
            x=future_forecast['ds'],
            y=future_forecast['yhat'],
            mode='lines',
            name='forecast',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        #confidence interval
        fig.add_trace(go.Scatter(
            x=future_forecast['ds'],
            y=future_forecast['yhat_upper'],
            mode='lines',
            name='upper bound',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=future_forecast['ds'],
            y=future_forecast['yhat_lower'],
            mode='lines',
            name='lower bound',
            line=dict(width=0),
            fillcolor='rgba(255,0,0,0.2)',
            fill='tonexty',
            showlegend=False
        ))
    
    fig.update_layout(
        title=f'{drug_name} adverse event reports over time',
        xaxis_title='date',
        yaxis_title='quarterly reports',
        hovermode='x unified',
        template='plotly_white'
    )
    
    if save_path:
        fig.write_html(save_path)
        print(f"saved forecast plot to {save_path}")
    
    return fig

#plot top adverse reactions
def plot_reactions(reactions: pd.DataFrame, drug_name: str, top_n: int = 20, save_path: str = None):
    if reactions.empty:
        return None
    
    top_reactions = reactions.head(top_n)
    
    fig = go.Figure(go.Bar(
        x=top_reactions['count'],
        y=top_reactions['reaction'],
        orientation='h',
        marker=dict(color='steelblue')
    ))
    
    fig.update_layout(
        title=f'top {top_n} adverse reactions for {drug_name}',
        xaxis_title='number of reports',
        yaxis_title='reaction',
        height=600,
        yaxis={'categoryorder': 'total ascending'},
        template='plotly_white'
    ))
    
    if save_path:
        fig.write_html(save_path)
        print(f"saved reactions plot to {save_path}")
    
    return fig

#plot clinical trials status breakdown
def plot_clinical_trials(trials: pd.DataFrame, drug_name: str, save_path: str = None):
    if trials.empty:
        return None
    
    status_counts = trials['status'].value_counts()
    
    fig = go.Figure(go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.3
    ))
    
    fig.update_layout(
        title=f'{drug_name} clinical trials by status',
        template='plotly_white'
    )
    
    if save_path:
        fig.write_html(save_path)
        print(f"saved trials plot to {save_path}")
    
    return fig

#create comprehensive dashboard
def create_dashboard(drug_name: str, 
                    df: pd.DataFrame, 
                    forecast: pd.DataFrame,
                    reactions: pd.DataFrame,
                    trials: pd.DataFrame,
                    summary_stats: Dict,
                    save_path: str = None):
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'adverse event trend & forecast',
            'top adverse reactions',
            'clinical trials status',
            'summary statistics'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'bar'}],
            [{'type': 'pie'}, {'type': 'table'}]
        ]
    )
    
    #subplot 1: time series
    fig.add_trace(go.Scatter(
        x=df['ds'], y=df['y'],
        mode='lines+markers',
        name='actual',
        line=dict(color='blue')
    ), row=1, col=1)
    
    if not forecast.empty:
        future = forecast[forecast['ds'] > df['ds'].max()]
        fig.add_trace(go.Scatter(
            x=future['ds'], y=future['yhat'],
            mode='lines',
            name='forecast',
            line=dict(color='red', dash='dash')
        ), row=1, col=1)
    
    #subplot 2: reactions
    if not reactions.empty:
        top_reactions = reactions.head(10)
        fig.add_trace(go.Bar(
            x=top_reactions['count'],
            y=top_reactions['reaction'],
            orientation='h',
            marker=dict(color='steelblue'),
            showlegend=False
        ), row=1, col=2)
    
    #subplot 3: trials
    if not trials.empty:
        status_counts = trials['status'].value_counts()
        fig.add_trace(go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            showlegend=False
        ), row=2, col=1)
    
    #subplot 4: summary table
    stats_df = pd.DataFrame([summary_stats]).T.reset_index()
    stats_df.columns = ['metric', 'value']
    
    fig.add_trace(go.Table(
        header=dict(values=['metric', 'value'],
                   fill_color='lightgray',
                   align='left'),
        cells=dict(values=[stats_df['metric'], stats_df['value']],
                  align='left')
    ), row=2, col=2)
    
    fig.update_layout(
        height=1000,
        title_text=f'{drug_name} pharmacovigilance dashboard',
        showlegend=True,
        template='plotly_white'
    )
    
    if save_path:
        fig.write_html(save_path)
        print(f"saved dashboard to {save_path}")
    
    return fig
