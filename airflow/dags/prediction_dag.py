import pendulum
from datetime import timedelta
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
import os
import pandas as pd
import requests
import psycopg2
import datetime
import json

# Configuration
GOOD_DATA_PATH = '/opt/airflow/data/good_data'
API_SERVICE_URL = 'http://fastapi:8000/predict'
DB_HOST = 'postgres'
DB_PORT = '5432'
DB_NAME = 'predictions'
DB_USER = 'postgres'
DB_PASSWORD = 'Password'

# DB Connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        connect_timeout=10
    )

def setup_tracking_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                filename TEXT PRIMARY KEY,
                processed_timestamp TIMESTAMPTZ
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prediction_payloads (
                id SERIAL PRIMARY KEY,
                filename TEXT,
                full_file JSONB,
                prediction_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()

# DAG Definition
@dag(
    dag_id="prediction_dag",
    start_date=pendulum.datetime(2025, 10, 1, tz="UTC"),
    schedule=timedelta(minutes=2),
    catchup=False,
    max_active_runs=1,
    tags=["prediction"],
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "depends_on_past": False,
    },
)
def PredictionPipeline():

    @task
    def check_for_new_data():
        conn = get_db_connection()
        setup_tracking_table(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM processed_files;")
            tracked_files = {row[0] for row in cur.fetchall()}

        os.makedirs(GOOD_DATA_PATH, exist_ok=True)
        all_files = sorted(f for f in os.listdir(GOOD_DATA_PATH) if f.endswith('.csv'))
        new_files = [f for f in all_files if f not in tracked_files]

        if not new_files:
            print("No new files found. Skipping DAG run.")
            raise AirflowSkipException("No new files found.")

        print(f"Found new files: {new_files}")
        conn.close()
        return new_files

    @task(task_concurrency=2)
    def make_predictions(new_files: list):
        processed = []

        for file_name in new_files:
            file_path = os.path.join(GOOD_DATA_PATH, file_name)

            try:
                df = pd.read_csv(file_path)
                data_for_api = df.to_dict('records')

                response = requests.post(
                    API_SERVICE_URL,
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(data_for_api),
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()

                # Extract predictions from API response
                predictions = result.get("predictions", [])
                print(f"Prediction successful for {file_name} with {len(predictions)} records")

                # --- Create tables and store both input and predictions ---
                conn = get_db_connection()
                with conn.cursor() as cur:
                    # Ensure predictions table exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS predictions (
                            id SERIAL PRIMARY KEY,
                            filename TEXT,
                            predictions JSONB,
                            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

                        # Insert predictions from FastAPI
                    cur.execute("""
                            INSERT INTO predictions (filename, predictions)
                            VALUES (%s, %s);
                        """, (file_name, json.dumps(predictions)))

                        # Keep your original logic for payload tracking
                    cur.execute("""
                            INSERT INTO prediction_payloads (filename, full_file)
                            VALUES (%s, %s);
                        """, (file_name, json.dumps(data_for_api)))

                    conn.commit()
                    conn.close()


                processed.append(file_name)

            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                continue

        if processed:
            conn = get_db_connection()
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO processed_files (filename, processed_timestamp)
                    VALUES (%s, %s)
                    ON CONFLICT (filename) DO UPDATE SET processed_timestamp = EXCLUDED.processed_timestamp;
                """, [(f, timestamp) for f in processed])
            conn.commit()
            conn.close()
            print(f"Tracked {len(processed)} files in DB.")
        else:
            print("No files were successfully processed.")

    files = check_for_new_data()
    make_predictions(files)

# Instantiate DAG
prediction_dag = PredictionPipeline()
