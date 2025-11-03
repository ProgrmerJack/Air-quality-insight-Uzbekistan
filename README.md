# Air-quality-insight-Uzbekistan

A reproducible data pipeline, analysis, models and dashboards for understanding and forecasting air quality across cities in Uzbekistan. This repository centralizes data ingestion, cleaning, exploratory analysis, spatial and temporal visualizations, AQI calculations and short-term forecasting using machine learning models. It is designed to be used by data scientists, public-health researchers, policy makers and civic technologists.

Table of contents
- Project overview
- Key features
- Data sources
- Project structure
- Getting started (install & run)
- Data processing & engineering
- Analytics & Modeling
- Dashboards / API
- Example workflows
- Reproducibility & deployment
- Contributing
- License & contact
- Acknowledgements

Project overview
---------------
Air-quality-insight-Uzbekistan aggregates air pollutant observations and remote-sensing data, cleans and harmonizes them, computes air quality indices (AQI), conducts exploratory and spatial analyses, and produces short-term forecasts (hours to days) for pollutant concentrations and AQI. The goal is to provide clear, reproducible insights into air quality patterns across Uzbekistan and to enable downstream visualization and alerting.

Key features
------------
- Multi-source data ingestion (station observations, satellite products, weather)
- End-to-end ETL (raw -> cleaned -> feature-engineered datasets)
- AQI calculation (configurable: EPA / WHO / custom thresholds)
- Time-series forecasting models (examples: XGBoost, RandomForest, LSTM) for PM2.5/PM10/NO2/O3
- Spatial visualizations (interactive maps) and temporal dashboards
- Lightweight REST API for predictions and latest readings
- Dockerfile and example CI for reproducible runs

Data sources
------------
This project is structured to use (and document) the following types of data sources. Replace or extend these with your local access keys or files.

