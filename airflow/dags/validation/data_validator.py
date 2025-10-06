import pandas as pd

def validate_file(file_path):
    stats = {
        "rows": 0,
        "valid": 0,
        "invalid": 0,
        "errors": []
    }

    try:
        df = pd.read_csv(file_path)
        stats["rows"] = len(df)
        valid_df = df.dropna()
        stats["valid"] = len(valid_df)
        stats["invalid"] = stats["rows"] - stats["valid"]

        if stats["invalid"] > 0:
            stats["errors"].append("Missing values found")

        return df, stats

    except Exception as e:
        stats["errors"].append(str(e))
        return pd.DataFrame(), stats

