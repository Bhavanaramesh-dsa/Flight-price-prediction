
import traceback
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pandas as pd
import requests
import logging

from databaseLogic.predictionDL import save_predictions_to_db

# === Configuration ===
GOOD_DIR = "/opt/airflow/data/good_data"
PREDICTIONS_DIR = "/opt/airflow/data/predictions"
PROCESSED_LOG = os.path.join(PREDICTIONS_DIR, "processed_files.csv")
API_URL = "http://fastapi:8000/api/predict"

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def calculate_days_left(date_str):
    """Calculate number of days between today and the flight date."""
    try:
        journey_date = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        today = datetime.now()
        days_left = (journey_date - today).days
        return max(days_left, 0)
    except Exception as e:
        logging.error(f" Error parsing Date_of_Journey '{date_str}': {e}")
        return None
    

# === Task 1: Check for new data ===
def check_for_new_data(**context):
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    logging.info("Checking for new files in directory: %s", GOOD_DIR)

    if os.path.exists(PROCESSED_LOG):
        processed_files = pd.read_csv(PROCESSED_LOG)['file_name'].tolist()
        logging.info(f" Found processed log with {len(processed_files)} files.")

    else:
        processed_files = []
        logging.info(" No processed log found — assuming first run.")

    all_files = os.listdir(GOOD_DIR)
    new_files = [f for f in all_files if f not in processed_files]

    if new_files:
        logging.info(f" New files detected for processing: {new_files}")
    else:
        logging.info(" No new files found. DAG will skip predictions.")

    context["ti"].xcom_push(key="new_files", value=new_files)
    logging.info(f" Files to process: {new_files}")


# === Task 2: Make predictions ===
def make_predictions(**context):
    new_files = context["ti"].xcom_pull(key="new_files")
    if not new_files:
        logging.info(" No new files to process.")
        return

    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    # Map your dataset’s columns to model expected columns
    column_mapping = {
        "airline": "Airline",
        "source": "Source",
        "destination": "Destination",
        "total_stops": "Total_Stops",
        "date_of_journey": "Date_of_Journey",
        "dep_time": "Dep_Time",
        "arrival_time": "Arrival_Time",
        "duration": "Duration"
    }

    required_cols = ["Airline", "Source", "Destination", "Total_Stops", "Date_of_Journey","Dep_Time", "Arrival_Time", "Duration"]

    for file in new_files:
        file_path = os.path.join(GOOD_DIR, file)
        logging.info(f"Processing file: {file_path}")
        logging.info(f" Reading data from {file_path}")

        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip().str.lower()

            # Rename columns using the mapping
            df.rename(columns=column_mapping, inplace=True)
            logging.info(f" Columns after renaming: {list(df.columns)}")


            # Check missing columns
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logging.warning(f" Skipping {file} — missing columns {missing}")
                continue

            # Send rows to FastAPI model
            predictions = []
            total_rows = len(df)
            logging.info(f" Starting prediction for {total_rows} rows...")

            for idx, row in df.iterrows():
                # Calculate days_left per row
                days_left = calculate_days_left(row['Date_of_Journey'])

                payload = {
                    'Airline': row['Airline'],
                    'Source': row['Source'],
                    'Destination': row['Destination'],
                    'Total_Stops': row['Total_Stops'],
                    'Date_of_Journey': row['Date_of_Journey'],
                    'Dep_Time': row['Dep_Time'],
                    'Arrival_Time': row['Arrival_Time'],
                    'Duration': row['Duration'],
                    'days_left': days_left
                }

                logging.info(f" [Row {idx + 1}/{total_rows}] Sending payload: {payload}")

                try:
                    response = requests.post(API_URL, json=payload, timeout=10)
                    logging.info(f" API status: {response.status_code}")

                    if response.status_code == 200:
                        resp_json = response.json()
                        predicted = resp_json.get("predicted_price")
                        logging.info(f" Received prediction: {predicted}")
                        predictions.append(predicted)
                    else:
                        logging.warning(f" API returned {response.status_code}: {response.text}")
                        predictions.append(None)

                except Exception as e:
                    logging.error(f" Request failed: {e}")
                    logging.debug(traceback.format_exc())
                    predictions.append(None)

            # Attach predictions to DataFrame
            df["Predicted_Price"] = predictions
            out_path = os.path.join(
                PREDICTIONS_DIR,
                f"pred_{os.path.splitext(file)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df.to_csv(out_path, index=False)
            logging.info(f" Predictions saved to: {out_path}")

            context["ti"].xcom_push(key="predictions_path", value=out_path)

            if os.path.exists(PROCESSED_LOG):
                processed_log = pd.read_csv(PROCESSED_LOG)
            else:
                processed_log = pd.DataFrame(columns=["file_name", "processed_at"])

            processed_log = pd.concat([
                processed_log,
                pd.DataFrame([{"file_name": file, "processed_at": datetime.now()}])
            ], ignore_index=True)
            processed_log.to_csv(PROCESSED_LOG, index=False)

        except Exception as e:
            logging.error(f" Error processing {file}: {e}")
            logging.debug(traceback.format_exc())

    logging.info(" All prediction jobs completed successfully!")

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


    t3 = PythonOperator(
        task_id="save_predictions_to_db",
        python_callable=save_predictions_to_db,
        provide_context=True
    )
    t1 >> t2 >> t3
