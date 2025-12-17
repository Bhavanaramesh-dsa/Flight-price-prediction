import pandas as pd

# Valid categorical values
VALID_AIRLINES = ["SpiceJet", "IndiGo", "Air India", "GoAir", "Vistara", "AirAsia"]
VALID_CITIES = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"]
VALID_TIMES = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]
VALID_STOPS = ["zero", "one", "two_or_more"]
VALID_CLASSES = ["Economy", "Business"]


def classify_errors(row):
    errors = []

    # Required columns (NO "flight" column)
    required_cols = [
        "airline", "source_city", "destination_city",
        "departure_time", "arrival_time", "stops",
        "class", "duration", "days_left", "price"
    ]

    # Missing required values
    for col in required_cols:
        if col not in row or pd.isna(row[col]):
            errors.append("missing_value")
            return errors

    # Invalid categorical values
    if row["airline"] not in VALID_AIRLINES:
        errors.append("invalid_airline")

    if row["source_city"] not in VALID_CITIES:
        errors.append("invalid_source_city")

    if row["destination_city"] not in VALID_CITIES:
        errors.append("invalid_destination_city")

    if row["departure_time"] not in VALID_TIMES:
        errors.append("invalid_departure_time")

    if row["arrival_time"] not in VALID_TIMES:
        errors.append("invalid_arrival_time")

    if row["stops"] not in VALID_STOPS:
        errors.append("invalid_stops")

    if row["class"] not in VALID_CLASSES:
        errors.append("invalid_class")

    # Numeric validation
    try:
        duration = float(row["duration"])
        if duration < 0 or duration > 30:
            errors.append("invalid_duration")
    except:
        errors.append("invalid_duration")

    try:
        days = float(row["days_left"])
        if days < 0 or days > 365:
            errors.append("invalid_days_left")
    except:
        errors.append("invalid_days_left")

    try:
        price = float(row["price"])
        if price < 0:
            errors.append("invalid_price")
    except:
        errors.append("invalid_price")

    return errors


def validate_dataframe_row_level(df):
    good_rows = []
    bad_rows = []
    issue_records = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        errors = classify_errors(row_dict)

        if len(errors) == 0:
            good_rows.append(row_dict)
        else:
            bad_rows.append(row_dict)
            for e in errors:
                issue_records.append({
                    "row_number": idx,
                    "error_type": e
                })

    return (
        pd.DataFrame(good_rows),
        pd.DataFrame(bad_rows),
        issue_records
    )