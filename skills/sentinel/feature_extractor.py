"""
skills/sentinel/feature_extractor.py

Turns raw network log rows into numeric features for the shared
AnomalyEngine. This is the ONLY domain-specific code Sentinel needs --
everything else (anomaly detection, LLM explanation) comes from core/.
"""

import pandas as pd


def extract_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects raw_df with columns:
        timestamp, latency_ms, packet_loss_pct, bandwidth_mbps, cpu_temp_c

    Returns a numeric feature dataframe (keeps original columns too, so
    the prompt template can reference them after scoring).
    """
    features = raw_df.copy()

    # Ensure numeric types
    for col in ["latency_ms", "packet_loss_pct", "bandwidth_mbps", "cpu_temp_c"]:
        features[col] = pd.to_numeric(features[col], errors="coerce")

    features = features.dropna(subset=[
        "latency_ms", "packet_loss_pct", "bandwidth_mbps", "cpu_temp_c"
    ])

    return features
