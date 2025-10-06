import pandas as pd
import numpy as np
import os

def split_file(n_files=10):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(base_dir, "../dataset/dataset.csv")
    out_dir = os.path.join(base_dir, "../raw-data")

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"❌ File not found: {input_csv}")

    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(input_csv)
    chunks = np.array_split(df, n_files)

    for i, chunk in enumerate(chunks):
        path = os.path.join(out_dir, f"data_part_{i}.csv")
        chunk.to_csv(path, index=False)
        print(f"✅ Wrote {path}")

if __name__ == "__main__":
    split_file()
