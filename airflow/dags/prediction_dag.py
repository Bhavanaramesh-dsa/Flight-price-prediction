# prediction_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pandas as pd
import requests
import logging

# === Configuration ===
GOOD_DIR = "/opt/airflow/data/good_data"
PREDICTIONS_DIR = "/opt/airflow/data/predictions"
PROCESSED_LOG = os.path.join(PREDICTIONS_DIR, "processed_files.csv")
API_URL = "http://host.docker.internal:8000/predict"

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Task 1: Check for new data ===
def check_for_new_data(**context):
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    if os.path.exists(PROCESSED_LOG):
        processed_files = pd.read_csv(PROCESSED_LOG)['file_name'].tolist()
    else:
        processed_files = []

    all_files = os.listdir(GOOD_DIR)
    new_files = [f for f in all_files if f not in processed_files]

    context["ti"].xcom_push(key="new_files", value=new_files)
    logging.info(f"📂 Files to process: {new_files}")


# === Task 2: Make predictions ===
def make_predictions(**context):
    new_files = context["ti"].xcom_pull(key="new_files")
    if not new_files:
        logging.info("✅ No new files to process.")
        return

    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    # Map your dataset’s columns to model expected columns
    column_mapping = {
        "airline": "Airline",
        "source_city": "Source",
        "destination_city": "Destination",
        "stops": "Total_Stops",
        "departure_time": "Dep_Time",
        "arrival_time": "Arrival_Time",
        "duration": "Duration"
    }

    required_cols = ["Airline", "Source", "Destination", "Total_Stops", "Dep_Time", "Arrival_Time", "Duration"]

    for file in new_files:
        file_path = os.path.join(GOOD_DIR, file)
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip().str.lower()

            # Rename columns using the mapping
            df.rename(columns=column_mapping, inplace=True)

            # Check missing columns
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logging.warning(f"⚠️ Skipping {file} — missing columns {missing}")
                continue

            # Send rows to FastAPI model
            predictions = []
            for _, row in df.iterrows():
                payload = {col: row[col] for col in required_cols}
                try:
                    response = requests.post(API_URL, json=payload, timeout=10)
                    if response.status_code == 200:
                        predictions.append(response.json().get("predicted_price"))
                    else:
                        logging.warning(f"⚠️ API returned {response.status_code} for {file}")
                        predictions.append(None)
                except Exception as e:
                    logging.error(f"⚠️ Request failed for {file}: {e}")
                    predictions.append(None)

            df["Predicted_Price"] = predictions

            # Save the predictions
            out = os.path.join(
                PREDICTIONS_DIR,
                f"pred_{os.path.splitext(file)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df.to_csv(out, index=False)
            logging.info(f"✅ Predictions saved: {out}")

            # Update processed log
            if os.path.exists(PROCESSED_LOG):
                processed_log = pd.read_csv(PROCESSED_LOG)
            else:
                processed_log = pd.DataFrame(columns=['file_name', 'processed_at'])
            processed_log = pd.concat([
                processed_log,
                pd.DataFrame([{'file_name': file, 'processed_at': datetime.now()}])
            ], ignore_index=True)
            processed_log.to_csv(PROCESSED_LOG, index=False)

        except Exception as e:
            logging.error(f"❌ Error processing {file}: {e}")

    logging.info("🏁 Prediction job completed.")


# === DAG Definition ===
with DAG(
    dag_id="prediction_dag",
    start_date=datetime(2025, 8, 17),
    schedule_interval="*/5 * * * *",  # every 5 minutes
    catchup=False,
    tags=["prediction"],
) as dag:

    t1 = PythonOperator(
        task_id="check_for_new_data",
        python_callable=check_for_new_data
    )

    t2 = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions
    )

    t1 >> t2
