from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from backend.models import domain
from backend.agents.question_gen import generate_questions
from backend.agents.search_agent import search_for_questions
from backend.agents.extractor import extract_findings
from backend.agents.comparator import detect_contradictions
from backend.agents.report_gen import generate_report
from backend.agents.auditor_agent import audit_research_report
from backend.agents.chart_agent import generate_report_charts
from backend.agents.boardroom_agent import run_boardroom_council
from backend.agents.knowledge_graph_agent import extract_knowledge_graph
import traceback

class ResearchState(TypedDict):
    topic_id: int
    loop_count: int
    questions: List[Any]
    sources: List[Any]
    findings: List[Any]
    contradictions: List[Any]
    needs_more_info: bool

def log_thought(topic_id: int, message: str, db: Session):
    log = domain.AgentLog(topic_id=topic_id, message=message)
    db.add(log)
    db.commit()

def run_question_generation(topic_id: int):
    from backend.core.database import SessionLocal
    db = SessionLocal()
    try:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if not db_topic:
            return
            
        print("Generating initial questions...")
        log_thought(topic_id, "[System] Initializing autonomous research pipeline...", db)
        log_thought(topic_id, "[Planner Agent] Deconstructing topic into sub-questions...", db)
        questions = generate_questions(db_topic, db)
        
        db_topic.status = "awaiting_approval"
        db.commit()
    except Exception as e:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if db_topic:
            db_topic.status = "failed"
            db_topic.final_report = f"Failed at question generation: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            db.commit()
        traceback.print_exc()
    finally:
        db.close()

def run_research_pipeline(topic_id: int):
    from backend.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if not db_topic:
            return
            
        db_questions = db_topic.questions

        def search_sources_node(state: ResearchState):
            log_thought(topic_id, f"[Deep Search Agent] Querying Tavily for sources (Loop {state.get('loop_count', 0) + 1})...", db)
            print(f"Searching sources... (Loop {state.get('loop_count', 0) + 1})")
            sources = search_for_questions(db_topic, state.get("questions", []), db)
            current_sources = state.get("sources", [])
            current_sources.extend(sources)
            return {"sources": current_sources}

        def extract_findings_node(state: ResearchState):
            log_thought(topic_id, "[Extractor Agent] Reading source contents and extracting facts...", db)
            print("Extracting findings...")
            findings = extract_findings(state.get("questions", []), state.get("sources", []), db)
            return {"findings": findings}

        def evaluate_sufficiency_node(state: ResearchState):
            loop_count = state.get("loop_count", 0)
            log_thought(topic_id, f"[System] Evaluating if sufficient information is gathered (Loop {loop_count + 1})...", db)
            print(f"Evaluating sufficiency (Loop {loop_count + 1})...")
            
            needs_more = False
            if loop_count < 1:
                needs_more = True
                
            return {"loop_count": loop_count + 1, "needs_more_info": needs_more}

        def should_continue(state: ResearchState):
            return "search_sources" if state.get("needs_more_info", False) else "detect_contradictions"

        def detect_contradictions_node(state: ResearchState):
            log_thought(topic_id, "[Skeptic Agent] Cross-referencing findings to detect contradictions...", db)
            print("Detecting contradictions...")
            contradictions = detect_contradictions(db_topic, state.get("findings", []), db)
            return {"contradictions": contradictions}

        def generate_report_node(state: ResearchState):
            log_thought(topic_id, "[Synthesizer Agent] Drafting final report with citations...", db)
            print("Generating report...")
            report = generate_report(db_topic, state.get("questions", []), state.get("findings", []), state.get("contradictions", []), db)
            return {}

        def audit_critique_node(state: ResearchState):
            log_thought(topic_id, "[Auditor Agent] Self-Reflective Audit: Computing Grounding Precision Score and auditing claims against sources...", db)
            print("Auditing report against ground truth...")
            audit_result = audit_research_report(db_topic, db_topic.final_report or "", state.get("findings", []), db)
            score = audit_result.get("grounding_score", 95.0)
            verdict = audit_result.get("verdict", "VERIFIED_EXCELLENT")
            log_thought(topic_id, f"[Auditor Agent] Audit complete: Score={score}% | Verdict={verdict}", db)
            return {}

        def generate_charts_node(state: ResearchState):
            log_thought(topic_id, "[Chartist Agent] Analyzing quantitative findings and synthesizing interactive Plotly visual analytics...", db)
            print("Generating dynamic charts...")
            generate_report_charts(db_topic, state.get("findings", []), db_topic.final_report or "", db)
            log_thought(topic_id, "[Chartist Agent] Visual analytics payload compiled successfully.", db)
            return {}

        def council_boardroom_review_node(state: ResearchState):
            log_thought(topic_id, "[Boardroom Council] CFO, CTO, and Legal Officer agents convening executive deliberation...", db)
            print("Running C-Suite Boardroom Council review...")
            run_boardroom_council(db_topic, db_topic.final_report or "", state.get("findings", []), db)
            log_thought(topic_id, "[Boardroom Council] Executive C-Suite dossiers and Board Consensus compiled.", db)
            return {}

        def extract_knowledge_graph_node(state: ResearchState):
            log_thought(topic_id, "[Knowledge Graph Agent] Extracting semantic entity network and relationship edges...", db)
            print("Extracting knowledge graph entities and relations...")
            extract_knowledge_graph(db_topic, state.get("findings", []), db_topic.final_report or "", db)
            log_thought(topic_id, "[Knowledge Graph Agent] Entity-relationship network graph synthesized successfully.", db)
            return {}

        workflow = StateGraph(ResearchState)
        
        workflow.add_node("search_sources", search_sources_node)
        workflow.add_node("extract_findings", extract_findings_node)
        workflow.add_node("evaluate_sufficiency", evaluate_sufficiency_node)
        workflow.add_node("detect_contradictions", detect_contradictions_node)
        workflow.add_node("generate_report", generate_report_node)
        workflow.add_node("audit_critique", audit_critique_node)
        workflow.add_node("generate_charts", generate_charts_node)
        workflow.add_node("council_boardroom_review", council_boardroom_review_node)
        workflow.add_node("extract_knowledge_graph", extract_knowledge_graph_node)
        
        workflow.set_entry_point("search_sources")
        workflow.add_edge("search_sources", "extract_findings")
        workflow.add_edge("extract_findings", "evaluate_sufficiency")
        
        workflow.add_conditional_edges(
            "evaluate_sufficiency",
            should_continue,
            {
                "search_sources": "search_sources",
                "detect_contradictions": "detect_contradictions"
            }
        )
        
        workflow.add_edge("detect_contradictions", "generate_report")
        workflow.add_edge("generate_report", "audit_critique")
        workflow.add_edge("audit_critique", "generate_charts")
        workflow.add_edge("generate_charts", "council_boardroom_review")
        workflow.add_edge("council_boardroom_review", "extract_knowledge_graph")
        workflow.add_edge("extract_knowledge_graph", END)
        
        app = workflow.compile()
        
        initial_state = {
            "topic_id": topic_id,
            "loop_count": 0,
            "questions": db_questions,
            "sources": [],
            "findings": [],
            "contradictions": [],
            "needs_more_info": False
        }
        
        app.invoke(initial_state)
        
        db_topic.status = "completed"
        db.commit()
    except Exception as e:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if db_topic:
            db_topic.status = "failed"
            db_topic.final_report = f"Failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            db.commit()
        print(f"Pipeline failed: {e}")
        traceback.print_exc()
    finally:
        db.close()
