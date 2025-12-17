import joblib
import pandas as pd
import numpy as np
import os

# Path inside Docker container
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/model.joblib")


class ModelService:
    def __init__(self):
        self.model = None
        self.feature_order = None

    # ---------------------------------------------------------
    # Load trained model + pipeline
    # ---------------------------------------------------------
    def load(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

        bundle = joblib.load(MODEL_PATH)
        self.model = bundle["pipeline"]
        self.feature_order = bundle["feature_order"]
        return self

    # ---------------------------------------------------------
    # Extract valid categories from OHE
    # ---------------------------------------------------------
    def get_valid_categories(self):
        try:
            preprocessor = self.model.named_steps["preprocessor"]
            ohe = preprocessor.named_transformers_["cat"]
            cats = ohe.categories_

            return {
                "airline": cats[0].tolist(),
                "source_city": cats[1].tolist(),
                "departure_time": cats[2].tolist(),
                "stops": cats[3].tolist(),
                "arrival_time": cats[4].tolist(),
                "destination_city": cats[5].tolist(),
                "class": cats[6].tolist(),
            }

        except Exception as e:
            print("[WARN] Could not extract categories:", e)
            return {}

    # ---------------------------------------------------------
    # Predict with FULL SANITIZATION
    # ---------------------------------------------------------
    def predict(self, records):
        df = pd.DataFrame(records)

        # Keep only expected columns
        df = df.reindex(columns=self.feature_order, fill_value=None)

        # ------------------------------------------------------
        # CLEANING LAYER
        # ------------------------------------------------------
        categorical_cols = [
            "airline", "source_city", "departure_time", "stops",
            "arrival_time", "destination_city", "class"
        ]

        numeric_cols = ["duration", "days_left"]

        # Replace empty strings
        df.replace("", pd.NA, inplace=True)

        # 1. Fill missing categorical → "Unknown"
        for col in categorical_cols:
            if col in df:
                df[col] = df[col].fillna("Unknown").astype(str)

        # 2. Convert numeric + fill missing with median
        for col in numeric_cols:
            if col in df:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].fillna(df[col].median())

        # 3. Handle unseen categories safely
        valid = self.get_valid_categories()
        for col in categorical_cols:
            if col in df and col in valid:
                df[col] = df[col].apply(
                    lambda x: x if x in valid[col] else "Unknown"
                )

        # ------------------------------------------------------
        # Ready for model
        # ------------------------------------------------------
        preds = self.model.predict(df)

        return [float(p) for p in preds]


# Global instance
model_service = ModelService()