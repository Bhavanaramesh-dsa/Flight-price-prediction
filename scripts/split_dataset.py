#!/usr/bin/env python3
import argparse
import pandas as pd
from pathlib import Path
import math


def parse_args():
    parser = argparse.ArgumentParser(description="Split dataset into multiple CSV chunks.")
    
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input CSV file (flights_errors.csv)"
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for raw CSV files"
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=50,
        help="Rows per output file (default = 50)"
    )

    return parser.parse_args()


def split_dataset(input_file, output_dir, rows_per_file):
    print(f"[INFO] Loading dataset: {input_file}")
    df = pd.read_csv(input_file)

    total_rows = len(df)
    print(f"[INFO] Total rows: {total_rows}")

    # Calculate number of files
    n_files = math.ceil(total_rows / rows_per_file)
    print(f"[INFO] Will create {n_files} files, each with {rows_per_file} rows")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(n_files):
        start = i * rows_per_file
        end = start + rows_per_file
        chunk = df.iloc[start:end]

        out_path = out_dir / f"raw_{i+1:04}.csv"
        chunk.to_csv(out_path, index=False)

    print(f"[SUCCESS] Created {n_files} raw files in {out_dir}")


if __name__ == "__main__":
    args = parse_args()
    split_dataset(args.input, args.out, args.rows)