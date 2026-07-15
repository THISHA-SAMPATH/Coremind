# Local AI Verification

## What Runs Fully On-Device

- **Anomaly detection**: scikit-learn's Isolation Forest runs entirely in-process on the local
  machine. No data or model calls leave the device for this step, for any skill pack (Sentinel,
  FinSight, StudyMate, HealthGuard).
- **LLM inference**: served locally via [Ollama](https://ollama.com) (default model `phi3:mini`,
  ~3.8B parameters, ~2.2GB on disk). All prompts and generations happen on `http://localhost:11434`
  — a loopback address that never leaves the machine.
- **Chat / conversational follow-ups**: routed through the same local Ollama instance. No
  external chat API is used.
- **Remediation rule matching**: a simple local rule-evaluation function (`core/remediation.py`),
  no network involved.
- **UI**: Streamlit serves the interface on `localhost` by default.

## What (If Anything) Requires Internet

- **One-time setup only**: downloading Ollama itself and pulling the `phi3:mini` model requires
  internet access, exactly once. After that, the application runs with no network connection.
- No feature of CoreMind requires an active internet connection during normal use.

## Does Any User Data Leave the Device?

No. Uploaded CSVs (network logs, transactions, study scores, health vitals), the resulting
anomaly scores, and all LLM-generated explanations stay in local memory/session state for the
duration of the app's run. Nothing is transmitted to any external server, API, or third party.
This is a deliberate design choice, not an incidental property — it's the reason the LLM was
run locally via Ollama instead of calling a cloud LLM API.
