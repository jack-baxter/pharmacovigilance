# Pharmacovigilance Monitor

real-time drug safety monitoring system using openfda adverse event reports, clinical trials data, and pubmed research. automated forecasting and anomaly detection for ozempic and related glp-1 drugs.

## what it does

monitors multiple data sources for drug safety signals:

1. **openfda adverse events**: quarterly trends of reported side effects
2. **clinical trials**: ongoing research from clinicaltrials.gov
3. **pubmed articles**: recent research publications
4. **forecasting**: prophet-based predictions for future adverse event rates
5. **anomaly detection**: statistical alerts for unusual patterns
6. **safety signals**: automated detection of concerning trends

outputs interactive dashboards with plotly visualizations and provides rest api for automated updates.

## project structure

```
pharma_monitor/
├── data/                   # collected raw data
├── models/                 # trained forecasting models
├── outputs/                # dashboards and visualizations
├── logs/                   # processing logs
├── config.py              # configuration loader
├── data_collection.py     # openfda, clinicaltrials, pubmed apis
├── forecasting.py         # prophet models and anomaly detection
├── visualization.py       # plotly dashboards
├── api_server.py          # fastapi rest endpoints
├── main.py                # main execution script
└── requirements.txt
```

## setup

1. install dependencies
```bash
pip install -r requirements.txt
```

2. configure monitoring targets
```bash
cp .env.example .env
# edit .env to set drug name and variants
```

3. run monitoring pipeline
```bash
python main.py
```

4. start api server (optional)
```bash
python api_server.py
```

## usage

**single drug monitoring:**
```python
from config import load_config
from data_collection import collect_all_drug_data
from forecasting import train_prophet_model, generate_forecast

config = load_config()
data = collect_all_drug_data('ozempic', config)

model = train_prophet_model(data['adverse_events'], config)
forecast = generate_forecast(model, periods=4)
```

**api endpoints:**
```bash
# health check
curl http://localhost:8000/health

# trigger update
curl -X POST http://localhost:8000/update

# get status
curl http://localhost:8000/status

# view dashboard
open http://localhost:8000/dashboard
```

## data sources

### openfda adverse events
- source: fda adverse event reporting system (faers)
- endpoint: https://api.fda.gov/drug/event.json
- data: quarterly aggregated report counts
- includes: patient reactions, outcomes, drug details

### clinicaltrials.gov
- source: nih clinical trials registry
- endpoint: https://clinicaltrials.gov/api/v2/studies
- data: trial status, phase, enrollment, completion dates
- filters: active trials for target drug

### pubmed
- source: ncbi pubmed database
- endpoint: https://eutils.ncbi.nlm.nih.gov/entrez/eutils
- data: recent research articles, publication dates
- searches: title/abstract mentions of drug

## forecasting approach

**prophet model:**
- facebook's time series forecasting library
- captures seasonality and trends in adverse events
- 95% confidence intervals for predictions
- configurable changepoint detection sensitivity

**anomaly detection:**
- rolling window z-score calculation
- flags quarters with reports >2 std deviations from mean
- adjustable threshold via config

**safety signals:**
- quarter-over-quarter percentage change
- flags increases >50% with >10 reports
- early warning system for emerging issues

## output formats

**dashboard includes:**
- time series plot with forecast overlay
- top 20 adverse reactions bar chart
- clinical trials status pie chart
- summary statistics table

**json summary:**
```json
{
  "total_reports": 1234,
  "avg_quarterly_reports": 45.2,
  "trend": "increasing",
  "recent_quarter_reports": 67,
  "forecast_next_quarter": 72.3,
  "forecast_upper_bound": 95.1,
  "forecast_lower_bound": 49.5
}
```

**anomaly output:**
```
         ds     y  z_score  is_anomaly
2023-12-31   145    3.42        True
2024-03-31   178    4.15        True
```

## notes and gotchas

- **api rate limits**: openfda limited to 240 requests/minute. pubmed needs api key for higher limits
- **data lag**: fda reports have ~3-6 month reporting delay. recent quarters may be incomplete
- **drug name matching**: searches are case-insensitive but require exact brand/generic names
- **forecast accuracy**: prophet works best with 2+ years of data. short history reduces reliability
- **anomaly false positives**: statistical thresholds may flag legitimate spikes. manual review recommended
- **clinical trial data**: may not include all international trials or pre-registration studies
- **pubmed parsing**: currently simplified. full xml parsing would extract abstracts and authors

## automated monitoring

**scheduled updates:**
set up cron job for daily updates:
```bash
# run every day at 2am
0 2 * * * cd /path/to/pharma_monitor && python main.py
```

**api server deployment:**
```bash
# production mode with gunicorn
gunicorn api_server:app --workers 4 --bind 0.0.0.0:8000
```

**docker deployment:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

## drug variants monitored

default configuration tracks glp-1 receptor agonists:
- **ozempic**: weekly injection, 0.25-2mg doses
- **wegovy**: higher dose formulation for weight loss
- **rybelsus**: oral tablet form
- **semaglutide**: generic name

add more variants in .env:
```bash
DRUG_VARIANTS=ozempic,wegovy,rybelsus,mounjaro,trulicity
```

## safety signal interpretation

**what triggers an alert:**
1. adverse event reports increase >50% quarter-over-quarter
2. absolute increase >10 reports (configurable threshold)
3. z-score >2 standard deviations from rolling mean

**common false positives:**
- media coverage spike causing increased reporting
- regulatory changes mandating more reporting
- expanded indication or dosing changes
- seasonal patterns (flu season, etc)

**actionable signals:**
- sustained upward trend over multiple quarters
- specific reaction types clustering
- severity increases (hospitalizations, deaths)
- new reactions not previously reported

## future improvements

things to add:
- pytorch tft model for more complex forecasting
- nbeats model from darts library (already imported)
- social media sentiment analysis (twitter/reddit)
- comparative safety analysis across drug classes
- automated report generation for regulatory submissions
- integration with ehr systems
- real-time alerting via email/slack
- geographic clustering of adverse events
- demographic risk factor analysis

## legal disclaimer

this tool is for research and educational purposes only. not intended for clinical decision making or regulatory submissions. adverse event data does not establish causation. consult healthcare professionals and regulatory guidance for drug safety decisions.

## references

- openfda api: https://open.fda.gov/apis/
- clinicaltrials.gov api: https://clinicaltrials.gov/data-api/
- pubmed e-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- prophet documentation: https://facebook.github.io/prophet/
- fda faers: https://www.fda.gov/drugs/surveillance/questions-and-answers-fdas-adverse-event-reporting-system-faers

## license

educational/research use only
