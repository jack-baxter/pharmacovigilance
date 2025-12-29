from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from datetime import datetime
import json
from config import load_config
from data_collection import collect_all_drug_data, save_data
from forecasting import (train_prophet_model, generate_forecast, detect_anomalies,
                        detect_safety_signals, compare_drug_trends, generate_summary_stats)
from visualization import create_dashboard

app = FastAPI(title="pharma monitor api")

#global cache for latest results
_cache = {
    'last_update': None,
    'data': None,
    'summary': None
}

#run monitoring pipeline
def run_monitoring_pipeline():
    config = load_config()
    drug_name = config['target_drug']
    
    print(f"\nrunning monitoring pipeline for {drug_name}...")
    
    #collect data
    data = collect_all_drug_data(drug_name, config)
    save_data(data, drug_name, config['data_dir'])
    
    #forecast and analyze
    df = data['adverse_events']
    
    if not df.empty:
        model = train_prophet_model(df, config)
        forecast = generate_forecast(model, config['forecast_horizon_quarters'])
        anomalies = detect_anomalies(df, config['anomaly_threshold'])
        signals = detect_safety_signals(df, config['min_reports_for_signal'])
        summary = generate_summary_stats(df, forecast)
        
        #create dashboard
        dashboard_path = f"{config['outputs_dir']}/{drug_name}_dashboard.html"
        create_dashboard(
            drug_name, df, forecast, 
            data['reactions'], data['clinical_trials'],
            summary, dashboard_path
        )
        
        #update cache
        _cache['last_update'] = datetime.now().isoformat()
        _cache['data'] = {
            'adverse_events_count': len(df),
            'reactions_count': len(data['reactions']),
            'trials_count': len(data['clinical_trials']),
            'articles_count': len(data['pubmed_articles']),
            'anomalies_detected': len(anomalies),
            'signals_detected': len(signals)
        }
        _cache['summary'] = summary
        
        print("pipeline complete")
    else:
        print("no data available for analysis")

@app.get("/")
def root():
    return {
        "message": "pharma monitor api",
        "endpoints": [
            "/health",
            "/status",
            "/update",
            "/dashboard",
            "/summary"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
def get_status():
    return {
        "last_update": _cache['last_update'],
        "data": _cache['data']
    }

@app.get("/summary")
def get_summary():
    if _cache['summary'] is None:
        return {"error": "no data available, run /update first"}
    
    return _cache['summary']

@app.post("/update")
def trigger_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_monitoring_pipeline)
    return {
        "message": "update triggered",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dashboard")
def get_dashboard():
    config = load_config()
    dashboard_path = f"{config['outputs_dir']}/{config['target_drug']}_dashboard.html"
    
    try:
        with open(dashboard_path, 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "dashboard not found, run /update first"}
        )

#run server
def start_api(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    config = load_config()
    start_api(config['api_host'], config['api_port'])
