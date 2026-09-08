from tavily import TavilyClient
from backend.core.config import settings
from backend.models import domain
from sqlalchemy.orm import Session
from backend.services.vector_store import vector_store

def search_for_questions(topic: domain.ResearchTopic, questions: list[domain.Question], db: Session) -> list[domain.Source]:
    """Searches the web for answers to the generated questions using Tavily."""
    if not settings.TAVILY_API_KEY or settings.TAVILY_API_KEY == "your_tavily_api_key_here":
        print("Tavily API key not set. Skipping search.")
        return []
        
    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    
    db_sources = []
    seen_urls = set()
    
    for q in questions:
        try:
            # Perform search using Tavily API
            # For deeper research, we use search_depth="advanced"
            response = client.search(query=q.question_text, search_depth="basic", max_results=2)
            
            for result in response.get("results", []):
                url = result.get("url")
                if url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                source = domain.Source(
                    topic_id=topic.id,
                    title=result.get("title", "Unknown Title"),
                    url=url,
                    content=result.get("content", ""),
                    source_name=result.get("raw_content", "")[:50] if result.get("raw_content") else "Web Search"
                )
                db.add(source)
                db_sources.append(source)
                
        except Exception as e:
            print(f"Error searching web for question '{q.question_text}': {e}")
            
        try:
            faiss_results = vector_store.similarity_search(q.question_text, k=2)
            for res in faiss_results:
                meta = res.get("metadata", {})
                source = domain.Source(
                    topic_id=topic.id,
                    title=f"Local Document: {meta.get('source', 'Unknown')}",
                    url=f"local://{meta.get('source', 'unknown')}",
                    content=meta.get("content", ""),
                    source_name="Private Knowledge Base"
                )
                db.add(source)
                db_sources.append(source)
        except Exception as e:
            print(f"Error searching FAISS for question '{q.question_text}': {e}")
            
    db.commit()
    for s in db_sources:
        db.refresh(s)
        
    return db_sources
