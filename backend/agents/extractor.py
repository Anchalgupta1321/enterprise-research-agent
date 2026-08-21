import json
from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session
from backend.services.vector_store import vector_store

def extract_findings(questions: list[domain.Question], sources: list[domain.Source], db: Session) -> list[domain.Finding]:
    """Extracts key findings from the gathered sources using the LLM."""
    llm = get_llm()
    
    prompt = PromptTemplate.from_template(
        """You are an expert enterprise research AI.
Given the following source text, extract key findings related to this research question: "{question}"

Source text:
{source_text}

Extract only the most important, factual findings. Classify each finding into a category (e.g., "Benefits", "Risks", "Technologies", "Business Impact") and assign a confidence level ("High", "Medium", "Low") based on the text.

Return ONLY a valid JSON list of objects with the following schema. Do not include markdown formatting or backticks.
[
  {{"finding": "The extracted fact", "category": "Category Name", "confidence": "High"}}
]
If no relevant findings are in the text, return an empty list: []
"""
    )
    
    chain = prompt | llm
    
    db_findings = []
    texts_to_embed = []
    metadatas_to_embed = []
    
    for q in questions:
        for s in sources:
            # Simple heuristic: only process if source has content
            if not s.content or len(s.content) < 50:
                continue
            
            # Limit to first chunk only to stay within Free Tier limits (20 RPM)
            content_chunk = s.content[:15000] # Use only the first big chunk
            
            try:
                import time
                time.sleep(6) # Strict Rate limit: Max 10 requests per minute for Gemini Free Tier
                
                from backend.core.utils import parse_json_from_llm, robust_invoke
                response = robust_invoke(chain, {
                    "question": q.question_text,
                    "source_text": content_chunk
                })
                
                findings_data = parse_json_from_llm(response.content)
                
                for item in findings_data:
                    finding = domain.Finding(
                        question_id=q.id,
                        source_id=s.id,
                        finding_text=item.get("finding", ""),
                        category=item.get("category", "Uncategorized"),
                        confidence=item.get("confidence", "Medium")
                    )
                    db.add(finding)
                    db_findings.append(finding)
                    
                    # Prepare for vector storage
                    texts_to_embed.append(item.get("finding", ""))
                    metadatas_to_embed.append({
                        "question_id": q.id,
                        "source_id": s.id,
                        "category": item.get("category", "Uncategorized")
                    })
                    
            except Exception as e:
                print(f"Error extracting findings for source {s.id}: {e}")
                
    db.commit()
    for f in db_findings:
        db.refresh(f)
        
    # Store in FAISS
    if texts_to_embed:
        vector_store.add_texts(texts_to_embed, metadatas_to_embed)
        
    return db_findings
