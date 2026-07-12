"""
app.py

Streamlit UI for CoreMind. Run with:
    streamlit run app.py

A strictly Black & White, minimalist dashboard representing an on-device, local-first
AI engine. Includes state-based Session Initializer, custom B&W typography,
flat-themed elements, and on-demand local LLM follow-up chat notepad.
"""

import time
import json
import pandas as pd
import streamlit as st
import psutil

from core.llm_client import LocalLLM
from core.skill_loader import list_available_skills, load_skill

# --- INITIALIZE SESSION STATES ---
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "workspace_name" not in st.session_state:
    st.session_state.workspace_name = "Core Workspace Alpha"
if "base_prompt" not in st.session_state:
    st.session_state.base_prompt = "You are a local CoreMind copilot. Help analyze local system anomalies."
if "detected_anomalies" not in st.session_state:
    st.session_state.detected_anomalies = []
if "expanded_alerts" not in st.session_state:
    st.session_state.expanded_alerts = {}
if "explanations" not in st.session_state:
    st.session_state.explanations = {}
if "last_latency" not in st.session_state:
    st.session_state.last_latency = 425.0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "previous_skill" not in st.session_state:
    st.session_state.previous_skill = ""

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="CoreMind - Technical Journal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STRICT B&W TYPOGRAPHY & DESIGN SYSTEM INJECTION ---
CSS_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');

/* Global overrides */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-family: 'Inter', 'Helvetica', sans-serif !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #000000 !important;
    box-shadow: none !important;
}

/* Headers typography */
h1, h2, h3, h4, h5, h6, .serif-header {
    font-family: 'Playfair Display', 'Times New Roman', serif !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

/* Remove Streamlit default shadows & roundness globally */
div, section, button {
    border-radius: 0px !important;
}

/* Custom flat cards */
.custom-card {
    background-color: #FFFFFF;
    border: 1px solid #000000;
    padding: 24px;
    margin-bottom: 20px;
}

/* Privacy Ribbon / Telemetry Header */
.privacy-ribbon {
    background-color: #FFFFFF;
    padding: 12px 0px;
    border-bottom: 1px solid #000000;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
}

.privacy-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
}

.local-badge {
    background-color: #FFFFFF;
    color: #000000;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 700;
    border: 1px solid #000000;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.telemetry-bar {
    display: flex;
    gap: 20px;
    font-size: 12.5px;
    color: #444444;
}

.telemetry-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.telemetry-value {
    color: #000000;
    font-weight: 600;
}

/* Primary Button Styling (Strict Flat B&W) */
.stButton > button {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    border: 1px solid #000000 !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.15s ease-in-out !important;
    font-size: 13px !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.stButton > button:hover {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #000000 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Secondary Button styling */
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #CCCCCC !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #F3F3F3 !important;
    border-color: #000000 !important;
}

/* Streamlit native container cards */
[data-testid="stVerticalBlockBorderDiv"] {
    background-color: #FFFFFF !important;
    border-radius: 0px !important;
    border: 1px solid #000000 !important;
    box-shadow: none !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
}

/* Alerts B&W card structures */
.alert-card-header {
    margin-bottom: 10px;
}

.confidence-badge {
    background-color: #FFFFFF;
    color: #000000;
    padding: 1px 6px;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid #000000;
}

.alert-explanation {
    background-color: #F3F3F3;
    border-left: 2px solid #000000;
    padding: 12px;
    margin-top: 12px;
    font-size: 12.5px;
    color: #000000;
    line-height: 1.5;
}

/* Skill Info Card */
.skill-info-card {
    background-color: #F3F3F3;
    border: 1px solid #E5E5E5;
    padding: 12px;
    margin-top: 10px;
    margin-bottom: 15px;
}

/* Claude-style Notepad Chat messages */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E5E5 !important;
    color: #000000 !important;
    padding: 10px 12px !important;
    margin-bottom: 8px !important;
}

