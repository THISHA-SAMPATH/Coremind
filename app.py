"""
app.py

Streamlit UI for CoreMind. Run with:
    streamlit run app.py

Lets the user pick a skill pack (Sentinel, FinSight, ...), upload a CSV
(or use the bundled sample data), and see flagged anomalies with plain-
English explanations from the local LLM. Everything below still routes
through the exact same core/ pipeline as the CLI -- this file is purely
presentation.
"""

import pandas as pd
import streamlit as st

from core.llm_client import LocalLLM
from core.pipeline import run_pipeline
from core.skill_loader import list_available_skills, load_skill

st.set_page_config(page_title="CoreMind", page_icon="🧠", layout="centered")

st.title("🧠 CoreMind")
st.caption("A local-first anomaly intelligence engine — no cloud, no API calls.")

# --- Sidebar: skill pack selection ---
skills = list_available_skills()
if not skills:
    st.error("No skill packs found under /skills. Check your project structure.")
    st.stop()

skill_name = st.sidebar.selectbox("Choose a skill pack", skills)
skill = load_skill(skill_name)
st.sidebar.info(skill.description)

top_n = st.sidebar.slider("Number of anomalies to explain", 1, 10, 3)
model_name = st.sidebar.text_input("Ollama model", value="phi3:mini")

# --- LLM availability check ---
llm = LocalLLM(model=model_name)
if llm.is_available():
    st.sidebar.success("Ollama detected — using real local LLM")
else:
    st.sidebar.warning("Ollama not detected — showing stub responses. Run `ollama serve`.")

# --- Data input ---
st.subheader(f"Input data for: {skill_name}")
sample_path_by_skill = {
    "sentinel": "skills/sentinel/sample_data/sample_logs.csv",
    "finsight": "skills/finsight/sample_data/sample_transactions.csv",
}

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
use_sample = st.checkbox("Use bundled sample data instead", value=uploaded_file is None)

raw_df = None
if uploaded_file is not None and not use_sample:
    raw_df = pd.read_csv(uploaded_file)
elif use_sample and skill_name in sample_path_by_skill:
    raw_df = pd.read_csv(sample_path_by_skill[skill_name])

if raw_df is not None:
    st.write("Preview of input data:")
    st.dataframe(raw_df.head(10), use_container_width=True)

    if st.button("Run analysis", type="primary"):
        with st.spinner("Detecting anomalies and generating explanations..."):
            try:
                results = run_pipeline(skill, raw_df, top_n=top_n, llm=llm)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                results = []

        if results:
            st.subheader(f"Top {len(results)} anomalies")
            for i, r in enumerate(results, 1):
                score = r["row"].get("anomaly_score")
                with st.expander(f"Anomaly #{i} — score: {score:.3f}", expanded=(i == 1)):
                    st.markdown("**Raw data:**")
                    display_row = {k: v for k, v in r["row"].items()
                                   if k not in ("anomaly_score", "is_anomaly")}
                    st.json(display_row)
                    st.markdown("**Explanation:**")
                    st.write(r["explanation"])
else:
    st.info("Upload a CSV or check 'Use bundled sample data' to get started.")

st.divider()
st.caption(
    "CoreMind runs entirely on your device: anomaly detection via scikit-learn, "
    "explanations via a local Ollama model. No data leaves this machine."
)
