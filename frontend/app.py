import streamlit as st
import requests
import time
import os

API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="Modus Enterprise Research Agent", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium enterprise look
st.markdown("""
<style>
    /* Main background and fonts */
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f0f6fc !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom Hero Section */
    .hero {
        padding: 3rem 0;
        text-align: center;
        background: linear-gradient(90deg, #1f2937 0%, #111827 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(#60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #9ca3af;
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #374151;
        background-color: #1f2937;
        color: white;
        padding: 12px;
        font-size: 1.1rem;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    
    /* Card for results */
    .report-card {
        background-color: #1f2937;
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    /* Markdown formatting inside report */
    .report-card a {
        color: #60a5fa;
        text-decoration: none;
    }
    .report-card a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

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
    st.caption("v1.0.0 | Powered by Gemini & Tavily")

# Hero Section
st.markdown("""
<div class="hero">
    <div class="hero-title">Enterprise AI Research Agent</div>
    <div class="hero-subtitle">Generate comprehensive, traceable research reports automatically at scale.</div>
</div>
""", unsafe_allow_html=True)

# Session state
if "topic_id" not in st.session_state:
    st.session_state.topic_id = None

# Input Section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    topic_input = st.text_input("Research Topic", placeholder="e.g., How is AI transforming retail operations?", label_visibility="collapsed")
    
    if st.button("🚀 Start Research Pipeline"):
        if topic_input:
            with st.spinner("Initializing autonomous agents..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/research", json={"topic": topic_input})
                    response.raise_for_status()
                    data = response.json()
                    st.session_state.topic_id = data["id"]
                    st.success("Pipeline deployed successfully! Agents are now working in the background.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to start research: {e}")
        else:
            st.warning("Please enter a research topic to begin.")

# Status & Results Section
if st.session_state.topic_id:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # A simple poll
    response = requests.get(f"{API_BASE_URL}/research/{st.session_state.topic_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        
        # Status Header
        st.markdown(f"### Research Tracker: Task #{st.session_state.topic_id}")
        
        if status == "processing":
            st.info("🔄 **Pipeline is currently running.** The agents are gathering sources, extracting facts, and synthesizing the report. This usually takes 1-3 minutes.")
            
            # Simulated progress UI (since we don't have real-time websockets in MVP)
            progress_bar = st.progress(0)
            st.caption("Waiting for completion...")
            
            if st.button("Refresh Status ⟳"):
                st.rerun()
                
        elif status == "completed":
            report = data.get("final_report")
            
            st.success("✨ Research Completed Successfully!")
            
            # Display Report in a Card
            if report:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Traceability section in tabs
            st.markdown("### Traceability & Audit Logs")
            tab1, tab2 = st.tabs(["📑 Sources Retrieved", "❓ Generated Sub-Questions"])
            
            with tab1:
                st.markdown("The following sources were automatically retrieved and analyzed:")
                for i, s in enumerate(data.get("sources", [])):
                    st.markdown(f"{i+1}. **[{s['title']}]({s['url']})**")
                    with st.expander("View Source Snippet"):
                        st.caption(f"Extracted from: {s['source_name']}")
                        st.write(s.get("content", "No snippet available.")[:300] + "...")
                        
            with tab2:
                st.markdown("The main topic was broken down into these specific research vectors:")
                for q in data.get("questions", []):
                    st.info(q.get("question_text"))
                    
        elif status == "failed":
            st.error("❌ Research Pipeline Failed.")
            with st.expander("View Error Logs"):
                st.text(data.get("final_report"))
            
    else:
        st.error("Could not fetch status from backend API.")

