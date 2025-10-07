# scripts/generate_data_errors.py

import pandas as pd
import numpy as np
import random
import os
from pathlib import Path

def generate_data_errors():
    """Generate data errors in the flight price dataset"""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Define file paths
    base_dir = Path(__file__).parent.parent
    clean_data_path = base_dir / "dataset" / "dataset.csv"
    output_path = base_dir / "dataset" / "raw_data_with_errors.csv"
    
    print(" GENERATING DATA ERRORS IN FLIGHT PRICE DATASET")
    
    
    # Load your existing dataset
    try:
        df = pd.read_csv(clean_data_path)
        print(f" Loaded dataset from: {clean_data_path}")
        print(f" Original shape: {df.shape}")
        print(f" Columns: {list(df.columns)}")
    except FileNotFoundError:
        print(f" File not found: {clean_data_path}")
        print("Please ensure your dataset.csv exists in the dataset folder")
        return
    
    # Create a copy to introduce errors
    df_with_errors = df.copy()
    
    # ERROR 1: Missing required column
    print("\n1.  Removing required column")
    required_columns_to_remove = ['Airline', 'Source', 'Destination']
    for col in required_columns_to_remove:
        if col in df_with_errors.columns:
            df_with_errors.drop(columns=[col], inplace=True)
            print(f"   Removed column: {col}")
    
    # ERROR 2: Missing values in required columns
    print("\n2.  Introducing missing values")
    columns_with_missing = ['Price', 'Duration', 'Date_of_Journey']
    for col in columns_with_missing:
        if col in df_with_errors.columns:
            n_missing = min(10, len(df_with_errors) // 20)  # 5% of data
            indices = random.sample(range(len(df_with_errors)), n_missing)
            df_with_errors.loc[indices, col] = np.nan
            print(f"   Added {n_missing} missing values in {col}")
    
    # ERROR 3: Unknown category values
    print("\n3.  Adding unknown category values")
    if 'Airline' in df_with_errors.columns:
        unknown_airlines = ['SpaceJet', 'OceanAir', 'MountainFly']
        n_unknown = min(8, len(df_with_errors) // 25)
        indices = random.sample(range(len(df_with_errors)), n_unknown)
        df_with_errors.loc[indices, 'Airline'] = random.choices(unknown_airlines, k=n_unknown)
        print(f"    Added {n_unknown} unknown airline values")
    
    # ERROR 4: Invalid numeric values
    print("\n4. Adding invalid numeric values")
    if 'Duration' in df_with_errors.columns:
        n_invalid = min(5, len(df_with_errors) // 40)
        indices = random.sample(range(len(df_with_errors)), n_invalid)
        df_with_errors.loc[indices, 'Duration'] = -10
        print(f"    Added {n_invalid} negative duration values")
    
    # ERROR 5: String values in numeric column
    print("\n5.  Adding string values in numeric column")
    if 'Price' in df_with_errors.columns:
        n_strings = min(6, len(df_with_errors) // 30)
        indices = random.sample(range(len(df_with_errors)), n_strings)
        df_with_errors.loc[indices, 'Price'] = 'unknown'
        print(f"    Added {n_strings} string values in Price column")
    
    # ERROR 6: Extreme outliers
    print("\n6.  Adding extreme outliers")
    numeric_columns = ['Duration', 'Price', 'Total_Stops'] if 'Total_Stops' in df_with_errors.columns else ['Duration', 'Price']
    for col in numeric_columns:
        if col in df_with_errors.columns:
            n_outliers = min(4, len(df_with_errors) // 50)
            indices = random.sample(range(len(df_with_errors)), n_outliers)
            if col == 'Price':
                df_with_errors.loc[indices, col] = 999999
            elif col == 'Duration':
                df_with_errors.loc[indices, col] = 500
            elif col == 'Total_Stops':
                df_with_errors.loc[indices, col] = 50
            print(f"   Added {n_outliers} extreme outliers in {col}")
    
    # ERROR 7: Inconsistent date formats
    print("\n7.  Adding inconsistent date formats")
    if 'Date_of_Journey' in df_with_errors.columns:
        n_invalid_dates = min(7, len(df_with_errors) // 30)
        indices = random.sample(range(len(df_with_errors)), n_invalid_dates)
        invalid_dates = ['2025-13-40', 'invalid_date', '2024-02-30', '2023/15/01']
        df_with_errors.loc[indices, 'Date_of_Journey'] = random.choices(invalid_dates, k=n_invalid_dates)
        print(f"    Added {n_invalid_dates} invalid date formats")
    
    # ERROR 8: Inconsistent text formatting
    print("\n8.  Adding inconsistent text formatting")
    if 'Airline' in df_with_errors.columns:
        n_inconsistent = min(8, len(df_with_errors) // 25)
        indices = random.sample(range(len(df_with_errors)), n_inconsistent)
        df_with_errors.loc[indices, 'Airline'] = df_with_errors.loc[indices, 'Airline'].str.upper() + '  '
        print(f"    Added {n_inconsistent} inconsistent text formats")
    
    # Save the dataset with errors
    df_with_errors.to_csv(output_path, index=False)
    
    
    print(" DATA ERRORS GENERATION COMPLETE!")
    print(f"Dataset with errors saved as: {output_path}")
    print(f"Final shape: {df_with_errors.shape}")
    print(f"Remaining columns: {list(df_with_errors.columns)}")
    
    # Display error summary
    print("\n ERROR SUMMARY:")
    error_summary = [
        "1. Missing required columns (Airline, Source, Destination)",
        "2. Missing values in Price, Duration, Date_of_Journey",
        "3. Unknown category values in Airline",
        "4. Invalid numeric values (negative Duration)",
        "5. String values in numeric Price column",
        "6. Extreme outliers in numeric columns",
        "7. Inconsistent date formats",
        "8. Inconsistent text formatting"
    ]
    for summary in error_summary:
        print(f"    {summary}")

if __name__ == "__main__":
    generate_data_errors()