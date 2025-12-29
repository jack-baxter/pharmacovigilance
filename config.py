import os
from dotenv import load_dotenv

#load config from env
def load_config() -> dict:
    load_dotenv()
    
    config = {
        'openfda_api_url': os.getenv('OPENFDA_API_URL', 'https://api.fda.gov/drug/event.json'),
        'clinicaltrials_api_url': os.getenv('CLINICALTRIALS_API_URL', 'https://clinicaltrials.gov/api/v2/studies'),
        'pubmed_api_url': os.getenv('PUBMED_API_URL', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'),
        'ncbi_api_key': os.getenv('NCBI_API_KEY', ''),
        'target_drug': os.getenv('TARGET_DRUG', 'ozempic'),
        'drug_variants': os.getenv('DRUG_VARIANTS', 'semaglutide,wegovy,rybelsus').split(','),
        'update_frequency_hours': int(os.getenv('UPDATE_FREQUENCY_HOURS', 24)),
        'anomaly_threshold': float(os.getenv('ANOMALY_THRESHOLD', 2.0)),
        'min_reports_for_signal': int(os.getenv('MIN_REPORTS_FOR_SIGNAL', 10)),
        'forecast_horizon_quarters': int(os.getenv('FORECAST_HORIZON_QUARTERS', 4)),
        'prophet_changepoint_prior': float(os.getenv('PROPHET_CHANGEPOINT_PRIOR', 0.05)),
        'data_dir': os.getenv('DATA_DIR', './data'),
        'models_dir': os.getenv('MODELS_DIR', './models'),
        'outputs_dir': os.getenv('OUTPUTS_DIR', './outputs'),
        'logs_dir': os.getenv('LOGS_DIR', './logs'),
        'api_host': os.getenv('API_HOST', '0.0.0.0'),
        'api_port': int(os.getenv('API_PORT', 8000))
    }
    
    return config

#validate and create directories
def validate_config(config: dict) -> bool:
    required_dirs = ['data_dir', 'models_dir', 'outputs_dir', 'logs_dir']
    
    for key in required_dirs:
        path = config.get(key)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"created directory: {path}")
    
    return True

#print config for debugging
def print_config(config: dict):
    print("current configuration:")
    print("-" * 50)
    for key, value in config.items():
        if 'key' in key.lower():
            display = f"{value[:8]}..." if value else "(not set)"
        else:
            display = value
        print(f"{key}: {display}")
    print("-" * 50)
