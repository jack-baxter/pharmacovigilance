import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import time

#fetch adverse event data from openfda
#fixed bug from original notebook
def fetch_fda_adverse_events(drug_name: str, start_year: int = 2014, end_year: int = 2025) -> pd.DataFrame:
    url = "https://api.fda.gov/drug/event.json"
    query = f'patient.drug.medicinalproduct:"{drug_name}"+AND+receivedate:[{start_year}0101+TO+{end_year}1231]'
    
    try:
        resp = requests.get(url, params={"search": query, "count": "receivedate"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if 'results' not in data:
            print(f"no data found for {drug_name}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data['results'])
        df['receivedate'] = pd.to_datetime(df['receivedate'].astype(str), format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['receivedate'])
        
        #aggregate by quarter
        df = df.set_index('receivedate').resample('Q').agg({'count': 'sum'}).reset_index()
        df.columns = ['ds', 'y']
        
        print(f"loaded {len(df)} quarters for {drug_name} (total reports: {df['y'].sum()})")
        return df
    
    except Exception as e:
        print(f"error fetching fda data: {e}")
        return pd.DataFrame()

#fetch detailed adverse event reactions
def fetch_fda_reactions(drug_name: str, limit: int = 100) -> pd.DataFrame:
    url = "https://api.fda.gov/drug/event.json"
    query = f'patient.drug.medicinalproduct:"{drug_name}"'
    
    try:
        resp = requests.get(url, params={"search": query, "count": "patient.reaction.reactionmeddrapt.exact", "limit": limit}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if 'results' not in data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data['results'])
        df.columns = ['reaction', 'count']
        df = df.sort_values('count', ascending=False)
        
        print(f"loaded {len(df)} unique reactions for {drug_name}")
        return df
    
    except Exception as e:
        print(f"error fetching reactions: {e}")
        return pd.DataFrame()

#fetch clinical trials from clinicaltrials.gov
def fetch_clinical_trials(drug_name: str) -> pd.DataFrame:
    url = "https://clinicaltrials.gov/api/v2/studies"
    
    try:
        params = {
            'query.term': drug_name,
            'format': 'json',
            'pageSize': 100
        }
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if 'studies' not in data:
            return pd.DataFrame()
        
        trials = []
        for study in data['studies']:
            protocol = study.get('protocolSection', {})
            identification = protocol.get('identificationModule', {})
            status = protocol.get('statusModule', {})
            design = protocol.get('designModule', {})
            
            trials.append({
                'nct_id': identification.get('nctId', ''),
                'title': identification.get('briefTitle', ''),
                'status': status.get('overallStatus', ''),
                'start_date': status.get('startDateStruct', {}).get('date', ''),
                'completion_date': status.get('completionDateStruct', {}).get('date', ''),
                'phase': design.get('phases', [''])[0] if design.get('phases') else '',
                'enrollment': status.get('enrollmentInfo', {}).get('count', 0)
            })
        
        df = pd.DataFrame(trials)
        print(f"loaded {len(df)} clinical trials for {drug_name}")
        return df
    
    except Exception as e:
        print(f"error fetching clinical trials: {e}")
        return pd.DataFrame()

#fetch recent pubmed articles
def fetch_pubmed_articles(drug_name: str, max_results: int = 50, api_key: str = None) -> pd.DataFrame:
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    try:
        #search for article ids
        search_params = {
            'db': 'pubmed',
            'term': f'{drug_name}[Title/Abstract]',
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'pub_date'
        }
        
        if api_key:
            search_params['api_key'] = api_key
        
        search_resp = requests.get(search_url, params=search_params, timeout=30)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        
        pmids = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            print(f"no pubmed articles found for {drug_name}")
            return pd.DataFrame()
        
        #fetch article details
        time.sleep(0.5)  #respect ncbi rate limit
        
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        if api_key:
            fetch_params['api_key'] = api_key
        
        fetch_resp = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_resp.raise_for_status()
        
        #parse xml response (simplified)
        articles = []
        for pmid in pmids:
            articles.append({
                'pmid': pmid,
                'title': f'article {pmid}',  #would need xml parsing for full details
                'pub_date': datetime.now().strftime('%Y-%m-%d'),
                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
            })
        
        df = pd.DataFrame(articles)
        print(f"loaded {len(df)} pubmed articles for {drug_name}")
        return df
    
    except Exception as e:
        print(f"error fetching pubmed articles: {e}")
        return pd.DataFrame()

#collect all data for drug
def collect_all_drug_data(drug_name: str, config: Dict) -> Dict[str, pd.DataFrame]:
    print(f"\ncollecting data for {drug_name}...")
    
    data = {
        'adverse_events': fetch_fda_adverse_events(drug_name),
        'reactions': fetch_fda_reactions(drug_name),
        'clinical_trials': fetch_clinical_trials(drug_name),
        'pubmed_articles': fetch_pubmed_articles(drug_name, api_key=config.get('ncbi_api_key'))
    }
    
    return data

#save collected data
def save_data(data: Dict[str, pd.DataFrame], drug_name: str, data_dir: str):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for key, df in data.items():
        if not df.empty:
            filepath = f"{data_dir}/{drug_name}_{key}_{timestamp}.csv"
            df.to_csv(filepath, index=False)
            print(f"saved {key} to {filepath}")
