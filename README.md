# Flight Price Prediction – End-to-End (Docker)

Components:
- FastAPI model service (serving + saving predictions to PostgreSQL)
- Streamlit webapp (single & batch predictions + past predictions)
- Airflow (ingestion & scheduled prediction DAGs)
- Great Expectations (code-defined checks inside the ingestion DAG)
- Scripts for dataset splitting and error generation
- Dockerized Postgres
