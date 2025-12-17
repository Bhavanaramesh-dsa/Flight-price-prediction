#!/usr/bin/env python3

import argparse
import math
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Allowed values (must match your Great Expectations value_sets)
# -------------------------------------------------------------------
VALID_AIRLINES = ["SpiceJet", "IndiGo", "Air India", "GoAir", "Vistara", "AirAsia"]
VALID_CITIES = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"]
VALID_TIMES = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]
VALID_STOPS = ["zero", "one", "two_or_more"]
VALID_CLASSES = ["Economy", "Business"]

# -------------------------------------------------------------------
# Error type helpers (7 row-level error types)
# -------------------------------------------------------------------


def e1_missing_required_value(row: pd.Series) -> str:
    """
    Error 1: Missing value in a required column.
    """
    candidates = [
        "airline",
        "source_city",
        "destination_city",
        "departure_time",
        "arrival_time",
        "stops",
        "class",
        "duration",
        "days_left",
        "price",
    ]
    col = random.choice(candidates)
    row[col] = np.nan
    return f"missing_value:{col}"


def e2_unknown_categorical_value(row: pd.Series) -> str:
    """
    Error 2: Unknown categorical in airline / source_city / destination_city.
    """
    candidates = ["airline", "source_city", "destination_city"]
    col = random.choice(candidates)

    if col == "airline":
        bad_val = random.choice(["UnknownAir", "123", "??"])
    elif col in ("source_city", "destination_city"):
        bad_val = random.choice(["Paris", "Nowhere", "Atlantis"])
    else:
        bad_val = "INVALID"

    row[col] = bad_val
    return f"unknown_categorical:{col}"


def e3_invalid_time_bucket(row: pd.Series) -> str:
    """
    Error 3: Invalid time bucket for departure_time / arrival_time.
    """
    col = random.choice(["departure_time", "arrival_time"])
    bad_val = random.choice(
        ["Morning ", " late_night", "Dawn", "Midnight", "NotATime"]
    )
    row[col] = bad_val
    return f"invalid_time:{col}"


def e4_invalid_stops(row: pd.Series) -> str:
    """
    Error 4: Invalid number of stops.
    """
    bad_val = random.choice(["two", "3", "-1", "many"])
    row["stops"] = bad_val
    return "invalid_stops"


def e5_out_of_range_numeric(row: pd.Series) -> str:
    """
    Error 5: Numeric values outside allowed range.
    """
    col = random.choice(["duration", "days_left", "price"])

    if col == "duration":
        bad_val = random.choice([-5, -1, 40, 1000])
    elif col == "days_left":
        bad_val = random.choice([-10, -1, 400, 10000])
    else:  # price
        bad_val = random.choice([-100, -1, -9999])

    row[col] = bad_val
    return f"out_of_range_numeric:{col}"


def e6_string_in_numeric(row: pd.Series) -> str:
    """
    Error 6: String values in numeric fields.
    """
    col = random.choice(["duration", "days_left", "price"])
    row[col] = random.choice(["NaN", "N/A", "NotANumber", "error"])
    return f"string_in_numeric:{col}"


def e7_whitespace_in_categorical(row: pd.Series) -> str:
    """
    Error 7: Leading/trailing whitespace around categorical values.
    """
    candidates = ["airline", "source_city", "destination_city", "class"]
    col = random.choice(candidates)

    if col == "airline":
        base = random.choice(VALID_AIRLINES)
    elif col in ("source_city", "destination_city"):
        base = random.choice(VALID_CITIES)
    elif col == "class":
        base = random.choice(VALID_CLASSES)
    else:
        base = str(row[col]) if pd.notna(row[col]) else "Value"

    row[col] = f" {base} "
    return f"whitespace_categorical:{col}"


ERROR_FUNCS = [
    e1_missing_required_value,
    e2_unknown_categorical_value,
    e3_invalid_time_bucket,
    e4_invalid_stops,
    e5_out_of_range_numeric,
    e6_string_in_numeric,
    e7_whitespace_in_categorical,
]

# -------------------------------------------------------------------
# Core logic: split + inject errors
# -------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate raw CSV files with injected row-level errors."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to CLEAN flights.csv (with columns airline, source_city, ..., price)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output folder for raw files (e.g. data/raw_data)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=50,
        help="Target rows per output CSV (default: 50)",
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.1,
        help="Fraction of rows per file to corrupt (default: 0.10 = 10%)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()


def inject_errors_into_chunk(df_chunk: pd.DataFrame, error_rate: float) -> pd.DataFrame:
    df_err = df_chunk.copy(deep=True)
    n_rows = len(df_err)

    if n_rows == 0:
        return df_err

    n_corrupt = max(1, int(n_rows * error_rate))
    n_corrupt = min(n_corrupt, n_rows)

    indices = df_err.index.to_list()
    corrupt_indices = random.sample(indices, n_corrupt)

    error_counts = {}

    for idx in corrupt_indices:
        row = df_err.loc[idx]
        fn = random.choice(ERROR_FUNCS)
        err_label = fn(row)
        df_err.loc[idx] = row  # write back modified row

        error_counts[err_label] = error_counts.get(err_label, 0) + 1

    print(f"  -> injected errors: {error_counts}")
    return df_err


def main():
    args = parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    input_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading clean dataset from: {input_path}")
    df = pd.read_csv(input_path)

    expected_cols = {
        "airline",
        "source_city",
        "destination_city",
        "departure_time",
        "arrival_time",
        "stops",
        "class",
        "duration",
        "days_left",
        "price",
    }
    missing = expected_cols.difference(df.columns)
    if missing:
        print(
            f"[WARN] Input file is missing expected columns: {sorted(missing)}\n"
            f"       Great Expectations / row validation may fail on these."
        )

    df = df.sample(frac=1, random_state=args.seed).reset_index(drop=True)

    total_rows = len(df)
    rows_per_file = args.rows
    n_files = math.ceil(total_rows / rows_per_file)

    print(f"[INFO] Total rows: {total_rows}")
    print(f"[INFO] Rows per file: {rows_per_file}")
    print(f"[INFO] Files to generate: {n_files}")
    print(f"[INFO] Error rate per file: {args.error_rate:.2%}")

    for i in range(n_files):
        start = i * rows_per_file
        end = min((i + 1) * rows_per_file, total_rows)
        chunk = df.iloc[start:end]

        if len(chunk) == 0:
            continue

        print(f"[FILE {i+1}/{n_files}] rows={len(chunk)}")
        chunk_err = inject_errors_into_chunk(chunk, args.error_rate)

        out_path = out_dir / f"raw_{i+1:04}.csv"
        chunk_err.to_csv(out_path, index=False)
        print(f"  -> saved: {out_path}")

    print("[DONE] Raw files generated.")


if __name__ == "__main__":
    main()