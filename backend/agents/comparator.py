import json
from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session

def detect_contradictions(topic: domain.ResearchTopic, findings: list[domain.Finding], db: Session) -> list[domain.Contradiction]:
    """Analyzes extracted findings across different sources to detect contradictions."""
    llm = get_llm()
    
    # We group findings to avoid passing too much context at once
    # In a real enterprise app, you'd use a more sophisticated grouping (e.g. via embeddings clustering)
    # Here we just pass all findings for the topic.
    
    findings_text = ""
    for idx, f in enumerate(findings):
        # f.source_obj is loaded because we are in session
        source_name = f.source_obj.source_name if f.source_obj else "Unknown"
        findings_text += f"[{idx+1}] Source: {source_name} | Finding: {f.finding_text}\n"
    
    if not findings_text:
        return []

    prompt = PromptTemplate.from_template(
        """You are an expert enterprise research AI.
Review the following list of research findings gathered from various sources regarding the topic: "{topic}"

Your task is to identify any direct contradictions or conflicting information among the findings.
For example, if Source A says "Costs decreased by 20%" and Source B says "Costs increased significantly", that is a contradiction.

Findings:
{findings_text}

Return ONLY a valid JSON list of objects describing the contradictions. Do not include markdown formatting or backticks.
[
  {{"description": "Brief description of the conflict", "reason": "Detailed explanation of why they conflict, referencing the sources"}}
]
If there are no contradictions, return an empty list: []
"""
    )
    
    chain = prompt | llm
    
    db_contradictions = []
    
    try:
        from backend.core.utils import parse_json_from_llm, robust_invoke
        response = robust_invoke(chain, {
            "topic": topic.topic,
            "findings_text": findings_text[:30000] # Limit token usage
        })
        
        contradictions_data = parse_json_from_llm(response.content)
        
        for item in contradictions_data:
            c = domain.Contradiction(
                topic_id=topic.id,
                description=item.get("description", ""),
                reason=item.get("reason", "")
            )
            db.add(c)
            db_contradictions.append(c)
            
        db.commit()
        for c in db_contradictions:
            db.refresh(c)
            
    except Exception as e:
        print(f"Error detecting contradictions: {e}")
        
    return db_contradictions
