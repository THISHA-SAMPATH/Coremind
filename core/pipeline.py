"""
core/pipeline.py

The end-to-end flow, same for every skill pack:

  raw data --> skill.extract_features() --> AnomalyEngine.score()
            --> top anomalies --> skill.prompt_template --> LocalLLM.generate()
            --> plain-English explanation

This file should never need to change when you add a new skill pack --
that's the whole point of the architecture.
"""

import pandas as pd

from core.anomaly_engine import AnomalyEngine
from core.llm_client import LocalLLM
from core.skill_loader import SkillPack


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
        explanation = llm.generate(prompt)
        results.append({"row": row_dict, "explanation": explanation})

    return results
