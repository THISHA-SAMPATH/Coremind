"""
skills/studymate/feature_extractor.py

Turns raw study/quiz performance rows into numeric features for the
shared AnomalyEngine. Same engine as Sentinel and FinSight -- proves
CoreMind generalizes beyond networks and finance.
"""

import pandas as pd


def extract_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    features = raw_df.copy()

    for col in ["score_pct", "avg_time_sec", "attempts"]:
        features[col] = pd.to_numeric(features[col], errors="coerce")

    features = features.dropna(subset=["score_pct", "avg_time_sec", "attempts"])

    # Only consider topics scoring below the student's own average --
    # we only want to flag weak spots, not high-scoring outliers.
    threshold = features["score_pct"].mean()
    features = features[features["score_pct"] < threshold].reset_index(drop=True)

    return features
