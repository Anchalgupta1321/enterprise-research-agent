import streamlit as st
import requests
import time
import os
import json

# Allows the app to connect to the Render backend when deployed
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

st.set_page_config(
    page_title="Modus Enterprise Research Agent", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

DARK_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp {
        background: linear-gradient(180deg, #050505 0%, #0b0f19 100%);
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }
    .hero {
        padding: 5rem 2rem;
        text-align: center;
        background: transparent;
        margin-bottom: 2rem;
        position: relative;
    }
    .hero-title {
        font-size: 5rem;
        font-weight: 800;
        background: linear-gradient(to right, #e2e8f0 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        letter-spacing: -2px;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        color: #8b5cf6;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .search-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        border-radius: 16px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
    }
    .stTextInput > div > div > input {
        border-radius: 14px;
        border: none;
        background: #0f172a;
        color: white;
        padding: 20px 24px;
        font-size: 1.25rem;
        font-weight: 300;
    }
    .stTextInput > div > div > input:focus {
        border-color: #8b5cf6;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -10px rgba(139, 92, 246, 0.5);
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
    }
    .report-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    .report-card a {
        color: #a78bfa;
        text-decoration: none;
        border-bottom: 1px dashed rgba(167, 139, 250, 0.5);
        transition: all 0.2s ease;
    }
    .report-card a:hover {
        color: #c4b5fd;
        border-bottom: 1px solid #c4b5fd;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(11, 15, 25, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    [data-testid="stChatInput"] {
        border-radius: 12px;
    }
    .stepper-container {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
    }
    .step-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 12px;
    }
    .step-card {
        padding: 12px 8px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1fr solid rgba(255, 255, 255, 0.06);
        text-align: center;
        font-size: 0.82rem;
        font-weight: 500;
        color: #94a3b8;
    }
    .step-card.active {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%);
        border: 1px solid #8b5cf6;
        color: #ffffff;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
    }
    .step-card.completed {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }
    .kpi-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 12px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-lbl {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .debate-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
    }
    .debate-bull {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 14px;
        padding: 20px;
    }
    .debate-bear {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 14px;
        padding: 20px;
    }
"""

LIGHT_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        color: #0f172a;
        font-family: 'Outfit', sans-serif;
    }
    p, li, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #0f172a !important;
    }
    [data-testid="stFileUploader"] section, 
    [data-testid="stFileUploader"] div[data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        border: 1px dashed #cbd5e1 !important;
    }
    [data-testid="stFileUploader"] * {
        color: #0f172a !important;
    }
    [data-testid="stFileUploader"] button {
        border: 1px solid #cbd5e1 !important;
        background-color: #f8fafc !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #0f172a !important;
        letter-spacing: -0.02em;
    }
    .hero {
        padding: 5rem 2rem;
        text-align: center;
        background: transparent;
        margin-bottom: 2rem;
        position: relative;
    }
    .hero-title {
        font-size: 5rem;
        font-weight: 800;
        background: linear-gradient(to right, #0f172a 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        letter-spacing: -2px;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        color: #4f46e5;
        font-weight: 600;
        max-width: 600px;
        margin: 0 auto;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .search-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        border-radius: 16px;
        box-shadow: 0 10px 20px rgba(139, 92, 246, 0.15);
    }
    .stTextInput > div > div > input {
        border-radius: 14px;
        border: none;
        background: #ffffff;
        color: #0f172a;
        padding: 20px 24px;
        font-size: 1.25rem;
        font-weight: 400;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTextInput > div > div > input:focus {
        border-color: #8b5cf6;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3);
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -10px rgba(79, 70, 229, 0.5);
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
        color: white;
    }
    .report-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 2.5rem;
        border: 1px solid rgba(0, 0, 0, 0.05);
        box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.1);
    }
    .report-card a {
        color: #6d28d9;
        text-decoration: none;
        border-bottom: 1px dashed rgba(109, 40, 217, 0.5);
        transition: all 0.2s ease;
    }
    .report-card a:hover {
        color: #4c1d95;
        border-bottom: 1px solid #4c1d95;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(248, 250, 252, 0.95);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stChatMessage"] * {
        color: #0f172a !important;
    }
    [data-testid="stChatInput"] {
        border-radius: 12px;
    }
    .stepper-container {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
    }
    .step-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 12px;
    }
    .step-card {
        padding: 12px 8px;
        border-radius: 10px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        text-align: center;
        font-size: 0.82rem;
        font-weight: 500;
        color: #64748b;
    }
    .step-card.active {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid #6366f1;
        color: #4338ca !important;
        font-weight: 700;
        box-shadow: 0 2px 10px rgba(99, 102, 241, 0.15);
    }
    .step-card.completed {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #059669 !important;
        font-weight: 600;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }
    .kpi-box {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 14px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-lbl {
        font-size: 0.75rem;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .debate-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
    }
    .debate-bull {
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 14px;
        padding: 20px;
    }
    .debate-bear {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 14px;
        padding: 20px;
    }
"""

if st.session_state.theme == "dark":
    st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)
