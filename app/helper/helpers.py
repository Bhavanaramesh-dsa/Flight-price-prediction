import os
import pandas as pd
import joblib
from catboost import CatBoostRegressor
from datetime import datetime

#  Model Loading
model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'catboost_flight_price_model.cbm')
columns_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'model_columns.pkl')

model = CatBoostRegressor()
model.load_model(model_path)
model_columns = joblib.load(columns_path)

# Helper Functions


def safe_parse_datetime(dt_str: str):
    """Try multiple datetime formats like '04:25 22 Mar' or '04:25 22/03/2019'."""
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    possible_formats = [
        "%H:%M %d/%m/%Y",
        "%H:%M %d %b",
        "%H:%M %d %B",
    ]
    for fmt in possible_formats:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    try:
        return pd.to_datetime(dt_str, errors="coerce")
    except Exception:
        return None


def duration_to_minutes(duration: str) -> int:
    total_mins = 0
    if not duration:
        return total_mins
    for part in duration.split():
        if 'h' in part:
            total_mins += int(part.replace('h', '')) * 60
        elif 'm' in part:
            total_mins += int(part.replace('m', ''))
    return total_mins


def parse_total_stops(value: str) -> int:
    if not value:
        return 0
    value = value.strip().lower()
    if "non" in value:
        return 0
    for token in value.split():
        if token.isdigit():
            return int(token)
    return 0


def preprocess_input(input_dict):
    dep_time = safe_parse_datetime(input_dict.get('Dep_Time'))
    arr_time = safe_parse_datetime(input_dict.get('Arrival_Time'))

    if dep_time is None or arr_time is None:
        raise ValueError(f"Unable to parse Dep_Time or Arrival_Time: {input_dict}")

    duration = input_dict.get("Duration", "")
    duration_mins = duration_to_minutes(duration)

    base_dict = {
        "Total_Stops": parse_total_stops(input_dict.get("Total_Stops", "")),
        "journey_day": datetime.strptime(input_dict["Date_of_Journey"], "%d/%m/%Y").day,
        "journey_month": datetime.strptime(input_dict["Date_of_Journey"], "%d/%m/%Y").month,
        "dep_hour": dep_time.hour,
        "dep_minute": dep_time.minute,
        "arrival_hour": arr_time.hour,
        "arrival_minute": arr_time.minute,
        "duration_mins": duration_mins,
    }

    df = pd.DataFrame([base_dict])
    categorical_columns = ["Airline", "Source", "Destination"]

    for col in categorical_columns:
        unique_vals = [c for c in model_columns if c.startswith(col + "_")]
        for val in unique_vals:
            category = val.split("_", 1)[1]
            df[val] = 1 if input_dict[col] == category else 0

    missing_cols = set(model_columns) - set(df.columns)
    for col in missing_cols:
        df[col] = 0

    return df[model_columns]


def predict_price(input_dict):
    df = preprocess_input(input_dict)
    return model.predict(df)[0]


def predict_flight_price_util(data: dict) -> float:
    return float(predict_price(data))
