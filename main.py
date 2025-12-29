#!/usr/bin/env python3

from config import load_config, validate_config, print_config
from data_collection import collect_all_drug_data, save_data
from forecasting import (train_prophet_model, generate_forecast, detect_anomalies,
                        detect_safety_signals, compare_drug_trends, generate_summary_stats)
from visualization import plot_forecast, plot_reactions, plot_clinical_trials, create_dashboard
import warnings
warnings.filterwarnings("ignore")

def main():
    #load config
    config = load_config()
    print_config(config)
    validate_config(config)
    
    drug_name = config['target_drug']
    
    print(f"\n{'='*60}")
    print(f"pharmacovigilance monitoring for {drug_name}")
    print(f"{'='*60}")
    
    #collect data from all sources
    data = collect_all_drug_data(drug_name, config)
    save_data(data, drug_name, config['data_dir'])
    
    #analyze adverse events
    df = data['adverse_events']
    
    if df.empty:
        print("\nno adverse event data available")
        return
    
    #train forecasting model
    print("\ntraining forecast model...")
    model = train_prophet_model(df, config)
    
    #generate forecast
    forecast = generate_forecast(model, config['forecast_horizon_quarters'])
    
    #detect anomalies and signals
    print("\ndetecting anomalies and safety signals...")
    anomalies = detect_anomalies(df, config['anomaly_threshold'])
    signals = detect_safety_signals(df, config['min_reports_for_signal'])
    
    if not anomalies.empty:
        print("\nanomalies detected:")
        print(anomalies[['ds', 'y', 'z_score']])
    
    if not signals.empty:
        print("\nsafety signals detected:")
        print(signals[['ds', 'y', 'pct_change']])
    
    #generate summary statistics
    summary = generate_summary_stats(df, forecast)
    print("\nsummary statistics:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    #create visualizations
    print("\ngenerating visualizations...")
    
    forecast_plot_path = f"{config['outputs_dir']}/{drug_name}_forecast.html"
    plot_forecast(df, forecast, drug_name, forecast_plot_path)
    
    if not data['reactions'].empty:
        reactions_plot_path = f"{config['outputs_dir']}/{drug_name}_reactions.html"
        plot_reactions(data['reactions'], drug_name, save_path=reactions_plot_path)
    
    if not data['clinical_trials'].empty:
        trials_plot_path = f"{config['outputs_dir']}/{drug_name}_trials.html"
        plot_clinical_trials(data['clinical_trials'], drug_name, trials_plot_path)
    
    #create comprehensive dashboard
    dashboard_path = f"{config['outputs_dir']}/{drug_name}_dashboard.html"
    create_dashboard(
        drug_name,
        df,
        forecast,
        data['reactions'],
        data['clinical_trials'],
        summary,
        dashboard_path
    )
    
    print(f"\n{'='*60}")
    print("monitoring complete")
    print(f"dashboard: {dashboard_path}")
    print(f"{'='*60}")

#monitor multiple drug variants
def monitor_variants():
    config = load_config()
    drug_variants = config['drug_variants']
    
    print(f"monitoring {len(drug_variants)} drug variants: {drug_variants}")
    
    all_data = {}
    
    for drug in drug_variants:
        print(f"\nprocessing {drug}...")
        data = collect_all_drug_data(drug, config)
        if not data['adverse_events'].empty:
            all_data[drug] = data['adverse_events']
    
    #compare trends
    if all_data:
        comparison = compare_drug_trends(all_data)
        print("\ndrug variant comparison:")
        print(comparison)
        
        comparison_path = f"{config['outputs_dir']}/variant_comparison.csv"
        comparison.to_csv(comparison_path, index=False)
        print(f"saved comparison to {comparison_path}")

if __name__ == "__main__":
    main()
    
    #optionally monitor all variants
    # monitor_variants()