else:
    st.markdown(f"<style>{LIGHT_CSS}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/artificial-intelligence.png", width=60)
    st.markdown("### Modus Research AI")
    st.markdown("Enterprise-grade autonomous research agent.")
    st.divider()
    st.markdown("#### Capabilities")
    st.markdown("""
    - 🔍 **Deep Web Search**
    - 🧠 **Contextual Extraction**
    - ⚖️ **Contradiction Detection**
    - 📊 **Report Synthesis**
    """)
    st.divider()
    
    st.markdown("#### Private Knowledge Base")
    uploaded_files = st.file_uploader("Upload Documents (PDF)", accept_multiple_files=True, type=["pdf"])
    if st.button("Embed Documents"):
        if uploaded_files:
            with st.spinner("Embedding into FAISS..."):
                try:
                    files_payload = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                    res = requests.post(f"{API_BASE_URL}/upload_documents", files=files_payload)
                    res.raise_for_status()
                    st.success(res.json().get("message", "Success!"))
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        else:
            st.warning("Please select files first.")
            
    st.divider()
    theme_toggle = st.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
    if theme_toggle:
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"
        
    st.divider()
    st.caption("v1.0.0 | Powered by Gemini & Tavily")

# Hero Section
st.markdown("""
<div class="hero">
    <div class="hero-title">Nexus</div>
    <div class="hero-subtitle">Autonomous AI Research Intelligence</div>
</div>
""", unsafe_allow_html=True)

# Session state
if "topic_id" not in st.session_state:
    st.session_state.topic_id = None

