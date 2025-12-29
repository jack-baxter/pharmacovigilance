import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

#fit prophet model to adverse event time series
def train_prophet_model(df: pd.DataFrame, config: Dict) -> Prophet:
    if df.empty or len(df) < 2:
        print("insufficient data for prophet model")
        return None
    
    model = Prophet(
        changepoint_prior_scale=config['prophet_changepoint_prior'],
        interval_width=0.95,
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    
    model.fit(df)
    print(f"trained prophet model on {len(df)} data points")
    
    return model

#generate forecast for future periods
def generate_forecast(model: Prophet, periods: int) -> pd.DataFrame:
    if model is None:
        return pd.DataFrame()
    
    future = model.make_future_dataframe(periods=periods, freq='Q')
    forecast = model.predict(future)
    
    print(f"generated forecast for {periods} quarters ahead")
    return forecast

#detect anomalies using statistical approach
def detect_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    if df.empty or len(df) < 3:
        return pd.DataFrame()
    
    #calculate rolling statistics
    df['mean'] = df['y'].rolling(window=4, min_periods=1).mean()
    df['std'] = df['y'].rolling(window=4, min_periods=1).std()
    
    #z-score based anomaly detection
    df['z_score'] = (df['y'] - df['mean']) / (df['std'] + 1e-10)
    df['is_anomaly'] = abs(df['z_score']) > threshold
    
    anomalies = df[df['is_anomaly']].copy()
    
    if not anomalies.empty:
        print(f"detected {len(anomalies)} anomalies")
    
    return anomalies

#detect signals based on rate of change
def detect_safety_signals(df: pd.DataFrame, min_reports: int = 10) -> pd.DataFrame:
    if df.empty or len(df) < 2:
        return pd.DataFrame()
    
    #calculate quarter-over-quarter change
    df['pct_change'] = df['y'].pct_change() * 100
    df['abs_change'] = df['y'].diff()
    
    #flag significant increases
    signals = df[
        (df['abs_change'] > min_reports) & 
        (df['pct_change'] > 50)  #more than 50% increase
    ].copy()
    
    if not signals.empty:
        print(f"detected {len(signals)} safety signals")
    
    return signals

#compare trends across drug variants
def compare_drug_trends(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    comparison = []
    
    for drug, df in data_dict.items():
        if df.empty:
            continue
        
        recent_trend = df['y'].tail(4).mean() if len(df) >= 4 else df['y'].mean()
        total_reports = df['y'].sum()
        
        comparison.append({
            'drug': drug,
            'total_reports': int(total_reports),
            'recent_avg_quarterly': round(recent_trend, 1),
            'peak_quarter': df.loc[df['y'].idxmax(), 'ds'] if not df.empty else None,
            'peak_reports': int(df['y'].max()) if not df.empty else 0
        })
    
    return pd.DataFrame(comparison)

#generate summary statistics
def generate_summary_stats(df: pd.DataFrame, forecast: pd.DataFrame) -> Dict:
    if df.empty:
        return {}
    
    stats = {
        'total_reports': int(df['y'].sum()),
        'avg_quarterly_reports': round(df['y'].mean(), 2),
        'std_quarterly_reports': round(df['y'].std(), 2),
        'trend': 'increasing' if df['y'].iloc[-1] > df['y'].iloc[0] else 'decreasing',
        'recent_quarter_reports': int(df['y'].iloc[-1]) if not df.empty else 0,
        'data_start': df['ds'].min().strftime('%Y-%m-%d') if not df.empty else None,
        'data_end': df['ds'].max().strftime('%Y-%m-%d') if not df.empty else None
    }
    
    if not forecast.empty:
        future_forecast = forecast[forecast['ds'] > df['ds'].max()]
        if not future_forecast.empty:
            stats['forecast_next_quarter'] = round(future_forecast['yhat'].iloc[0], 1)
            stats['forecast_upper_bound'] = round(future_forecast['yhat_upper'].iloc[0], 1)
            stats['forecast_lower_bound'] = round(future_forecast['yhat_lower'].iloc[0], 1)
    
    return stats
