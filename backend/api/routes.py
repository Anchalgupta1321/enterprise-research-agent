from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import traceback
import json

from backend.core.database import get_db, SessionLocal
from backend.models import schemas, domain
from backend.agents.orchestrator import run_research_pipeline, run_question_generation
from backend.agents.chat_agent import generate_chat_reply, stream_chat_reply

from fastapi import File, UploadFile
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.services.vector_store import vector_store

router = APIRouter()

@router.post("/upload_documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    docs_processed = 0
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            chunks = text_splitter.split_documents(pages)
            
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [{"source": file.filename, "type": "local_document", "content": chunk.page_content} for chunk in chunks]
            
            vector_store.add_texts(texts, metadatas)
            docs_processed += 1
            
        os.remove(file_path)
        
    return {"message": f"Successfully embedded {docs_processed} documents."}

@router.post("/research", response_model=schemas.ResearchTopicSchema)
async def start_research(request: schemas.ResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Create the initial topic record
    db_topic = domain.ResearchTopic(topic=request.topic, status="processing")
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    # Start question generation in the background
    background_tasks.add_task(run_question_generation, db_topic.id)
    
    return db_topic

@router.post("/research/{topic_id}/approve", response_model=schemas.ResearchTopicSchema)
async def approve_questions(topic_id: int, request: schemas.ApproveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    if db_topic.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Topic is not awaiting approval")

    # Delete existing questions and replace with the newly approved ones
    db.query(domain.Question).filter(domain.Question.topic_id == topic_id).delete()
    
    for q_text in request.questions:
        new_q = domain.Question(topic_id=topic_id, question_text=q_text)
        db.add(new_q)
        
    db_topic.status = "processing"
    db.commit()
    db.refresh(db_topic)
    
    # Resume the pipeline
    background_tasks.add_task(run_research_pipeline, db_topic.id)
    
    return db_topic

@router.get("/research/{topic_id}", response_model=schemas.ResearchTopicSchema)
def get_research_status(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic

@router.post("/research/{topic_id}/chat", response_model=schemas.ChatResponse)
def chat_with_report(topic_id: int, request: schemas.ChatRequest, db: Session = Depends(get_db)):
    db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if not db_topic.final_report:
        raise HTTPException(status_code=400, detail="Research report has not been generated yet.")
    
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    reply = generate_chat_reply(db_topic, request.message, history_dicts)
    return schemas.ChatResponse(reply=reply)

@router.post("/research/{topic_id}/chat/stream")
def stream_chat_with_report(topic_id: int, request: schemas.ChatRequest, db: Session = Depends(get_db)):
    db_topic = db.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if not db_topic.final_report:
        raise HTTPException(status_code=400, detail="Research report has not been generated yet.")
    
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    def event_stream():
        for chunk in stream_chat_reply(db_topic, request.message, history_dicts):
            if chunk:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


