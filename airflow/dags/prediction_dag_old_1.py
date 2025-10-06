"""
Prediction DAG (compliant version)
- check_for_new_data: scans /opt/airflow/data/good_data for new files not in processed log
                      → if none: raises AirflowSkipException to skip entire DAG run
- make_predictions: reads new files, calls prediction API, saves output CSVs
Schedule: every 2 minutes
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from typing import List

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException
from airflow.utils.trigger_rule import TriggerRule

GOOD_DIR = "/opt/airflow/data/good_data"
PREDICTIONS_DIR = "/opt/airflow/data/predictions"
PROCESSED_LOG = os.path.join(PREDICTIONS_DIR, "processed_files.csv")
API_URL = os.environ.get("MODEL_API_URL", "http://host.docker.internal:8000/predict")

def _read_processed() -> set:
    if not os.path.exists(PROCESSED_LOG):
        return set()
    with open(PROCESSED_LOG, newline="") as fh:
        return {r["file_name"] for r in csv.DictReader(fh)}

def _append_processed(file_name: str):
    header_needed = not os.path.exists(PROCESSED_LOG)
    with open(PROCESSED_LOG, "a", newline="") as fh:
        writer = csv.writer(fh)
        if header_needed:
            writer.writerow(["file_name", "processed_at"])
        writer.writerow([file_name, datetime.utcnow().isoformat()])

def check_for_new_data(**context):
    os.makedirs(GOOD_DIR, exist_ok=True)
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    all_files = sorted(f for f in os.listdir(GOOD_DIR) if f.lower().endswith(".csv"))
    processed = _read_processed()
    new_files = [f for f in all_files if f not in processed]

    if not new_files:
        print("[check_for_new_data] No new files → skipping DAG run")
        raise AirflowSkipException("No new files to process")

    print(f"[check_for_new_data] Found new files: {new_files}")
    context["ti"].xcom_push(key="new_files", value=new_files)
    return new_files

def make_predictions(**context):
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_data")
    if not new_files:
        print("[make_predictions] No files received from XCom")
        return

    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    for fname in new_files:
        path = os.path.join(GOOD_DIR, fname)
        if not os.path.exists(path):
            print(f"[make_predictions] File missing: {path}")
            _append_processed(fname)
            continue

        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))

        try:
            resp = requests.post(API_URL, json=rows, timeout=60)
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:
            print(f"[make_predictions] API error for {fname}: {exc}")
            out_path = os.path.join(PREDICTIONS_DIR, f"pred_failed_{fname}")
            with open(out_path, "w", newline="", encoding="utf-8") as outfh:
                writer = csv.writer(outfh)
                writer.writerow(["error"])
                writer.writerow([str(exc)])
            _append_processed(fname)
            continue

        preds = None
        if isinstance(body, dict) and "predictions" in body:
            preds = body["predictions"]
        elif isinstance(body, list) and len(body) == len(rows):
            preds = body
        elif isinstance(body, dict) and "predicted_price" in body and len(rows) == 1:
            preds = [body["predicted_price"]]
        else:
            try:
                preds = list(body)
            except Exception:
                preds = None

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        out_file = os.path.join(PREDICTIONS_DIR, f"pred_{fname.rsplit('.',1)[0]}_{timestamp}.csv")

        if preds and len(preds) == len(rows):
            fieldnames = list(rows[0].keys()) + ["Predicted_Price"]
            with open(out_file, "w", newline="", encoding="utf-8") as outfh:
                writer = csv.DictWriter(outfh, fieldnames=fieldnames)
                writer.writeheader()
                for r, p in zip(rows, preds):
                    r["Predicted_Price"] = p
                    writer.writerow(r)
            print(f"[make_predictions] Saved predictions to {out_file}")
        else:
            with open(out_file, "w", encoding="utf-8") as outfh:
                outfh.write(json.dumps(body, indent=2, default=str))
            print(f"[make_predictions] Saved raw response to {out_file} (prediction mismatch)")

        _append_processed(fname)

default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(seconds=15),
}

with DAG(
    dag_id="prediction_dag",
    default_args=default_args,
    schedule_interval="*/2 * * * *",
    start_date=datetime(2025, 10, 1),
    catchup=False,
    max_active_runs=1,
    tags=["prediction"],
) as dag:

    t_check = PythonOperator(
        task_id="check_for_new_data",
        python_callable=check_for_new_data,
        provide_context=True,
    )

    t_predict = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_SUCCESS,  # Only run if check_for_new_data succeeds
    )

    t_check >> t_predict