- Local air quality monitoring stations (CSV, JSON, direct database, or API)
- OpenAQ (https://openaq.org) — global aggregated station data
- Satellite products (e.g., NASA MODIS, Sentinel-5P TROPOMI) for column/derived pollutants
- Meteorological data (temperature, wind, humidity) from providers such as Open-Meteo, Meteostat or local services
- Administrative boundaries and city shapefiles for mapping

Project structure
-----------------
A recommended layout (your repo may vary; adjust paths if different):

- README.md — this file
- requirements.txt — Python dependencies
- environment.yml — (optional) conda env specification
- Dockerfile — container definition
- data/
  - raw/ — raw downloads (DO NOT commit large raw files)
  - processed/ — cleaned & merged datasets
- notebooks/ — EDA and experiment notebooks
- src/
  - data/ — ingestion, cleaning, transformations (ingest.py, clean.py)
  - features/ — feature engineering (meteorological lags, rolling stats)
  - models/ — model training and evaluation (train.py, predict.py)
  - api/ — fastapi/flask app to serve predictions
  - viz/ — plotting utilities and dashboard code (streamlit / dash)
- app/ or deployment/ — Docker / k8s manifests, CI scripts
- docs/ — additional docs and methodology

Getting started
---------------
Prerequisites
- Python 3.9+ (3.10 recommended)
- pip or conda
- (Optional) Docker for containerized runs

Quick start (local)
1. Clone the repository
   git clone https://github.com/ProgrmerJack/Air-quality-insight-Uzbekistan.git
   cd Air-quality-insight-Uzbekistan

2. Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   venv\Scripts\activate      # Windows

3. Install dependencies
   pip install -r requirements.txt

4. Prepare data
   - Place raw station CSVs into data/raw/ or configure the ingestion scripts to fetch from APIs.
   - Populate a config file (examples/config.yml) with API keys and source paths.

5. Run ingestion & preprocessing
   python src/data/ingest.py --config examples/config.yml
   python src/data/clean.py --input data/raw/ --output data/processed/

6. Train a model (example)
   python src/models/train.py --data data/processed/train.csv --model_out models/pm25_xgb.pkl

7. Launch dashboard (example using Streamlit)
   streamlit run src/viz/streamlit_app.py

8. Run API (example using Uvicorn / FastAPI)
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

Data processing & engineering
-----------------------------
This project follows standard ETL steps:

1. Ingestion
   - Download or fetch station measurements and satellite data.
   - Normalize timestamps to a common timezone (UTC) and format (ISO 8601).

2. Cleaning
   - Deduplicate records, remove clearly invalid readings (negative concentrations), apply unit conversions (µg/m3), and mark missing values.
   - Use sensor-specific calibration factors if available.

3. Harmonization
   - Resample to consistent frequency (hourly is typical).
   - Merge meteorological covariates and nearby station readings.
   - Apply spatial joins with city boundaries.

4. Feature engineering
   - Rolling statistics (mean, std) over windows (3h, 24h, 7d).
   - Lag features (1h, 3h, 24h) for autoregressive models.
   - Meteorological interactions (e.g., wind speed * pollutant).

Analytics & Modeling
-------------------
AQI calculation
- Configurable methods are supported:
  - EPA breakpoint method (for PM2.5, PM10, O3, etc.)
  - WHO guideline comparisons
  - Custom thresholds suited to Uzbekistan (if provided)

Forecasting
- Example modeling approaches included:
  - Gradient boosting (XGBoost / LightGBM) with engineered features — fast, interpretable feature importances
  - RandomForest for baseline ensemble
  - LSTM or Temporal Convolutional Networks for sequence modeling (if enough historical data)
- Evaluation: train/validation/test splits using time-aware holdouts, metrics like RMSE, MAE, and classification metrics if forecasting exceedance events.

Model explainability
- SHAP or permutation importances are used to explain model predictions and highlight drivers of poor air quality

Dashboards / API
----------------
Interactive dashboards let users:
- Inspect time-series of pollutants for a city or station
- Explore spatial maps of pollutant concentrations (choropleth, point layers)
- View model forecasts and uncertainty bands
- Configure alerts for AQI thresholds

API
- Lightweight REST API for:
  - Latest station observations
  - Predicted pollutant concentrations and AQI for a given station/city and horizon
  - Health advisory messages (based on AQI band)
- Example endpoints:
  - GET /api/v1/stations — list stations
  - GET /api/v1/stations/{station_id}/latest — latest reading
  - POST /api/v1/predict — input: station_id or coordinates, horizon -> returns forecast

Example workflows
-----------------
- Recreate a specific analysis:
  1. Run the ingestion steps to collect data for the period of interest
  2. Execute notebooks/eda/PM25_city_trends.ipynb to reproduce plots
  3. Train models with src/models/train.py and save results to models/
  4. Start dashboard to visualize outputs

- Produce daily forecasts and publish:
  - Schedule a daily job (cron or GitHub Actions) to run the pipeline: ingest -> preprocess -> predict -> push forecasts to API / database.

Reproducibility & deployment
----------------------------
- Docker: build and run containers for production deployment:
  docker build -t aqi-uzbekistan:latest .
  docker run -p 8000:8000 aqi-uzbekistan:latest

- CI: Add tests to verify data contracts (expected columns, types and ranges). Include small fixture datasets for unit tests under tests/.

- Data ethics & privacy: do not publish raw personal data or station metadata that is restricted by local regulations. Respect terms of service of third-party data providers.

Configuration
-------------
- examples/config.yml (store API keys, source URLs, local paths)
- .env (environment variables) — never commit secrets to the repo

Common environment variables
- DATA_PATH — base data folder
- DB_CONN — connection string for a timeseries DB (optional)
- OPENAQ_TOKEN — if using authenticated OpenAQ endpoints
- S3_BUCKET — for storing processed data (optional)

Contributing
------------
Contributions are welcome. Typical ways to contribute:
- Open an issue for bugs or feature requests
- Add new data source adapters (src/data/)
- Improve models or add benchmarks
- Add visualizations or improve the dashboard UX
- Submit pull requests to the main branch; follow coding and testing guidelines outlined in CONTRIBUTING.md (create one if missing)

License
-------
This repository is open-source and uses the MIT License. See LICENSE file for details.

Contact
-------
Maintainer: ProgrmerJack
- GitHub: https://github.com/ProgrmerJack
- For questions, open an issue.

Acknowledgements
----------------
- OpenAQ and national monitoring agencies for public air quality data
- NASA / ESA for satellite data products
- The open-source Python ecosystem: pandas, scikit-learn, xgboost, pytorch/keras (if used), geopandas, folium/leaflet, streamlit/plotly

Notes
-----
This README is a high-level guide. Check the notebooks/ and src/ folders for implementation details, usage examples, and exact command-line flags for each script.
If you want, I can generate:
- a detailed requirements.txt from the code,
- example config.yml,
- starter ingestion script template,
- or a Streamlit dashboard scaffold to visualize PM2.5 across Uzbek cities.
