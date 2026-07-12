"""
skills/finsight/feature_extractor.py

Turns raw bank transaction rows into numeric features for the shared
AnomalyEngine. Same engine as Sentinel -- only this extractor differs.
"""

import pandas as pd


def extract_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects raw_df with columns: date, merchant, amount, hour_of_day

    Adds merchant_frequency (how many times this merchant appears this
    month) as a feature -- duplicate/unusual-frequency charges are a
    classic fraud signal.
    """
    features = raw_df.copy()

    features["amount"] = pd.to_numeric(features["amount"], errors="coerce")
    features["hour_of_day"] = pd.to_numeric(features["hour_of_day"], errors="coerce")
    features = features.dropna(subset=["amount", "hour_of_day"])

    merchant_counts = features["merchant"].value_counts()
    features["merchant_frequency"] = features["merchant"].map(merchant_counts)

    return features
