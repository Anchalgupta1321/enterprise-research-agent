from sqlalchemy.orm import Session
from backend.models import domain
from backend.agents.question_gen import generate_questions
from backend.agents.search_agent import search_for_questions
from backend.agents.extractor import extract_findings
from backend.agents.comparator import detect_contradictions
from backend.agents.report_gen import generate_report
import traceback

def run_research_pipeline(topic_id: int):
    from backend.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
        if not db_topic:
            return
            
        # 1. Generate Questions
        print("Generating questions...")
        questions = generate_questions(db_topic, db)
        
        # 2. Search Sources
        print("Searching sources...")
        sources = search_for_questions(db_topic, questions, db)
        
        # 3. Extract Findings (and store in Vector DB implicitly)
        print("Extracting findings...")
        findings = extract_findings(questions, sources, db)
        
        # 4. Detect Contradictions
        print("Detecting contradictions...")
        contradictions = detect_contradictions(db_topic, findings, db)
        
        # 5. Generate Report
        print("Generating report...")
        report = generate_report(db_topic, questions, findings, contradictions, db)
        
        db_topic.status = "completed"
        # final_report is already set in generate_report, but we ensure status is completed
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
