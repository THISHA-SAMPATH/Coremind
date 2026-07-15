# Attribution

## Pretrained Models

- **phi3:mini** (Microsoft Phi-3-mini) — served locally via Ollama. Used for all natural-language
  explanations, chat follow-ups, and remediation phrasing.
  License: MIT. https://ollama.com/library/phi3

## Libraries and Frameworks

- **scikit-learn** — Isolation Forest anomaly detection. BSD-3-Clause License.
- **Streamlit** — web UI framework. Apache 2.0 License.
- **Ollama** — local LLM serving runtime. MIT License.
- **pandas** — data handling. BSD-3-Clause License.
- **PyYAML** — skill pack configuration parsing. MIT License.
- **requests** — HTTP client used to talk to the local Ollama API. Apache 2.0 License.

## Datasets

No external datasets were used. All sample data (network logs, transactions, study scores,
health vitals) under `skills/*/sample_data/` was synthetically created by the project author
for demonstration and testing purposes.

## Original Work

The following were designed and built by the project author during the hackathon period:
core anomaly-detection pipeline architecture, the pluggable skill-pack system, all four skill
packs (Sentinel, FinSight, StudyMate, HealthGuard), the remediation rules layer, the
conversational chat context system, and the Streamlit UI.
