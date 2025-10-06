import os
import random
import shutil
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException

# Paths matched to your docker-compose mounts
RAW_DIR = "/opt/airflow/data/raw_data"
GOOD_DIR = "/opt/airflow/data/good_data"

def read_data(**context):
    os.makedirs(RAW_DIR, exist_ok=True)   # avoid FileNotFoundError
    files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".csv")]
    if not files:
        # no raw files -> skip this run (safe)
        print(f"[read_data] No CSV files in {RAW_DIR}")
        raise AirflowSkipException("No raw files available")
    chosen = random.choice(files)
    file_path = os.path.join(RAW_DIR, chosen)
    print(f"[read_data] Selected: {file_path}")
    # push full path to XCom
    context["ti"].xcom_push(key="file_path", value=file_path)
    return file_path

def save_file(**context):
    file_path = context["ti"].xcom_pull(key="file_path", task_ids="read_data")
    if not file_path:
        raise ValueError("save_file: no file_path found in XCom")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"save_file: file not found: {file_path}")

    os.makedirs(GOOD_DIR, exist_ok=True)
    dest = os.path.join(GOOD_DIR, os.path.basename(file_path))
    shutil.move(file_path, dest)
    print(f"[save_file] Moved {file_path} -> {dest}")
    return dest

default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(seconds=15),
}

with DAG(
    dag_id="data_ingestion_dag",
    default_args=default_args,
    schedule_interval="*/1 * * * *",  # every 1 minute
    start_date=datetime(2025, 10, 1),
    catchup=False,
    max_active_runs=1,
    tags=["ingestion"],
) as dag:

    t_read = PythonOperator(
        task_id="read_data",
        python_callable=read_data,
        provide_context=True,
    )

    t_save = PythonOperator(
        task_id="save_file",
        python_callable=save_file,
        provide_context=True,
    )

    t_read >> t_save
