import streamlit as st
import requests
import time
import os

# Allows the app to connect to the Render backend when deployed
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

st.set_page_config(
    page_title="Modus Enterprise Research Agent", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium enterprise look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Hide Streamlit Header and Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Main background and fonts */
    .stApp {
        background: linear-gradient(180deg, #050505 0%, #0b0f19 100%);
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }
    
    /* Custom Hero Section */
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
    
    /* Search Box Container */
    .search-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        border-radius: 16px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
    }
    
    /* Input box styling */
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
    
    /* Button styling */
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
    
    /* Glassmorphism Cards */
    .report-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    
    /* Markdown formatting inside report */
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
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(11, 15, 25, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
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
st.markdown('</div><br>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚀 INITIATE INTELLIGENCE PROTOCOL"):
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
                
        elif status == "awaiting_approval":
            st.warning("⚠️ **Review Required:** The agent has generated sub-questions for your topic. Please review and edit them before the search begins.")
            
            # Form for editing questions
            with st.form("approve_questions_form"):
                questions = data.get("questions", [])
                edited_questions = []
                for i, q in enumerate(questions):
                    edited_q = st.text_input(f"Question {i+1}", value=q.get("question_text"), key=f"q_{i}")
                    if edited_q.strip():
                        edited_questions.append(edited_q)
                
                # Option to add a new question
                new_q = st.text_input("Add a new question (optional)", key="new_q")
                if new_q.strip():
                    edited_questions.append(new_q)
                    
                submitted = st.form_submit_button("Approve & Continue Research")
                if submitted:
                    with st.spinner("Submitting approved questions..."):
                        try:
                            approve_resp = requests.post(
                                f"{API_BASE_URL}/research/{st.session_state.topic_id}/approve", 
                                json={"questions": edited_questions}
                            )
                            approve_resp.raise_for_status()
                            st.success("Questions approved! Resuming research...")
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to approve questions: {e}")
                            
        elif status == "completed":
            report = data.get("final_report")
            
            st.success("✨ Research Completed Successfully!")
            
            # Dashboard Metrics
            st.markdown("### Process Overview")
            m1, m2, m3 = st.columns(3)
            m1.metric("Sources Analyzed", len(data.get("sources", [])))
            m2.metric("Claims Extracted", len(data.get("findings", [])))
            m3.metric("Research Vectors", len(data.get("questions", [])))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display Report in a Card
            st.markdown("### Final Synthesized Report")
            if report:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Traceability section in tabs
            st.markdown("### Traceability & Audit Logs")
            tab1, tab2, tab3 = st.tabs(["📑 Sources Retrieved", "❓ Generated Sub-Questions", "🔍 Citation Explorer (Hallucination Check)"])
            
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
                    
            with tab3:
                st.markdown("Verify the AI's claims by cross-referencing `[SRC-X]` tags with the exact text the AI extracted from the source.")
                findings = data.get("findings", [])
                if not findings:
                    st.info("No explicit findings found.")
                else:
                    for f in findings:
                        with st.expander(f"[SRC-{f['id']}] Extracted Claim"):
                            st.markdown(f"> {f['finding_text']}")
                            st.caption(f"Category: {f['category']} | AI Confidence: {f['confidence']}")
                            
                            matching_source = next((s for s in data.get("sources", []) if s["id"] == f["source_id"]), None)
                            if matching_source:
                                st.markdown(f"**Original Source:** [{matching_source['title']}]({matching_source['url']})")
                            else:
                                st.markdown("**Original Source:** Unknown")
                    
        elif status == "failed":
            st.error("❌ Research Pipeline Failed.")
            with st.expander("View Error Logs"):
                st.text(data.get("final_report"))
            
    else:
        st.error("Could not fetch status from backend API.")

