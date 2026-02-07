import glob
import os
import pathlib
from datetime import timedelta

import pandas as pd
import requests
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sqlalchemy import create_engine, text

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
GOOD_DIR = os.getenv("GOOD_DATA_DIR", "/opt/airflow/data/good_data")
PRED_DIR = os.getenv("PREDICTIONS_DIR", "/opt/airflow/data/predictions")

APP_DB = os.getenv(
    "APP_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@postgres:5432/predictions"
)

API_URL = os.getenv("API_INTERNAL_URL", "http://api:8000")

engine = create_engine(APP_DB, pool_pre_ping=True)

REQUIRED_COLS = [
    "airline",
    "source_city",
    "departure_time",
    "stops",
    "arrival_time",
    "destination_city",
    "class",
    "duration",
    "days_left",
]

# ------------------------------------------------------------
# 0. ENSURE TABLES
# ------------------------------------------------------------
def ensure_tables():
    with engine.begin() as con:
        con.execute(text("""
            CREATE TABLE IF NOT EXISTS prediction_runs (
                id SERIAL PRIMARY KEY,
                filename TEXT,
                n_rows INT,
                status TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))

        con.execute(text("""
            CREATE TABLE IF NOT EXISTS processed_files (
                filename TEXT PRIMARY KEY
            );
        """))

# ------------------------------------------------------------
# 1. CHECK FOR NEW GOOD FILES
# ------------------------------------------------------------
def check_for_new_data(**context):
    ensure_tables()

    all_files = sorted(glob.glob(str(pathlib.Path(GOOD_DIR) / "*.csv")))
    if not all_files:
        raise AirflowSkipException("No good_data files found.")

    with engine.begin() as con:
        processed = {
            r[0] for r in con.execute(text("SELECT filename FROM processed_files"))
        }

    new_files = [
        f for f in all_files if os.path.basename(f) not in processed
    ]

    if not new_files:
        raise AirflowSkipException("No new files to process.")

    print(f"[INFO] New files detected: {new_files}")
    context["ti"].xcom_push(key="files", value=new_files)

# ------------------------------------------------------------
# 2. MAKE PREDICTIONS USING API
# ------------------------------------------------------------
def make_predictions(**context):
    files = context["ti"].xcom_pull(key="files")

    pathlib.Path(PRED_DIR).mkdir(parents=True, exist_ok=True)

    for fp in files:
        fname = os.path.basename(fp)
        print(f"[INFO] Predicting → {fname}")

        try:
            df = pd.read_csv(fp)
            if df.empty:
                raise ValueError("Empty file.")

            missing = [c for c in REQUIRED_COLS if c not in df.columns]
            if missing:
                raise ValueError(f"Missing columns: {missing}")

            df = df[REQUIRED_COLS].fillna("")

            payload = {
                "source": "scheduled",
                "records": df.to_dict(orient="records"),
            }

            r = requests.post(f"{API_URL}/predict", json=payload, timeout=40)
            r.raise_for_status()

            result_df = pd.DataFrame(r.json())

            out_path = pathlib.Path(PRED_DIR) / f"pred_{fname}"
            result_df.to_csv(out_path, index=False)

            print(f"[INFO] Saved predictions → {out_path}")

            with engine.begin() as con:
                con.execute(
                    text("""
                        INSERT INTO prediction_runs (filename, n_rows, status)
                        VALUES (:f, :n, 'SUCCESS')
                    """),
                    {"f": fname, "n": len(result_df)},
                )

                con.execute(
                    text("""
                        INSERT INTO processed_files (filename)
                        VALUES (:f)
                        ON CONFLICT (filename) DO NOTHING
                    """),
                    {"f": fname},
                )

        except Exception as e:
            print(f"[ERROR] Prediction failed → {fname}: {e}")
            with engine.begin() as con:
                con.execute(
                    text("""
                        INSERT INTO prediction_runs (filename, n_rows, status)
                        VALUES (:f, 0, 'FAILED')
                    """),
                    {"f": fname},
                )

# ------------------------------------------------------------
# DAG
# ------------------------------------------------------------
with DAG(
    dag_id="prediction_dag",
    start_date=days_ago(1),
    schedule_interval="*/2 * * * *",
    catchup=False,
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(seconds=10),
    },
    tags=["prediction"],
) as dag:

    t1 = PythonOperator(
        task_id="check_for_new_data",
        python_callable=check_for_new_data,
    )

    t2 = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions,
    )

    t1 >> t2