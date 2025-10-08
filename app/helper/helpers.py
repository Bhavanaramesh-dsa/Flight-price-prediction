import os
import pandas as pd
import joblib
from catboost import CatBoostRegressor
from datetime import datetime

# Load model and columns once when module loads (singleton pattern)
model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'catboost_flight_price_model.cbm')
columns_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'model_columns.pkl')

model = CatBoostRegressor()
model.load_model(model_path)

model_columns = joblib.load(columns_path)

def preprocess_input(input_dict):
 
    # 1. Map Total_Stops
    stops_mapping = {
        'non-stop': 0,
        '1 stop': 1,
        '2 stops': 2,
        '3 stops': 3,
        '4 stops': 4
    }
    total_stops = stops_mapping.get(input_dict['Total_Stops'].lower(), 0)

    date = pd.to_datetime(input_dict['Date_of_Journey'], format='%d/%m/%Y')
    journey_day = date.day
    journey_month = date.month

    dep_time = pd.to_datetime(input_dict['Dep_Time'], format='%H:%M')
    dep_hour = dep_time.hour
    dep_minute = dep_time.minute

    try:
        arrival_time = pd.to_datetime(input_dict['Arrival_Time'], format='%H:%M %d/%m/%Y')
    except Exception:
        arrival_time = pd.to_datetime(input_dict['Arrival_Time'], format='%H:%M')
    arrival_hour = arrival_time.hour
    arrival_minute = arrival_time.minute

    def duration_to_minutes(duration):
        time_parts = duration.split()
        total_mins = 0
        for part in time_parts:
            if 'h' in part:
                total_mins += int(part.replace('h', ''))
                total_mins *= 60
            if 'm' in part:
                total_mins += int(part.replace('m', ''))
        return total_mins

    duration_mins = duration_to_minutes(input_dict['Duration'])

    base_dict = {
        'Total_Stops': total_stops,
        'journey_day': journey_day,
        'journey_month': journey_month,
        'dep_hour': dep_hour,
        'dep_minute': dep_minute,
        'arrival_hour': arrival_hour,
        'arrival_minute': arrival_minute,
        'duration_mins': duration_mins
    }

    df = pd.DataFrame([base_dict])

    categorical_columns = ['Airline', 'Source', 'Destination']

    for col in categorical_columns:
        unique_vals = [c for c in model_columns if c.startswith(col + '_')]
        for val in unique_vals:
            category = val.split('_', 1)[1]
            df[val] = 1 if input_dict[col] == category else 0

    missing_cols = set(model_columns) - set(df.columns)
    for col in missing_cols:
        df[col] = 0

    df = df[model_columns]

    return df


def predict_price(input_dict):
  
    df = preprocess_input(input_dict)
    prediction = model.predict(df)[0]
    return prediction


def predict_flight_price_util(data: dict) -> float:
  
    return float(predict_price(data))


def parse_datetime(date_str: str, dep_time: str, arrival_time: str):
   
    journey_date = datetime.strptime(date_str, "%d/%m/%Y").date()
    dep_datetime = datetime.strptime(f"{dep_time} {date_str}", "%H:%M %d/%m/%Y")
    
    try:
        arrival_datetime = datetime.strptime(arrival_time, "%H:%M %d/%m/%Y")
    except ValueError:
        arrival_datetime = datetime.strptime(f"{arrival_time} {date_str}", "%H:%M %d/%m/%Y")
    
    return journey_date, dep_datetime, arrival_datetime


def duration_to_minutes(duration: str) -> int:

    total_mins = 0
    for part in duration.split():
        if 'h' in part:
            total_mins += int(part.replace('h', '')) * 60
        if 'm' in part:
            total_mins += int(part.replace('m', ''))
    return total_mins

def parse_total_stops(value: str) -> int:
    """
    Convert total stops like '1 stop', '2 stops', 'non-stop' → integer safely.
    """
    if not value:
        return 0
    value = value.strip().lower()
    if "non" in value:
        return 0
    for token in value.split():
        if token.isdigit():
            return int(token)
    return 0


# ✅ Helper: convert duration text to minutes
def duration_to_minutes(duration: str) -> int:
    total_mins = 0
    parts = duration.split()
    for part in parts:
        if 'h' in part:
            total_mins += int(part.replace('h', '')) * 60
        elif 'm' in part:
            total_mins += int(part.replace('m', ''))
    return total_mins