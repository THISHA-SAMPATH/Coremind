# Architecture

## System Diagram

┌─────────────────────────────────────────────────────────────────┐
│                         Streamlit UI (app.py)                    │
│  Skill selector │ File upload │ Results view │ Chat │ Fix button │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     core/skill_loader.py                         │
│  Discovers skill packs under /skills, loads skill.yaml config    │
│  and the skill's feature_extractor.py at runtime                │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              skills/<name>/feature_extractor.py                  │
│  Domain-specific: raw CSV → numeric feature dataframe            │
│  (Sentinel: logs | FinSight: transactions | StudyMate: scores |  │
│   HealthGuard: vitals)                                            │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 core/anomaly_engine.py                           │
│  Shared, domain-agnostic Isolation Forest model                  │
│  Input: numeric features → Output: anomaly_score, is_anomaly     │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    core/pipeline.py                               │
│  Orchestrates: features → anomaly scoring → top-N anomalies      │
│  → fills each skill's prompt_template with the row's data        │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   core/llm_client.py                              │
│  Sends filled prompt to local Ollama (http://localhost:11434)    │
│  Model: phi3:mini │ temperature: 0.2 │ falls back to a labeled    │
│  stub response if Ollama is unreachable                          │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
                 Plain-English explanation
                 displayed back in the UI
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   core/remediation.py     │   │   Chat follow-up (in app.py)   │
│ Matches anomaly's values   │   │ Uses skill description + last  │
│ against skill's rule table │   │ analysis results as context;   │
│ (skill.yaml) → LLM only    │   │ same LocalLLM instance, same    │
│ phrases the matched fix,   │   │ hallucination-guard prompt      │
│ never invents one          │   │ instructions                    │
└───────────────────────────┘   └───────────────────────────────┘

## Model / Pipeline Summary

| Stage | Component | Runs Where |
|---|---|---|
| Feature extraction | `skills/<name>/feature_extractor.py` | Local (pandas) |
| Anomaly detection | `core/anomaly_engine.py` (Isolation Forest) | Local (scikit-learn) |
| Explanation generation | `core/llm_client.py` → Ollama `phi3:mini` | Local (Ollama, `localhost:11434`) |
| Remediation matching | `core/remediation.py` | Local (pure Python, rule evaluation) |
| Chat follow-up | `app.py` → `core/llm_client.py` | Local (same Ollama instance) |
| UI rendering | `app.py` (Streamlit) | Local (`localhost:8501`) |

## Data Flow

1. User selects a skill pack and either uploads a CSV or uses bundled sample data.
2. The skill's `feature_extractor.py` converts raw columns into a numeric feature dataframe, keeping original columns (timestamps, merchant names, topic names, etc.) for later display.
3. `AnomalyEngine` fits/scores an Isolation Forest on the numeric columns only (non-numeric columns are excluded from the model but preserved in the output for context).
4. The top-N lowest-scoring (most anomalous) rows are selected.
5. Each anomaly's row data is substituted into that skill's `prompt_template` (from `skill.yaml`) and sent to the local LLM for a plain-English explanation.
6. If the user clicks "How do I fix this?", the row is checked against the skill's `remediation_rules`; only a matched, pre-written fix is sent to the LLM for natural phrasing.
7. If the user opens the chat panel, follow-up questions are answered using the skill's description and the current session's flagged anomalies as grounding context — not general knowledge, and not a fresh anomaly-detection pass.

## Local vs. Cloud Components

**Local (100% of the AI pipeline):**
- Anomaly detection (scikit-learn)
- LLM inference for explanations, remediation phrasing, and chat (Ollama, `phi3:mini`)
- All data storage (in-memory / Streamlit session state only)

**Cloud (none required):**
- CoreMind has no cloud dependency for any core feature. The only network activity in the entire project is the one-time download of Ollama and the `phi3:mini` model weights during initial setup.

## Key Design Decisions

- **Shared engine, swappable skill packs**: `core/` contains zero domain-specific logic. Adding a new domain only requires a new `skill.yaml` + `feature_extractor.py` — no changes to detection, LLM handling, or UI wiring.
- **Isolation Forest over deep learning for detection**: needs no training data beyond the input batch, is fast on CPU, and suits tabular, mixed-domain data.
- **Small quantized-friendly LLM (phi3:mini) via Ollama**: practical local-inference footprint (~2.2GB, runs on CPU) instead of a GPU-dependent model.
- **Deterministic remediation rules instead of free-form LLM fixes**: fixes are pre-written and rule-matched; the LLM only rephrases them, directly constraining hallucination risk for the most actionable part of the output.
- **Session-only state, no persistence by default**: avoids a data-retention liability for the sensitive categories (financial, health) this project explicitly targets.