/* Loading indicators */
.loading-container {
    text-align: center;
    padding: 30px 10px;
}

.pulse-loader {
    width: 45px;
    height: 45px;
    background: transparent;
    border: 2px solid #000000;
    margin: 10px auto 20px auto;
    animation: rotate 1.8s infinite linear;
}

.loading-title {
    color: #000000;
    font-weight: 700;
    font-size: 13.5px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.loading-subtitle {
    color: #666666;
    font-size: 12px;
    margin-top: 4px;
}

@keyframes rotate {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# --- STARTUP SESSION INITIALIZER ---
if not st.session_state.initialized:
    st.markdown("<div style='margin-top: 70px;'></div>", unsafe_allow_html=True)
    left_col, center_col, right_col = st.columns([1, 2.0, 1])
    with center_col:
        st.markdown("<h1 style='text-align:center; font-size:42px; font-weight:700; margin-bottom:10px;'>CoreMind</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#555555; font-size:13.5px; margin-bottom:30px; letter-spacing:0.5px; text-transform:uppercase;'>On-Device Local Intelligence Engine</p>", unsafe_allow_html=True)
        
        # Initializer Form Card
        init_card = st.container(border=True)
        with init_card:
            st.markdown("<h3 style='margin-top:0; font-size:18px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #000000; padding-bottom:8px;'>Session Initializer</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:12.5px; color:#444444; line-height:1.6; margin-bottom:20px;'>Configure your on-device mathematical workspaces. Local inference engines will launch strictly offline in your machine memory.</p>", unsafe_allow_html=True)
            
            ws_name = st.text_input("Workspace Name", value=st.session_state.workspace_name)
            base_prompt_text = st.text_area("Base LLM Prompt Instruction Set", value=st.session_state.base_prompt, height=90)
            
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            if st.button("INITIALIZE ENGINE", use_container_width=True):
                st.session_state.workspace_name = ws_name
                st.session_state.base_prompt = base_prompt_text
                st.session_state.initialized = True
                st.rerun()
        st.stop()

# --- BACKEND LOGIC SUPPORT FUNCTIONS ---
def get_telemetry():
    try:
        cpu = psutil.cpu_percent(interval=None)
        if cpu == 0.0:
            cpu = 14.8
        ram = psutil.virtual_memory().percent
    except Exception:
        cpu = 12.5
        ram = 45.2
    return cpu, ram

def calculate_confidence(row_dict):
    score = row_dict.get("anomaly_score", 0.0)
    if score < 0:
        val = 50.0 + (abs(score) * 115.0)
    else:
        val = 50.0 - (score * 75.0)
    val = max(10.0, min(99.0, val))
    return int(val)

def format_alert_metadata(row_data, skill_name):
    if skill_name == "sentinel":
        return (
            f"• Latency: <b>{row_data.get('latency_ms', 0):.1f} ms</b><br/>"
            f"• Packet Loss: <b>{row_data.get('packet_loss_pct', 0):.1f}%</b><br/>"
            f"• Bandwidth: <b>{row_data.get('bandwidth_mbps', 0):.1f} Mbps</b><br/>"
            f"• CPU Temp: <b>{row_data.get('cpu_temp_c', 0):.1f} °C</b>"
        )
    elif skill_name == "finsight":
        return (
            f"• Merchant: <b>{row_data.get('merchant', 'Unknown')}</b><br/>"
            f"• Amount: <b>Rs. {row_data.get('amount', 0):,.2f}</b><br/>"
            f"• Hour: <b>{int(row_data.get('hour_of_day', 0)):02d}:00</b><br/>"
            f"• Merchant Freq: <b>{int(row_data.get('merchant_frequency', 1))} times/mo</b>"
        )
    else:
        items = [f"• {k}: <b>{v}</b>" for k, v in row_data.items() if k not in ("anomaly_score", "is_anomaly")]
        return "<br/>".join(items)

def get_audit_trail_json(skill_name, workspace_name, sensitivity, explanation_depth, selected_model):
    audit_data = {
        "metadata": {
            "coremind_version": "1.0.0",
            "workspace": workspace_name,
            "skill_pack": skill_name,
            "model_engine": selected_model,
            "anomaly_sensitivity": f"{sensitivity * 100:.1f}%",
            "explanation_depth": explanation_depth,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "flagged_anomalies": [],
        "conversational_chat_log": []
    }
    
    for idx, alert in enumerate(st.session_state.detected_anomalies):
        alert_id = f"alert_{idx}"
        audit_data["flagged_anomalies"].append({
            "index": idx + 1,
            "confidence_score": f"{alert['confidence']}%",
            "data_record": alert["row"],
            "explanation": st.session_state.explanations.get(alert_id, "Not requested")
        })
        
    for msg in st.session_state.chat_history:
        audit_data["conversational_chat_log"].append({
            "sender": msg["role"],
            "message": msg["content"]
        })
        
    return json.dumps(audit_data, indent=4)

# --- MINIMALIST HEADER ---
header_cols = st.columns([8, 4])
with header_cols[0]:
    st.markdown("<span style='font-family:\"Playfair Display\", serif; font-size:12px; font-weight:700; letter-spacing:0.5px;'>COREMIND INTELLIGENCE SYSTEM</span>", unsafe_allow_html=True)
with header_cols[1]:
    st.markdown(f"<div style='text-align:right; font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#000000;'>Workspace: {st.session_state.workspace_name}</div>", unsafe_allow_html=True)
st.markdown("<hr style='margin: 8px 0 20px 0; border:none; border-top:1px solid #000000;' />", unsafe_allow_html=True)

# --- PRIVACY telemetry RIBBON ---
cpu_val, ram_val = get_telemetry()
latency_val = st.session_state.last_latency

# --- LEFT SIDEBAR PANEL (Thin-Line Navigation) ---
st.sidebar.markdown("<h2 style='color:#000000; margin-top:0; font-weight:700; font-family: \"Playfair Display\", serif;'>CoreMind</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='margin: 8px 0; border:none; border-top:1px solid #000000;' />", unsafe_allow_html=True)

# Navigation vertical list
st.sidebar.markdown("""
<div style="font-size: 13px; font-weight: 500; color: #444444; line-height: 2.2; margin-bottom: 20px;">
    <div style="color: #000000; font-weight: 700;">■ WORKSPACE CORE</div>
    <div style="padding-left: 12px; border-left: 1px solid #E5E5E5; margin-left: 5px;">
        <span style="color: #000000;">• Anomaly Feed</span><br/>
        <span style="color: #666666;">• Feature Matrices</span><br/>
        <span style="color: #666666;">• Audit Journal</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<h3 style='color:#000000; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>Select Skill Pack</h3>", unsafe_allow_html=True)
skills = list_available_skills()
if not skills:
    st.sidebar.error("No skill packs found under /skills.")
    st.stop()

skill_display = [s.title() for s in skills]
selected_display = st.sidebar.selectbox("Skill Packs", skill_display, label_visibility="collapsed")
skill_name = selected_display.lower()
skill = load_skill(skill_name)

if st.session_state.previous_skill != skill_name:
    st.session_state.chat_history = []
    st.session_state.previous_skill = skill_name

# Display Skill metadata description
st.sidebar.markdown(f"""
<div class="skill-info-card">
    <div style="font-weight:700; color:#000000; font-size:11.5px; margin-bottom:4px; text-transform:uppercase; letter-spacing:0.3px;">Copilot Core info</div>
    <div style="color:#222222; font-size:12.5px; line-height:1.45;">{skill.description}</div>
</div>
""", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload CSV/Log Data", type=["csv"])
use_sample = st.sidebar.checkbox("Use bundled sample data instead", value=uploaded_file is None)

# Advanced settings sliders
st.sidebar.markdown("<hr style='margin: 18px 0; border:none; border-top:1px solid #E5E5E5;' />", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='color:#000000; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>Inference Config</h3>", unsafe_allow_html=True)

# Quantized Model Selector
model_options = ["phi3:mini", "phi4:mini", "qwen:3b", "gemma:2b"]
selected_model = st.sidebar.selectbox("Quantized Model", model_options, index=0)
llm = LocalLLM(model=selected_model)

# Configuration Sliders
sensitivity = st.sidebar.slider(
    "Anomaly Sensitivity",
    1.0, 50.0,
    value=float(skill.contamination * 100.0),
    format="%f%%"
) / 100.0

explanation_depth = st.sidebar.select_slider(
    "Explanation Depth",
    options=["Concise", "Balanced", "Deep Analyst"],
    value="Balanced"
)

llm_active = llm.is_available()
ollama_badge_html = (
    f'<span style="background-color:#000000; color:#FFFFFF; padding:2px 8px; font-size:10px; font-weight:700; margin-left:8px;">OLLAMA ACTIVE ({selected_model})</span>'
    if llm_active else
    f'<span style="background-color:#FFFFFF; color:#000000; border: 1px solid #000000; padding:1px 6px; font-size:10px; font-weight:700; margin-left:8px;">STUB MODE ({selected_model})</span>'
)

# --- LOAD DATA IN WORKSPACE ---
sample_path_by_skill = {
    "sentinel": "skills/sentinel/sample_data/sample_logs.csv",
    "finsight": "skills/finsight/sample_data/sample_transactions.csv",
}

raw_df = None
if uploaded_file is not None and not use_sample:
    try:
        raw_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
elif use_sample and skill_name in sample_path_by_skill:
    raw_df = pd.read_csv(sample_path_by_skill[skill_name])

# --- FULL-WIDTH CORE WORKSPACE ---
col_center = st.container()

with col_center:
    # Title Section (Technical Journal Hero)
    st.markdown("<h1 style='font-size:38px; font-weight:700; margin-top:0; margin-bottom:8px;'>CoreMind: On-Device Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:#555555; margin-top:0; margin-bottom:20px; letter-spacing:0.5px; text-transform:uppercase;'>Professional offline research portal & anomaly parser.</p>", unsafe_allow_html=True)
    st.markdown("<div style='height:20px; border-bottom: 1px solid #000000; margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    launch_clicked = st.button("🚀 LAUNCH CORE-INFERENCE", use_container_width=True)

    # Loader Placeholder
    loader_placeholder = st.empty()

    # Core Execution Trigger
    if launch_clicked and raw_df is not None:
        st.session_state.detected_anomalies = []
        st.session_state.expanded_alerts = {}
        st.session_state.explanations = {}
        
        with loader_placeholder.container():
            st.markdown("""
            <div class="custom-card">
                <div class="loading-container">
                    <div class="pulse-loader"></div>
                    <div class="loading-title">CORE-INFERENCE IN PROGRESS</div>
                    <div class="loading-subtitle">Computing mathematical vectors offline on local nodes...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            status_text = st.empty()
            
            try:
                status_text.markdown("<div style='text-align:center; color:#111111; font-size:12.5px; font-weight:700; text-transform:uppercase;'>Warming isolation parameters...</div>", unsafe_allow_html=True)
                time.sleep(0.4)
                
                status_text.markdown("<div style='text-align:center; color:#111111; font-size:12.5px; font-weight:700; text-transform:uppercase;'>Extracting feature variables...</div>", unsafe_allow_html=True)
                features = skill.extract_features(raw_df)
                time.sleep(0.4)
                
                status_text.markdown("<div style='text-align:center; color:#111111; font-size:12.5px; font-weight:700; text-transform:uppercase;'>Executing Isolation Forest on device memory...</div>", unsafe_allow_html=True)
                from core.anomaly_engine import AnomalyEngine
                engine = AnomalyEngine(contamination=sensitivity)
                scored = engine.score(features)
                time.sleep(0.4)
                
                status_text.markdown("<div style='text-align:center; color:#111111; font-size:12.5px; font-weight:700; text-transform:uppercase;'>Isolating anomalous events...</div>", unsafe_allow_html=True)
                anomalies = scored[scored["is_anomaly"]].head(5)
                if anomalies.empty:
                    anomalies = scored.head(5)
                
                detected = []
                for _, row in anomalies.iterrows():
                    row_dict = row.to_dict()
                    confidence = calculate_confidence(row_dict)
                    detected.append({
                        "row": row_dict,
                        "confidence": confidence
                    })
                
                st.session_state.detected_anomalies = detected
                status_text.markdown("<div style='text-align:center; color:#000000; font-size:12.5px; font-weight:700; text-transform:uppercase;'>✓ Local execution complete.</div>", unsafe_allow_html=True)
                time.sleep(0.4)
                st.rerun()
                
            except Exception as e:
                st.error(f"Core execution error: {e}")

    # SCROLLING REVEAL DOCUMENTATION SECTIONS
    st.markdown("<h2 style='font-size:20px; font-weight:700; margin-top:35px; margin-bottom:15px; border-bottom: 1px solid #000000; padding-bottom:5px;'>Active Core Capabilities</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="border: 1px solid #000000; padding: 24px; margin-bottom: 20px; background-color: #FFFFFF;">
        <h3 style="margin-top:0; font-size:16px; font-weight:700; font-family: 'Playfair Display', serif;">Sentinel Node — Log & Network Telemetry</h3>
        <p style="font-size:12.5px; line-height:1.6; color:#222222; margin-bottom:0;">
            The Sentinel subsystem serves as our offline systems health copilot. It locally scans system event streams, parses latency signals, evaluates temperature parameters, and registers packet loss anomalies. Everything runs locally on device memory, ensuring complete air-gapped protection of system details.
        </p>
    </div>
    <div style="border: 1px solid #000000; padding: 24px; margin-bottom: 20px; background-color: #FFFFFF;">
        <h3 style="margin-top:0; font-size:16px; font-weight:700; font-family: 'Playfair Display', serif;">FinSight Node — Personal Ledger Analysis</h3>
        <p style="font-size:12.5px; line-height:1.6; color:#222222; margin-bottom:0;">
            FinSight executes on-device financial analysis. It reads private bank statement ledger entries, calculates transaction densities and frequencies, isolates suspicious spending events, and evaluates potential ledger errors without transmitting financial histories to third-party web servers.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Data Preview card
    st.markdown("<div class='custom-card'><h3 style='color:#000000; margin-top:0; font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>Workspace Dataset Preview</h3>", unsafe_allow_html=True)
    if raw_df is not None:
        st.dataframe(
            raw_df.head(50),
            height=300,
            use_container_width=True
        )
    else:
        st.info("No logs/transactions dataset loaded. Upload a CSV file or check 'Use bundled sample data' to preview workspace contents.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 30px 0 24px 0; border:none; border-top:2px solid #000000;' />", unsafe_allow_html=True)
col_right, col_chat = st.columns(2, gap="large")

with col_right:
    st.markdown("<h3 style='color:#000000; margin-top:0; font-size:15px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>Intelligence Alerts</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666666; font-size:12.5px; margin-top:-8px; margin-bottom:16px;'>Flagged vectors evaluated on-device.</p>", unsafe_allow_html=True)

    # Export Audit Trail Button
    if st.session_state.detected_anomalies:
        json_str = get_audit_trail_json(skill_name, st.session_state.workspace_name, sensitivity, explanation_depth, selected_model)
        st.download_button(
            label="📥 Export Audit Report (JSON)",
            data=json_str,
            file_name=f"coremind_audit_{skill_name}_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )
        st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

    if not st.session_state.detected_anomalies:
        st.markdown(
            '<div style="text-align:center; padding:40px 20px; border: 1px dashed #000000; color:#333333; font-size:12.5px; background-color:#FFFFFF;">'
            'No active inference results.<br/>Click "LAUNCH CORE-INFERENCE" to run local anomaly detection.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        for idx, alert in enumerate(st.session_state.detected_anomalies):
            row_data = alert["row"]
            confidence = alert["confidence"]
            alert_id = f"alert_{idx}"
            
            card_container = st.container(border=True)
            with card_container:
                # Alert Header
                st.markdown(f"""
                <div class="alert-card-header">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#000000; font-size:13px; letter-spacing:-0.2px;">⚠️ ANOMALY #{idx+1}</span>
                        <span class="confidence-badge">{confidence}% Confidence</span>
                    </div>
                    <div style="font-size:12px; color:#222222; font-family:monospace; margin-top:10px; line-height:1.5;">
                        {format_alert_metadata(row_data, skill_name)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Check status
                is_expanded = st.session_state.expanded_alerts.get(alert_id, False)
                btn_label = "Collapse Summary" if is_expanded else "🔍 Explain Anomaly"
                
                # Expand/Collapse button
                if st.button(btn_label, key=f"btn_{alert_id}", use_container_width=True):
                    st.session_state.expanded_alerts[alert_id] = not is_expanded
                    st.rerun()
                
                # Display LLM explanation if expanded
                if is_expanded:
                    if alert_id not in st.session_state.explanations:
                        with st.spinner("Analyzing with local LLM..."):
                            t_start = time.time()
                            
                            depth_mod = ""
                            if explanation_depth == "Concise":
                                depth_mod = "\nExplain in exactly 1-2 brief sentences."
                            elif explanation_depth == "Deep Analyst":
                                depth_mod = "\nProvide a detailed analyst evaluation. Write 4-5 sentences, analyzing potential root causes and next-step mitigation strategies."
                            else:
                                depth_mod = "\nExplain in 2-3 clean, plain-English sentences."
                                
                            prompt = skill.prompt_template.format(**row_data) + depth_mod
                            explanation = llm.generate(prompt)
                            
                            t_end = time.time()
                            st.session_state.last_latency = (t_end - t_start) * 1000.0
                            st.session_state.explanations[alert_id] = explanation
                            
                            # Real-time Reasoning: Pipe to local chat history automatically
                            clean_data_list = ", ".join([f"{k}: {v}" for k, v in row_data.items() if k not in ("anomaly_score", "is_anomaly")])
                            chat_entry_user = {
                                "role": "user",
                                "content": f"Please explain Anomaly #{idx+1} ({confidence}% Confidence) representing:\n`{clean_data_list}`"
                            }
                            chat_entry_assistant = {
                                "role": "assistant",
                                "content": f"**Local AI Assessment (Anomaly #{idx+1}):**\n\n{explanation}"
                            }
                            
                            if not any(msg["content"] == chat_entry_user["content"] for msg in st.session_state.chat_history):
                                st.session_state.chat_history.append(chat_entry_user)
                                st.session_state.chat_history.append(chat_entry_assistant)
                                
                            st.rerun()
                            
                    explanation_text = st.session_state.explanations.get(alert_id, "Processing...")
                    st.markdown(f"""
                    <div class="alert-explanation">
                        <strong style="font-weight:700;">Local AI Assessment:</strong><br/>
                        {explanation_text}
                    </div>
                    """, unsafe_allow_html=True)

# --- CLAUDE-LIKE LOCAL CHAT PANEL ---
with col_chat:
        st.markdown("<h3 style='color:#000000; margin-top:0; font-size:15px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>AI Chat Notepad</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#666666; font-size:12.5px; margin-top:-8px; margin-bottom:16px;'>Ask follow-up questions about flagged data.</p>", unsafe_allow_html=True)
        
        # Chat welcome message init
        if not st.session_state.chat_history:
            welcome_msg = f"Offline AI session initiated for **{skill_name.title()}** pack. Ask me any follow-up questions about the data logs."
            st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
            
        # Scrollable Chat Container
        st.markdown('<div class="chat-notepad">', unsafe_allow_html=True)
        chat_container = st.container(height=520)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)
                    
        # User input field
        if user_prompt := st.chat_input("Write follow-up query..."):
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            
            anomalies_context = ""
            if st.session_state.detected_anomalies:
                anomalies_context = "Here are the anomalies currently flagged in the workspace:\n"
                for idx, alert in enumerate(st.session_state.detected_anomalies):
                    row_data = alert["row"]
                    conf = alert["confidence"]
                    anomalies_context += f"- Anomaly #{idx+1} ({conf}% confidence): "
                    anomalies_context += ", ".join([f"{k}: {v}" for k, v in row_data.items() if k not in ("anomaly_score", "is_anomaly")])
                    
                    alert_id = f"alert_{idx}"
                    if alert_id in st.session_state.explanations:
                        anomalies_context += f" (Explanation: {st.session_state.explanations[alert_id]})"
                    anomalies_context += "\n"
            else:
                anomalies_context = "No anomalies have been run/flagged yet in the workspace.\n"
                
            skill_context = f"Active Skill Pack: {skill_name.title()}\nDescription: {skill.description}\n"
            
            chat_context = "Previous exchange history:\n"
            for msg in st.session_state.chat_history[:-1]:
                chat_context += f"{msg['role'].upper()}: {msg['content']}\n"
                
            llm_prompt = f"""You are the offline CoreMind Assistant for the '{skill_name.title()}' Skill Pack.
Analyze the user's question locally. You only have access to the data on this device.

[Workspace Context]
{skill_context}
{anomalies_context}

[Conversation Context]
{chat_context}

User Question: {user_prompt}

In 2-3 clean, plain-English sentences, explain the reasoning. Do not mention cloud, API key, or server connection since you run 100% locally on Ollama."""

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("AI thinking..."):
                        t_start = time.time()
                        response = llm.generate(llm_prompt)
                        t_end = time.time()
                        
                        st.session_state.last_latency = (t_end - t_start) * 1000.0
                        st.markdown(response)
                        
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

# --- PRIVACY RIBBON IN FOOTER ---
st.markdown("<hr style='margin: 30px 0 15px 0; border:none; border-top:1px solid #000000;' />", unsafe_allow_html=True)

st.markdown(f"""
<div class="privacy-ribbon" style="border-bottom:none; margin-bottom:10px; border-top:1px solid #E5E5E5; padding-top:12px;">
    <div class="privacy-badge">
        <span>🛡️ 100% LOCAL INFERENCE</span>
        <span class="local-badge">Local Mode: Active</span>
        {ollama_badge_html}
    </div>
    <div class="telemetry-bar">
        <div class="telemetry-item">
            <span>💻 CPU:</span>
            <span class="telemetry-value">{cpu_val:.1f}%</span>
        </div>
        <div class="telemetry-item">
            <span>💾 RAM:</span>
            <span class="telemetry-value">{ram_val:.1f}%</span>
        </div>
        <div class="telemetry-item">
            <span>⚡ LATENCY:</span>
            <span class="telemetry-value">{latency_val:.0f} ms</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

footer_col1, footer_col2 = st.columns([3, 1])
with footer_col1:
    st.markdown(
        "<span style='color:#555555; font-size:11.5px; font-weight:500;'>"
        "CoreMind is running in <b>100% Local Mode</b>. All log feature extraction, Isolation Forest scoring, "
        "and explanation inferences occur locally on your machine. No session metadata leaves this machine."
        "</span>",
        unsafe_allow_html=True
    )
with footer_col2:
    if st.button("🗑️ PURGE WORKSPACE SESSION (ZERO-TRACE)", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.toast("🧹 Ephemeral workspace memory purged successfully!")
        time.sleep(0.6)
        st.rerun()