# Input Section
st.markdown('<div class="search-container">', unsafe_allow_html=True)
topic_input = st.text_input("Research Topic", placeholder="Enter any complex topic, question, or hypothesis...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# Quick-Start Inspiration Chips
st.markdown("<p style='text-align: center; font-size: 0.85rem; color: #94a3b8; margin-top: 14px; margin-bottom: 6px;'>⚡ <b>Explore Trending Intelligence Vectors:</b></p>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
chip_selected = None
with c1:
    if st.button("🔬 AI Drug Discovery", key="chip_1", use_container_width=True):
        chip_selected = "Impact of Generative AI on Oncology Drug Discovery in 2026"
with c2:
    if st.button("⚡ Quantum Cryptography", key="chip_2", use_container_width=True):
        chip_selected = "Commercialization timeline and enterprise risks of Post-Quantum Cryptography"
with c3:
    if st.button("📊 2nm Semiconductor Risks", key="chip_3", use_container_width=True):
        chip_selected = "Geopolitical and supply chain risks in advanced 2nm semiconductor fabrication"
with c4:
    if st.button("🔋 Solid-State Batteries", key="chip_4", use_container_width=True):
        chip_selected = "Commercial viability of solid-state lithium metal batteries for EV mobility"

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    initiate_clicked = st.button("🚀 INITIATE INTELLIGENCE PROTOCOL")

target_topic = chip_selected if chip_selected else (topic_input if initiate_clicked else None)

if target_topic:
    with st.spinner("Initializing autonomous multi-agent pipeline..."):
        try:
            response = requests.post(f"{API_BASE_URL}/research", json={"topic": target_topic})
            response.raise_for_status()
            data = response.json()
            st.session_state.topic_id = data["id"]
            st.session_state[f"chat_history_{data['id']}"] = []
            st.success(f"Pipeline deployed for: '{target_topic}'")
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to start research: {e}")

# Status & Results Section
if st.session_state.topic_id:
    st.markdown("<br><hr style='border-color: rgba(139, 92, 246, 0.2);'><br>", unsafe_allow_html=True)
    
    # Poll API
    response = requests.get(f"{API_BASE_URL}/research/{st.session_state.topic_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        logs = data.get("logs", [])
        
        # Determine Stepper Active Nodes
        s1_class = "completed" if status in ["awaiting_approval", "completed"] or any("question" in l.get("message", "").lower() for l in logs) else "active"
        s2_class = "completed" if any("extracted" in l.get("message", "").lower() or "evaluat" in l.get("message", "").lower() for l in logs) else ("active" if any("search" in l.get("message", "").lower() for l in logs) else "")
        s3_class = "completed" if any("debate" in l.get("message", "").lower() or "judge" in l.get("message", "").lower() for l in logs) else ("active" if any("optimist" in l.get("message", "").lower() or "skeptic" in l.get("message", "").lower() for l in logs) else "")
        s4_class = "completed" if status == "completed" else ("active" if any("judge" in l.get("message", "").lower() or "compil" in l.get("message", "").lower() for l in logs) else "")

        if status == "awaiting_approval":
            s1_class = "active"
            s2_class = ""
            s3_class = ""
            s4_class = ""
            
        # Stepper Header Card
        st.markdown(f"""
        <div class="stepper-container">
            <div style="font-size: 1rem; font-weight: 700; display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span>🚀 Autonomous Research Pipeline &bull; Task #{st.session_state.topic_id}</span>
                <span style="font-size: 0.8rem; padding: 4px 10px; border-radius: 20px; background: rgba(139, 92, 246, 0.2); color: #c084fc; font-weight: 600;">{status.upper()}</span>
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 10px;">Topic: <i>{data.get('topic', '')}</i></div>
            <div class="step-grid">
                <div class="step-card {s1_class}">
                    <b>1. Decomposition</b><br><span style="font-size: 0.72rem; opacity: 0.8;">HITL Steering</span>
                </div>
                <div class="step-card {s2_class}">
                    <b>2. Hybrid Retrieval</b><br><span style="font-size: 0.72rem; opacity: 0.8;">FAISS + Web Search</span>
                </div>
                <div class="step-card {s3_class}">
                    <b>3. Dialectical Debate</b><br><span style="font-size: 0.72rem; opacity: 0.8;">Optimist vs Skeptic</span>
                </div>
                <div class="step-card {s4_class}">
                    <b>4. Executive Synthesis</b><br><span style="font-size: 0.72rem; opacity: 0.8;">Judge & Audit Logs</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if status == "processing":
            st.info("🔄 **LangGraph Execution in Progress:** Agents are gathering sources, extracting facts, and debating hypotheses.")
            
            # Agent Thought Console
            st.markdown("### 📟 Live Agent Thought Console")
            if logs:
                log_text = "\n".join([f"[{l.get('timestamp', '')[:19]}] {l.get('message', '')}" for l in logs])
                st.code(log_text, language="bash")
            else:
                st.code("[System] Initializing LangGraph state machine...", language="bash")
            
            st.caption("Auto-refreshing status (2s interval)...")
            time.sleep(2)
            st.rerun()
                
        elif status == "awaiting_approval":
            st.warning("⚠️ **Human-in-the-Loop Steering:** Review or edit the agent-generated research vectors before deep search commences.")
            
            with st.form("approve_questions_form"):
                questions = data.get("questions", [])
                edited_questions = []
                for i, q in enumerate(questions):
                    edited_q = st.text_input(f"Research Vector {i+1}", value=q.get("question_text"), key=f"q_{i}")
                    if edited_q.strip():
                        edited_questions.append(edited_q)
                
                new_q = st.text_input("Add an additional research vector (optional)", key="new_q")
                if new_q.strip():
                    edited_questions.append(new_q)
                    
                submitted = st.form_submit_button("✅ Approve Vectors & Launch Research")
                if submitted:
                    with st.spinner("Confirming research vectors..."):
                        try:
                            approve_resp = requests.post(
                                f"{API_BASE_URL}/research/{st.session_state.topic_id}/approve", 
                                json={"questions": edited_questions}
                            )
                            approve_resp.raise_for_status()
                            st.success("Vectors confirmed! Pipeline resuming...")
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to approve vectors: {e}")
                            
        elif status == "completed":
            report = data.get("final_report", "")
            sources = data.get("sources", [])
            findings = data.get("findings", [])
            
            word_count = len(report.split()) if report else 0
            read_time = max(1, round(word_count / 200))
            
            st.success("✨ **Intelligence Briefing Compiled Successfully!**")
            
            # Executive KPI Row
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-box">
                    <div class="kpi-val">{len(sources)}</div>
                    <div class="kpi-lbl">Verified Sources</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-val">{len(findings)}</div>
                    <div class="kpi-lbl">Extracted Claims</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-val">~{read_time}m</div>
                    <div class="kpi-lbl">Est. Read Time</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-val">100%</div>
                    <div class="kpi-lbl">Audit Traceable</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Executive Export Action Center
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label="📥 Download Full Markdown Report (.md)",
                    data=report,
                    file_name=f"Intelligence_Report_{st.session_state.topic_id}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with exp_col2:
                briefing_txt = f"# Executive Intelligence Summary: {data.get('topic')}\n\n" + report
                st.download_button(
                    label="📑 Download Executive Text Briefing (.txt)",
                    data=briefing_txt,
                    file_name=f"Executive_Briefing_{st.session_state.topic_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Side-by-Side Multi-Agent Debate Cards
            st.markdown("### ⚖️ Multi-Agent Dialectical Debate Insights")
            st.caption("Side-by-side synthesis of Bull Case opportunities vs. Bear Case risks prior to final Judge synthesis.")
            
            # Derive top findings for Bull vs Bear preview
            bull_findings = [f for f in findings if any(w in f['category'].lower() for w in ['benefit', 'opportunit', 'growth', 'positive', 'market'])]
            bear_findings = [f for f in findings if any(w in f['category'].lower() for w in ['risk', 'limitation', 'downside', 'threat', 'cost', 'failure'])]
            
            bull_sample = bull_findings[0]['finding_text'] if bull_findings else (findings[0]['finding_text'] if findings else "Strong market adoption catalysts and strategic expansion upside.")
            bear_sample = bear_findings[0]['finding_text'] if bear_findings else (findings[-1]['finding_text'] if len(findings) > 1 else "Critical regulatory, technical friction, and operational adoption barriers.")
            
            st.markdown(f"""
            <div class="debate-grid">
                <div class="debate-bull">
                    <h4 style="color: #34d399 !important; margin-top: 0;">📈 Optimist Analyst (Bull Case)</h4>
                    <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 0;"><b>Key Upside Driver:</b> {bull_sample}</p>
                    <div style="margin-top: 8px; font-size: 0.78rem; color: #34d399; font-weight: 600;">✓ Focus: Catalysts, ROI, Strategic Acceleration</div>
                </div>
                <div class="debate-bear">
                    <h4 style="color: #f87171 !important; margin-top: 0;">📉 Skeptic Analyst (Bear Case)</h4>
                    <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 0;"><b>Key Risk Vector:</b> {bear_sample}</p>
                    <div style="margin-top: 8px; font-size: 0.78rem; color: #f87171; font-weight: 600;">⚠️ Focus: Failure Modes, Compliance, Vulnerabilities</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Audio Briefing Player
            st.markdown("#### 🎧 Multi-Modal Executive Audio Briefing")
            audio_col1, audio_col2 = st.columns([1, 2])
            with audio_col1:
                generate_audio = st.button("🎙️ Generate 60-Sec Audio Briefing", key=f"gen_audio_{st.session_state.topic_id}", use_container_width=True)
            
            audio_key = f"audio_bytes_{st.session_state.topic_id}"
            if generate_audio:
                with st.spinner("Synthesizing audio briefing from report..."):
                    try:
                        from gtts import gTTS
                        import io
                        # Clean markdown for natural speech
                        speech_text = f"Executive intelligence briefing on {data.get('topic')}. "
                        if report:
                            clean_text = report.replace("#", "").replace("*", "").replace("[SRC-", "Source ").replace("]", "")
                            speech_text += " ".join(clean_text.split()[:140]) + ". End of summary. Explore the full audit logs for citations."
                        
                        tts = gTTS(text=speech_text, lang='en', tld='com')
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        audio_fp.seek(0)
                        st.session_state[audio_key] = audio_fp.read()
                    except Exception as audio_err:
                        st.error(f"Audio synthesis error: {audio_err}")

            if audio_key in st.session_state and st.session_state[audio_key]:
                with audio_col2:
                    st.audio(st.session_state[audio_key], format="audio/mp3")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display Final Synthesized Report in Card
            st.markdown("### 📄 Final Synthesized Intelligence Report")
            if report:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Traceability section in tabs
            st.markdown("### 🔍 Traceability & Audit Logs")
            tab1, tab2, tab3 = st.tabs(["📑 Sources Retrieved", "❓ Research Vectors Addressed", "🔍 Citation Explorer (Hallucination Check)"])
            
            with tab1:
                st.markdown("The following sources were automatically retrieved and analyzed:")
                for i, s in enumerate(sources):
                    st.markdown(f"{i+1}. **[{s['title']}]({s['url']})**")
                    with st.expander("View Source Snippet"):
                        st.caption(f"Extracted from: {s['source_name']}")
                        st.write(s.get("content", "No snippet available.")[:300] + "...")
                        
            with tab2:
                st.markdown("The main topic was decomposed into these specific research vectors:")
                for q in data.get("questions", []):
                    st.info(q.get("question_text"))
                    
            with tab3:
                st.markdown("Verify the AI's claims by cross-referencing `[SRC-X]` tags with the exact text the AI extracted from the source.")
                if not findings:
                    st.info("No explicit findings found.")
                else:
                    for f in findings:
                        with st.expander(f"[SRC-{f['id']}] Extracted Claim"):
                            st.markdown(f"> {f['finding_text']}")
                            st.caption(f"Category: {f['category']} | AI Confidence: {f['confidence']}")
                            
                            matching_source = next((s for s in sources if s["id"] == f["source_id"]), None)
                            if matching_source:
                                st.markdown(f"**Original Source:** [{matching_source['title']}]({matching_source['url']})")
                            else:
                                st.markdown("**Original Source:** Unknown")
                                
            # Interactive Chat with Report (RAG)
            st.markdown("<br><hr style='border-color: rgba(139, 92, 246, 0.2);'><br>", unsafe_allow_html=True)
            st.markdown("### 💬 Interactive Intelligence: Chat with this Report")
            st.caption("Ask follow-up questions, request specific executive breakdowns, or probe deeper into the findings and citations.")
            
            # Contextual Smart Follow-Up Suggestions
            st.markdown("<p style='font-size: 0.82rem; color: #94a3b8; margin-top: 6px; margin-bottom: 6px;'>💡 <b>Suggested Strategic Inquiries:</b></p>", unsafe_allow_html=True)
            sug1, sug2, sug3 = st.columns(3)
            suggested_prompt = None
            with sug1:
                if st.button("⚠️ Top 3 Regulatory & Risk Barriers", key="sug_1", use_container_width=True):
                    suggested_prompt = "What are the top 3 regulatory and adoption barriers highlighted in this research?"
            with sug2:
                if st.button("📈 Quantify ROI & Timeline", key="sug_2", use_container_width=True):
                    suggested_prompt = "Can you provide a quantitative breakdown of the projected commercial timeline and ROI catalysts?"
            with sug3:
                if st.button("⚔️ Skeptic Counter-Arguments", key="sug_3", use_container_width=True):
                    suggested_prompt = "What are the strongest counter-arguments raised by the Skeptic Analyst against this topic?"
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            chat_key = f"chat_history_{st.session_state.topic_id}"
            if chat_key not in st.session_state:
                st.session_state[chat_key] = [
                    {"role": "assistant", "content": f"Hello! I've fully analyzed and synthesized the findings on **{data.get('topic', 'this topic')}**. How can I assist you with this report?"}
                ]
            
            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            chat_input_val = st.chat_input("Ask a question about this research report...")
            active_chat_prompt = suggested_prompt if suggested_prompt else chat_input_val
            
            if active_chat_prompt:
                st.session_state[chat_key].append({"role": "user", "content": active_chat_prompt})
                with st.chat_message("user"):
                    st.markdown(active_chat_prompt)
                
                with st.chat_message("assistant"):
                    def sse_stream_generator():
                        payload = {
                            "message": active_chat_prompt,
                            "history": st.session_state[chat_key][:-1]
                        }
                        try:
                            # Stream from FastAPI SSE endpoint
                            with requests.post(
                                f"{API_BASE_URL}/research/{st.session_state.topic_id}/chat/stream",
                                json=payload,
                                stream=True,
                                timeout=60
                            ) as response:
                                response.raise_for_status()
                                for line in response.iter_lines(decode_unicode=True):
                                    if line:
                                        if line.startswith("data: "):
                                            raw_data = line[6:].strip()
                                            if raw_data == "[DONE]":
                                                break
                                            try:
                                                parsed = json.loads(raw_data)
                                                token = parsed.get("chunk", "")
                                                if token:
                                                    yield token
                                            except json.JSONDecodeError:
                                                yield raw_data
                        except Exception as e:
                            # Fallback to standard chat endpoint if streaming encounters network issue
                            try:
                                fallback_resp = requests.post(
                                    f"{API_BASE_URL}/research/{st.session_state.topic_id}/chat",
                                    json=payload,
                                    timeout=60
                                )
                                fallback_resp.raise_for_status()
                                yield fallback_resp.json().get("reply", "No response received.")
                            except Exception as fb_err:
                                yield f"*(Error receiving answer: {fb_err})*"

                    # st.write_stream renders real-time token typewriter animation
                    full_response = st.write_stream(sse_stream_generator)
                    st.session_state[chat_key].append({"role": "assistant", "content": full_response})
                    
        elif status == "failed":
            st.error("❌ Research Pipeline Failed.")
            with st.expander("View Error Logs"):
                st.text(data.get("final_report"))
            
    else:
        st.error("Could not fetch status from backend API.")

