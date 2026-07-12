# CoreMind

**A local-first anomaly intelligence engine — no cloud, no API calls, no data leaving your device.**

CoreMind detects unusual patterns in any stream of personal or organizational data — network logs, financial transactions, study performance, health vitals — and explains what it found in plain language, using an LLM that runs entirely on your machine. The same statistical core powers every domain; only a lightweight "skill pack" changes.

---

## Table of Contents

- [Problem](#problem)
- [Solution](#solution)
- [Architecture](#architecture)
- [Skill Packs](#skill-packs)
- [On-Device AI Usage](#on-device-ai-usage)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Usage](#usage)
- [Conversational Follow-Ups](#conversational-follow-ups)
- [Remediation Rules (Anti-Hallucination Layer)](#remediation-rules-anti-hallucination-layer)
- [Adding a New Skill Pack](#adding-a-new-skill-pack)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Future Scope](#future-scope)
- [License](#license)

---

## Problem

Very different domains share the same underlying shape: a stream of data is generated over time, most of it is routine, and the rare abnormal entries are the ones that actually matter — but they're buried in noise that a non-technical person can't easily read. Network logs, bank statements, quiz scores, and health vitals all look unrelated on the surface, but "find what's unusual and explain it simply" is the same problem underneath.

Sending any of this data to a cloud AI service isn't acceptable for most of these categories — financial records and health vitals are exactly the kind of data people don't want leaving their device.

## Solution

CoreMind is one local engine — a shared anomaly-detection model (Isolation Forest) plus a local LLM that explains flagged anomalies in plain English — specialized to a domain through small, swappable **skill packs**. Each skill pack is just a config file and a short feature-extraction script; the detection engine, LLM pipeline, and UI never change.

Four skill packs currently prove this out:

| Skill Pack | Domain | What it flags |
|---|---|---|
| **Sentinel** | Network / system health | Latency spikes, packet loss, bandwidth drops, overheating |
| **FinSight** | Personal finance | Unusual spending, duplicate charges, possible fraud |
| **StudyMate** | Study performance | Topics where scores are anomalously weak relative to your own average |
| **HealthGuard** | Personal health vitals | Unusual heart rate, sleep, or activity patterns |

## Architecture

raw data (CSV)
│
▼
skill's feature_extractor.py  ──►  numeric feature vector
│
▼
core/anomaly_engine.py (Isolation Forest, shared across all skills)
│
▼
top anomalies ranked by anomaly_score
│
▼
skill's prompt_template + remediation_rules
│
▼
core/llm_client.py  ──►  local Ollama model  ──►  plain-English explanation
│
▼
Streamlit UI: results, chat follow-ups, "How do I fix this?"

The core engine (`core/`) has zero domain knowledge. Every skill-specific decision — which columns matter, what counts as a fix, how to phrase the prompt — lives entirely inside that skill's folder. This is what makes adding a new domain cheap: no changes to detection logic, LLM handling, or UI wiring.

## Skill Packs

### Sentinel — Network & System Health

Ingests logs with latency, packet loss, bandwidth, and device temperature. Flags entries statistically inconsistent with normal operation and explains the likely cause (congestion, overheating, hardware issues) with a suggested next step.

### FinSight — Personal Finance Analyzer

Ingests bank statement transactions (merchant, amount, time of day, frequency). Flags unusually large charges, odd-hour transactions, and repeated high-value charges from the same merchant — classic fraud signals — entirely offline, since financial data never touches a server.

### StudyMate — Study Performance Analyzer

Ingests quiz/practice results per topic (score, average time per question, attempts). Flags topics scoring below the student's own average — genuine weak spots, not just any statistical outlier — and suggests concrete next steps for revision.

### HealthGuard — Personal Vitals Monitor

Ingests daily health metrics (resting heart rate, sleep hours, steps, active heart rate). Flags readings that deviate from a person's normal pattern and suggests sensible next steps. Does not provide medical diagnoses — only flags patterns worth noticing.

## On-Device AI Usage

- **LLM**: served locally via [Ollama](https://ollama.com), default model `phi3:mini` (swappable for any Ollama-compatible model via the UI's model selector). All inference happens on `localhost:11434` — no network calls at generation time.
- **Anomaly detection**: scikit-learn's Isolation Forest, runs fully in-process.
- **Chat / follow-up Q&A**: same local LLM, grounded in the actual flagged anomaly data as context — not a general-purpose chatbot.
- Internet access is never required to run any part of the core pipeline.

## Tech Stack

- Python 3.10+
- scikit-learn — anomaly detection
- Ollama — local LLM serving
- Streamlit — web UI
- pandas, PyYAML, requests

## Quick Start

**Windows (PowerShell):**

```powershell
.\setup.ps1
```

**Mac/Linux:**

```bash
chmod +x setup.sh && ./setup.sh
```

This installs Python dependencies, checks for Ollama, pulls `phi3:mini` if needed, and launches the Streamlit UI. Requires Ollama already installed from [ollama.com/download](https://ollama.com/download).

## Manual Setup

```bash
git clone <this-repo>
cd coremind
pip install -r requirements.txt

# Install Ollama: https://ollama.com/download
ollama pull phi3:mini
ollama serve   # usually starts automatically after install
```

## Usage

**Web UI:**

```bash
python -m streamlit run app.py
```

Opens a browser interface where you pick a skill pack, upload a CSV (or use bundled sample data), run analysis, chat about the results, and ask for fixes.

**CLI:**

```bash
python cli.py --skill sentinel --input skills/sentinel/sample_data/sample_logs.csv
python cli.py --skill finsight --input skills/finsight/sample_data/sample_transactions.csv
python cli.py --skill studymate --input skills/studymate/sample_data/sample_scores.csv
python cli.py --skill healthguard --input skills/healthguard/sample_data/sample_vitals.csv
python cli.py --list   # see all available skill packs
```

If Ollama isn't running, CoreMind falls back to a clearly labeled stub response so the rest of the pipeline is still testable.

## Conversational Follow-Ups

After running an analysis, a chat panel lets you ask follow-up questions about the results (e.g. *"why is 400ms latency actually a problem?"*). The LLM is given the specific flagged anomaly data as context — it isn't answering from general knowledge, and it's explicitly instructed not to invent facts beyond what's in that context.

## Remediation Rules (Anti-Hallucination Layer)

Rather than letting the LLM freely invent a "fix" for a flagged anomaly, each skill pack defines a small table of human-written remediation rules (condition → fix) in its `skill.yaml`. When a "How do I fix this?" request is made:

1. The anomaly's actual values are checked against that skill's rule conditions.
2. Only a *matched, pre-written* fix is passed to the LLM.
3. The LLM's only job is to phrase that fix naturally using the specific numbers — it cannot suggest a remediation that isn't already in the rule table.

This keeps the actionable advice deterministic and human-verified, while still using the LLM for natural language phrasing.

## Adding a New Skill Pack

1. Create `skills/<name>/skill.yaml` — description, prompt template, contamination rate, remediation rules.
2. Create `skills/<name>/feature_extractor.py` with a single function: `extract_features(raw_df) -> pd.DataFrame`.
3. Add sample data under `skills/<name>/sample_data/`.

No changes to `core/anomaly_engine.py`, `core/pipeline.py`, `core/skill_loader.py`, or the UI's skill-selection logic are required — they all discover skill packs dynamically.

## Project Structure

coremind/
├── core/
│   ├── anomaly_engine.py     # shared Isolation Forest engine
│   ├── llm_client.py         # local Ollama wrapper
│   ├── pipeline.py           # ties detection + LLM together
│   ├── skill_loader.py       # dynamic skill pack loader
│   └── remediation.py        # rule-matching for "How do I fix this?"
├── skills/
│   ├── sentinel/
│   ├── finsight/
│   ├── studymate/
│   └── healthguard/
├── app.py                    # Streamlit UI
├── cli.py                    # command-line interface
├── setup.ps1 / setup.sh      # one-command setup
├── requirements.txt
└── README.md

## Known Limitations

- Explanations are generated by a small local model (`phi3:mini`, ~3.8B parameters) and may occasionally phrase things imprecisely; a larger local model would improve fidelity at the cost of speed and disk space.
- Remediation advice is limited to rules explicitly written per skill pack — an anomaly with no matching rule falls back to general guidance rather than a specific fix.
- Currently CLI + Streamlit only; no packaged desktop installer yet.
- Contamination rate (sensitivity) is currently static per skill; it isn't yet auto-tuned based on dataset size.

## Future Scope

- Auto-tuned contamination rates based on dataset size and variance.
- Additional skill packs (e.g. calendar/time-usage analysis, code-quality anomaly detection).
- Packaged desktop app (Tauri) for a native, no-terminal experience.
- Optional local vector-store memory so chat can reference past analysis sessions.

## License

MIT — see [LICENSE](LICENSE)
