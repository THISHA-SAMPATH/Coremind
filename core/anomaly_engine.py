"""
core/anomaly_engine.py

The shared statistical core of CoreMind. Every skill pack (Sentinel,
FinSight, future packs) feeds numeric feature vectors into the SAME
Isolation Forest model here -- only the feature extraction differs per
domain. This is the reusable engine that makes CoreMind a platform
rather than two separate apps.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyEngine:
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        contamination: expected proportion of anomalies in the data.
        Tune this per skill pack if needed (e.g. finance data might have
        fewer true anomalies than network traffic).
        """
        self.model = IsolationForest(
            contamination=contamination, random_state=random_state
        )
        self._fitted = False

    @staticmethod
    def _numeric_only(df: pd.DataFrame) -> pd.DataFrame:
        """Isolation Forest only accepts numeric input. Non-numeric columns
        (timestamps, merchant names, etc.) are kept in the output for
        context/prompts but excluded from the model itself."""
        return df.select_dtypes(include="number")

    def fit(self, features: pd.DataFrame):
        self.model.fit(self._numeric_only(features))
        self._fitted = True
        return self

    def score(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Returns the original dataframe (all columns, numeric and non-numeric)
        with two extra columns:
          - anomaly_score: lower = more anomalous
          - is_anomaly: True/False
        """
        numeric = self._numeric_only(features)
        if numeric.empty:
            raise ValueError(
                "No numeric columns found for anomaly detection. "
                "Check your skill's feature_extractor.py."
            )

        if not self._fitted:
            self.fit(features)

        scores = self.model.decision_function(numeric)
        preds = self.model.predict(numeric)  # -1 = anomaly, 1 = normal

        result = features.copy()
        result["anomaly_score"] = scores
        result["is_anomaly"] = preds == -1
        return result.sort_values("anomaly_score")


def fit_and_score(features: pd.DataFrame, contamination: float = 0.1) -> pd.DataFrame:
    """Convenience one-liner used by skill pack feature extractors."""
    engine = AnomalyEngine(contamination=contamination)
    return engine.score(features)
