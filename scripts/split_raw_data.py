import pandas as pd
import numpy as np
import os

def split_main_dataset(input_csv, output_folder="raw-data", n_files=1000):
    """
    Split a main CSV dataset into smaller CSV files named 'prediction_XXXX.csv'
    and store them in the 'raw-data' folder.
    
    Parameters:
        input_csv (str): Path to the main dataset (CSV file).
        output_folder (str): Folder where smaller CSV files will be stored.
        n_files (int): Number of output files (default: 1000).
    """
    
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"❌ File not found: {input_csv}")

    os.makedirs(output_folder, exist_ok=True)
    
    # Load dataset
    df = pd.read_csv(input_csv)
    total_rows = len(df)
    
    # Split dataset into n_files
    chunks = np.array_split(df, n_files)
    
    for i, chunk in enumerate(chunks):
        output_path = os.path.join(output_folder, f"raw-data_{i+1:04d}.csv")
        chunk.to_csv(output_path, index=False)
        print(f"✅ Saved {output_path} ({len(chunk)} rows)")
    
    print(f"\n🎉 Done! Split {total_rows} rows into {n_files} files in '{output_folder}'.")

if __name__ == "__main__":
    # Example usage
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, "../dataset/dataset.csv")
    output_folder = os.path.join(base_dir, "../airflow/data/raw-data")
    
    split_main_dataset(input_csv, output_folder, n_files=1000)
