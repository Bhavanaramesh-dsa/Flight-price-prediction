import os
import pandas as pd

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from helper.config import engine  
PREDICTIONS_DIR = "/opt/airflow/data/predictions"
PROCESSED_LOG = os.path.join(PREDICTIONS_DIR, "processed_files.csv")

# DB connection info (matches docker-compose)
DB_CONN = {
    "dbname": "predictions",
    "user": "postgres",
    "password": "Password",
    "host": "postgres",  # docker service name
    "port": "5432",
}



def save_predictions_to_db(**context):
    """
    Load the predictions CSV from previous task (via XCom)
    and save it to PostgreSQL safely — with schema auto-alignment.
    """

    # 1️⃣ Get predictions file path from XCom
    predictions_path = context["ti"].xcom_pull(key="predictions_path")

    if not predictions_path or not os.path.exists(predictions_path):
        print("⚠️ No predictions file found or invalid path in XCom.")
        return

    print(f"📂 Loading predictions from: {predictions_path}")
    df = pd.read_csv(predictions_path)

    if df.empty:
        print("⚠️ DataFrame is empty, skipping database insertion.")
        return

    # 2️⃣ Normalize column names to lowercase for PostgreSQL
    df.columns = [col.strip().lower() for col in df.columns]
    print(f"🧾 Normalized columns: {list(df.columns)}")

    table_name = "predictions"

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # 3️⃣ Drop table if schema mismatched (optional but safe for dev)
        if table_name in existing_tables:
            db_cols = [col["name"] for col in inspector.get_columns(table_name)]
            df_cols = list(df.columns)
            if set(db_cols) != set(df_cols):
                print("⚠️ Detected schema mismatch between DataFrame and DB table.")
                print(f"🗑️ Dropping old '{table_name}' table to recreate with correct schema.")
                with engine.begin() as conn:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
                df.head(0).to_sql(table_name, con=engine, index=False)
                print(f"✅ Recreated table '{table_name}' with correct columns: {df_cols}")
        else:
            print(f"🛠️ Table '{table_name}' not found — creating it now.")
            df.head(0).to_sql(table_name, con=engine, index=False)
            print(f"✅ Created new table '{table_name}' successfully.")

        # 4️⃣ Insert data
        print(f"💾 Inserting {len(df)} records into '{table_name}'...")
        df.to_sql(table_name, con=engine, if_exists="append", index=False)
        print(f"✅ {len(df)} records inserted successfully!")

    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

    print("🏁 save_predictions_to_db task completed successfully.")
