# Privacy and Safety

## Data Handling

CoreMind processes all data (CSV uploads: network logs, financial transactions, study scores,
health vitals) entirely in local memory and Streamlit session state. No uploaded file, derived
feature, anomaly score, or LLM-generated explanation is written to a remote server, external
database, or third-party API.

## Storage

No persistent storage is used by default. Session data (chat history, last analysis results)
exists only for the duration of the running Streamlit session and is cleared when the app is
closed or the "Clear chat" / cache-purge action is used.

## Permissions

The application requires no special OS-level permissions beyond running a local Python process
and a local Ollama server on `localhost:11434`. File uploads use Streamlit's standard file
picker; no filesystem access outside the uploaded file and the bundled sample data is performed.

## Limitations

- This is a hackathon prototype, not a production security/compliance tool. It has not undergone
  formal security auditing.
- The LLM (`phi3:mini`) is a small local model and may occasionally produce imprecise or
  incomplete explanations (see `README.md`'s Known Limitations section). Remediation advice is
  constrained by human-written rules specifically to reduce this risk for actionable guidance.
- HealthGuard and FinSight intentionally avoid framing outputs as medical or financial advice —
  prompts explicitly instruct the model not to give a diagnosis or definitive financial judgment,
  only to flag patterns worth a human's attention.

## Potential Risks

- If a user runs this on a shared/public machine, uploaded CSVs and session data would be visible
  to anyone with access to that session while it's active — standard care around physical device
  access applies, as with any local application.
- Since this project processes sensitive categories (health, finance) by design, it should not be
  treated as a substitute for professional medical or financial consultation — it is intended to
  surface anomalies worth a human's attention, not to make final decisions.
