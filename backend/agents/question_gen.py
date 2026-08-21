import json
from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session

def generate_questions(topic: domain.ResearchTopic, db: Session) -> list[domain.Question]:
    """Generates sub-questions for a research topic."""
    llm = get_llm()
    
    prompt = PromptTemplate.from_template(
        """You are an expert enterprise research AI.
Given the following research topic, generate 5 specific, highly relevant sub-questions that need to be answered to fully cover this topic.
Focus on business impact, technology, risks, benefits, and implementation challenges.

Research Topic: {topic}

Return ONLY a valid JSON list of strings representing the questions. Do not include markdown formatting or backticks.
Example: ["Question 1", "Question 2"]
"""
    )
    
    chain = prompt | llm
    
    try:
        from backend.core.utils import parse_json_from_llm, robust_invoke
        response = robust_invoke(chain, {"topic": topic.topic})
        
        questions_text = parse_json_from_llm(response.content)

        
        db_questions = []
        for q_text in questions_text:
            db_q = domain.Question(topic_id=topic.id, question_text=q_text)
            db.add(db_q)
            db_questions.append(db_q)
            
        db.commit()
        
        # Refresh to get IDs
        for q in db_questions:
            db.refresh(q)
            
        return db_questions
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []
