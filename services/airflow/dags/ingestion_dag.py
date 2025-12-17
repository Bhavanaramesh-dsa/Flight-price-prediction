import os
import random
import pathlib

import pandas as pd
import requests
from sqlalchemy import create_engine, text

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException

import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.render.renderer import ValidationResultsPageRenderer
from great_expectations.render.view import DefaultJinjaPageView

from row_validator import validate_dataframe_row_level


# -------------------------------------------------------
# PATH CONFIG
# -------------------------------------------------------
RAW_DIR = os.getenv("RAW_DATA_DIR", "/opt/airflow/data/raw_data")
GOOD_DIR = os.getenv("GOOD_DATA_DIR", "/opt/airflow/data/good_data")
BAD_DIR = os.getenv("BAD_DATA_DIR", "/opt/airflow/data/bad_data")

REPORT_DIR = "/opt/airflow/data/reports"
GX_DIR = "/opt/airflow/gx"

APP_DB = os.getenv(
    "APP_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@postgres:5432/predictions"
)

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

for d in [RAW_DIR, GOOD_DIR, BAD_DIR, REPORT_DIR]:
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)

engine = create_engine(APP_DB, pool_pre_ping=True)


# -------------------------------------------------------
# 1. Select random raw file  (FIX: return path)
# -------------------------------------------------------
def read_data(**context):
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]
    if not files:
        raise AirflowSkipException("No raw files found.")

    filename = random.choice(files)
    path = str(pathlib.Path(RAW_DIR) / filename)

    context["ti"].xcom_push(key="filepath", value=path)

    # FIX — Airflow stores return_value in XCom
    return path


# -------------------------------------------------------
# 2. Row-level validation (unchanged except XCom guard)
# -------------------------------------------------------
def validate_data(**context):
    fp = context["ti"].xcom_pull(key="filepath")

    if not fp:
        raise ValueError("Missing XCom 'filepath'. read_data did not return correctly.")

    df = pd.read_csv(fp)
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")

    good_df, bad_df, issues = validate_dataframe_row_level(df)

    n_rows = len(df)
    n_good = len(good_df)
    n_bad = len(bad_df)

    ratio = n_bad / max(n_rows, 1)

    if ratio == 0:
        severity = "none"
    elif ratio < 0.05:
        severity = "low"
    elif ratio < 0.20:
        severity = "medium"
    else:
        severity = "high"

    context["ti"].xcom_push(
        key="validation",
        value={
            "n_rows": n_rows,
            "n_good": n_good,
            "n_bad": n_bad,
            "severity": severity,
            "good_records": good_df.to_dict(orient="records"),
            "bad_records": bad_df.to_dict(orient="records"),
            "issues": issues,
        }
    )


# -------------------------------------------------------
# 3. Great Expectations validation (unchanged)
# -------------------------------------------------------
def ge_validate(**context):
    fp = context["ti"].xcom_pull(key="filepath")
    filename = pathlib.Path(fp).stem

    report_path = pathlib.Path(REPORT_DIR) / f"{filename}_report.html"

    try:
        ctx = gx.get_context(context_root_dir=GX_DIR)

        batch_request = RuntimeBatchRequest(
            datasource_name="flight_raw_files",
            data_connector_name="runtime_data_connector",
            data_asset_name="raw_csvs",
            runtime_parameters={"path": fp},
            batch_identifiers={"default": filename},
        )

        validator = ctx.get_validator(
            batch_request=batch_request,
            expectation_suite_name="flight_raw_expectations"
        )

        results = validator.validate()

        renderer = ValidationResultsPageRenderer()
        rendered = renderer.render(validation_results=results)
        html = DefaultJinjaPageView().render(rendered)

        report_path.write_text(html)
        context["ti"].xcom_push(key="ge_result", value=results.success)

    except Exception as e:
        fallback = f"""
        <html><body>
        <h2>GE Error</h2>
        <p>{filename}</p>
        <pre>{str(e)}</pre>
        </body></html>
        """
        report_path.write_text(fallback)
        context["ti"].xcom_push(key="ge_result", value=False)


# -------------------------------------------------------
# 4. Save statistics (unchanged)
# -------------------------------------------------------
def save_statistics(**context):
    fp = context["ti"].xcom_pull(key="filepath")
    filename = pathlib.Path(fp).stem
    v = context["ti"].xcom_pull(key="validation")
    ge_result = context["ti"].xcom_pull(key="ge_result")

    report_url = f"http://localhost:8000/reports/{filename}_report.html"

    with engine.begin() as con:
        con.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_stats (
                id SERIAL PRIMARY KEY,
                filename TEXT,
                n_rows INT,
                n_valid INT,
                n_invalid INT,
                severity TEXT,
                report_path TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                success BOOLEAN DEFAULT false
            );
        """))

        con.execute(text("""
            INSERT INTO ingestion_stats
                (filename, n_rows, n_valid, n_invalid, severity, report_path, success)
            VALUES
                (:f, :nr, :nv, :ni, :sev, :rp, :s)
        """), dict(
            f=filename + ".csv",
            nr=v["n_rows"],
            nv=v["n_good"],
            ni=v["n_bad"],
            sev=v["severity"],
            rp=report_url,
            s=ge_result
        ))

        for issue in v["issues"]:
            con.execute(text("""
                INSERT INTO data_issues (filename, row_number, error_type)
                VALUES (:f, :rn, :et)
            """), dict(
                f=filename + ".csv",
                rn=issue["row_number"],
                et=issue["error_type"]
            ))


# -------------------------------------------------------
# 5. Save good/bad files (unchanged)
# -------------------------------------------------------
def save_file(**context):
    fp = context["ti"].xcom_pull(key="filepath")
    filename = pathlib.Path(fp).stem
    v = context["ti"].xcom_pull(key="validation")

    if v["good_records"]:
        pd.DataFrame(v["good_records"]).to_csv(f"{GOOD_DIR}/{filename}_good.csv", index=False)

    if v["bad_records"]:
        pd.DataFrame(v["bad_records"]).to_csv(f"{BAD_DIR}/{filename}_bad.csv", index=False)

    if os.path.exists(fp):
        os.remove(fp)


# -------------------------------------------------------
# 6. Send Teams alert (unchanged)
# -------------------------------------------------------
def send_alerts(**context):
    if not TEAMS_WEBHOOK_URL:
        return

    v = context["ti"].xcom_pull(key="validation")
    fp = context["ti"].xcom_pull(key="filepath")
    filename = pathlib.Path(fp).stem

    report_url = f"http://localhost:8000/reports/{filename}_report.html"

    msg = f"""
**DSP Ingestion Status**
- Total Rows: {v['n_rows']}
- Valid: {v['n_good']}
- Invalid: {v['n_bad']}
- Severity: {v['severity']}
👉 **[Open GE Report]({report_url})**
"""

    try:
        requests.post(TEAMS_WEBHOOK_URL, json={"text": msg}, timeout=5)
    except Exception:
        pass


# -------------------------------------------------------
# DAG
# -------------------------------------------------------
default_args = {"owner": "airflow", "retries": 0}

with DAG(
    dag_id="ingestion_dag",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="*/1 * * * *",
    catchup=False,
    tags=["validation", "ingestion"],
) as dag:

    t1 = PythonOperator(task_id="read_data", python_callable=read_data)
    t2 = PythonOperator(task_id="validate_data", python_callable=validate_data)
    t3 = PythonOperator(task_id="ge_validate", python_callable=ge_validate)
    t4 = PythonOperator(task_id="save_statistics", python_callable=save_statistics)
    t5 = PythonOperator(task_id="save_file", python_callable=save_file)
    t6 = PythonOperator(task_id="send_alerts", python_callable=send_alerts)

    t1 >> t2 >> t3 >> [t4, t5, t6]