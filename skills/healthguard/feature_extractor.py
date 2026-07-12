import pandas as pd

def extract_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    features = raw_df.copy()
    for col in ["resting_hr", "sleep_hours", "steps", "active_hr"]:
        features[col] = pd.to_numeric(features[col], errors="coerce")
    features = features.dropna(subset=["resting_hr", "sleep_hours", "steps", "active_hr"])
    return features