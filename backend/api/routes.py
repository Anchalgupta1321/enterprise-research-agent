from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import traceback

from backend.core.database import get_db, SessionLocal
from backend.models import schemas, domain
from backend.agents.orchestrator import run_research_pipeline

router = APIRouter()

def background_research_task(topic_id: int):
    # Create a new session for the background task
    db = SessionLocal()
    try:
        run_research_pipeline(topic_id, db)
    finally:
        db.close()

@router.post("/research", response_model=schemas.ResearchTopicSchema)
async def start_research(request: schemas.ResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Create the initial topic record
    db_topic = domain.ResearchTopic(topic=request.topic, status="processing")
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    # Start the orchestrator in the background with just the ID
    background_tasks.add_task(run_research_pipeline, db_topic.id)
    
    return db_topic

@router.get("/research/{topic_id}", response_model=schemas.ResearchTopicSchema)
def get_research_status(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic
