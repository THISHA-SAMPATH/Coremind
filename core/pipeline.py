"""
core/pipeline.py

The end-to-end flow, same for every skill pack:

  raw data --> skill.extract_features() --> AnomalyEngine.score()
            --> top anomalies --> skill.prompt_template --> LocalLLM.generate()
            --> plain-English explanation

This file should never need to change when you add a new skill pack --
that's the whole point of the architecture.
"""

import re

import pandas as pd

from core.anomaly_engine import AnomalyEngine
from core.llm_client import LocalLLM
from core.skill_loader import SkillPack


_NUMBER_PATTERN = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
_DERIVED_FIELDS = {"anomaly_score", "is_anomaly"}


def add_numeric_guardrail(explanation: str, row_data: dict) -> str:
    """Label numeric claims that cannot be matched to the original row data."""
    source_numbers = {
        _normalize_number(match.group())
        for key, value in row_data.items()
        if key not in _DERIVED_FIELDS
        for match in _NUMBER_PATTERN.finditer(str(value))
    }
    unverified = []
    for match in _NUMBER_PATTERN.finditer(explanation):
        number = _normalize_number(match.group())
        if number not in source_numbers and match.group() not in unverified:
            unverified.append(match.group())

    if not unverified:
        return explanation

    details = ", ".join(unverified)
    return (
        f"{explanation}\n\n"
        f"⚠️ Unverified numeric detail: {details}. Verify this against the source data."
    )


def _normalize_number(value: str) -> str:
    """Treat equivalent forms such as 45 and 45.0 as the same value."""
    normalized = value.replace(",", "")
    try:
        return format(float(normalized), ".12g")
    except ValueError:
        return normalized


def run_pipeline(skill: SkillPack, raw_df: pd.DataFrame, top_n: int = 3, llm: LocalLLM = None):
    """
    Returns a list of dicts, one per top anomaly:
        {"row": <original row as dict>, "explanation": <LLM text>}
    """
    llm = llm or LocalLLM()

    features = skill.extract_features(raw_df)
    engine = AnomalyEngine(contamination=skill.contamination)
    scored = engine.score(features)

    anomalies = scored[scored["is_anomaly"]].head(top_n)
    if anomalies.empty:
        # no anomalies detected -- take the lowest-scoring rows anyway so the
        # demo always has something to show
        anomalies = scored.head(top_n)

    results = []
    for _, row in anomalies.iterrows():
        row_dict = row.to_dict()
        prompt = skill.prompt_template.format(**row_dict)
        explanation = add_numeric_guardrail(llm.generate(prompt), row_dict)
        results.append({"row": row_dict, "explanation": explanation})

    return results
