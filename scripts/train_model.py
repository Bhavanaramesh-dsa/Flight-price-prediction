import os
import pathlib
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sqlalchemy import create_engine, text


# ---------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------
DATA_PATH = os.getenv("TRAIN_DATA_PATH", "/app/dataset/flights.csv")
df = pd.read_csv(DATA_PATH)

# Remove ANY unnamed index column (best practice)
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

TARGET = "price"

FEATURES = [
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

X = df[FEATURES]
y = df[TARGET]


# ---------------------------------------------------------
# 2. Preprocessing
# ---------------------------------------------------------
numeric_cols = ["duration", "days_left"]
categorical_cols = [c for c in FEATURES if c not in numeric_cols]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", StandardScaler(), numeric_cols),
    ]
)


# ---------------------------------------------------------
# 3. Pipeline (IMPORTANT: name must be 'preprocessor')
# ---------------------------------------------------------
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", LinearRegression()),
    ]
)


# ---------------------------------------------------------
# 4. Train model
# ---------------------------------------------------------
pipeline.fit(X, y)


# ---------------------------------------------------------
# 5. Save model bundle (pipeline + feature order)
# ---------------------------------------------------------
bundle = {"pipeline": pipeline, "feature_order": FEATURES}

pathlib.Path("models").mkdir(parents=True, exist_ok=True)
joblib.dump(bundle, "models/model.joblib")

print("MODEL TRAINING COMPLETE.")
print("Saved to: models/model.joblib")


# ---------------------------------------------------------
# 6. Save training stats for Grafana drift monitoring
# ---------------------------------------------------------
DB_URL = os.getenv(
    "APP_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@postgres:5432/predictions",
)

try:
    duration_mean = float(df["duration"].mean())
    duration_std = float(df["duration"].std())

    engine = create_engine(DB_URL, pool_pre_ping=True)

    with engine.begin() as con:
        con.execute(
            text("""
                CREATE TABLE IF NOT EXISTS training_stats (
                    id SERIAL PRIMARY KEY,
                    duration_mean FLOAT NOT NULL,
                    duration_std FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
        )

        con.execute(text("DELETE FROM training_stats;"))

        con.execute(
            text("""
                INSERT INTO training_stats (duration_mean, duration_std)
                VALUES (:mean, :std)
            """),
            {"mean": duration_mean, "std": duration_std},
        )

    print(f"[INFO] Training stats saved → mean={duration_mean:.4f}, std={duration_std:.4f}")

except Exception as e:
    print(f"[WARN] Could not save training stats: {e}")