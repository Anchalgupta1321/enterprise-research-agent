from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from backend.models import domain
from backend.agents.question_gen import generate_questions
from backend.agents.search_agent import search_for_questions
from backend.agents.extractor import extract_findings
from backend.agents.comparator import detect_contradictions
from backend.agents.report_gen import generate_report
import traceback

class ResearchState(TypedDict):
    topic_id: int
    loop_count: int
    questions: List[Any]
    sources: List[Any]
    findings: List[Any]
    contradictions: List[Any]
    needs_more_info: bool

def run_question_generation(topic_id: int):
    from backend.core.database import SessionLocal
    db = SessionLocal()
    try:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if not db_topic:
            return
            
        print("Generating initial questions...")
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
            print(f"Searching sources... (Loop {state.get('loop_count', 0) + 1})")
            sources = search_for_questions(db_topic, state.get("questions", []), db)
            current_sources = state.get("sources", [])
            current_sources.extend(sources)
            return {"sources": current_sources}

        def extract_findings_node(state: ResearchState):
            print("Extracting findings...")
            findings = extract_findings(state.get("questions", []), state.get("sources", []), db)
            return {"findings": findings}

        def evaluate_sufficiency_node(state: ResearchState):
            loop_count = state.get("loop_count", 0)
            print(f"Evaluating sufficiency (Loop {loop_count + 1})...")
            
            needs_more = False
            if loop_count < 1:
                needs_more = True
                
            return {"loop_count": loop_count + 1, "needs_more_info": needs_more}

        def should_continue(state: ResearchState):
            return "search_sources" if state.get("needs_more_info", False) else "detect_contradictions"

        def detect_contradictions_node(state: ResearchState):
            print("Detecting contradictions...")
            contradictions = detect_contradictions(db_topic, state.get("findings", []), db)
            return {"contradictions": contradictions}

        def generate_report_node(state: ResearchState):
            print("Generating report...")
            report = generate_report(db_topic, state.get("questions", []), state.get("findings", []), state.get("contradictions", []), db)
            return {}

        workflow = StateGraph(ResearchState)
        
        workflow.add_node("search_sources", search_sources_node)
        workflow.add_node("extract_findings", extract_findings_node)
        workflow.add_node("evaluate_sufficiency", evaluate_sufficiency_node)
        workflow.add_node("detect_contradictions", detect_contradictions_node)
        workflow.add_node("generate_report", generate_report_node)
        
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
        workflow.add_edge("generate_report", END)
        
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
