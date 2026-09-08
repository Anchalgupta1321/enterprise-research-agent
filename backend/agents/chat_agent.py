from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from backend.core.utils import robust_invoke
from typing import List, Dict, Any

def generate_chat_reply(topic: domain.ResearchTopic, user_message: str, history: List[Dict[str, Any]]) -> str:
    """Answers user follow-up questions grounded strictly in the research report, findings, and verified sources."""
    llm = get_llm()
    
    # Format chat history (keep last 6 turns for context)
    history_lines = []
    for msg in history[-6:]:
        role = "User" if msg.get("role") == "user" else "AI Assistant"
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")
    history_text = "\n".join(history_lines) if history_lines else "No previous conversation."

    # Format findings/sources summary
    findings_summary = []
    if topic.findings:
        for f in topic.findings[:25]:
            source_url = f.source_obj.url if f.source_obj else "N/A"
            findings_summary.append(f"- [SRC-{f.id}] ({f.category}) {f.finding_text} [Source: {source_url}]")
    findings_text = "\n".join(findings_summary) if findings_summary else "No additional raw findings."

    report_text = topic.final_report or "No final report generated yet."

    chat_prompt = PromptTemplate.from_template(
        """You are an elite AI Research Assistant specializing in enterprise intelligence for the topic: "{topic}".
You are answering follow-up questions from an executive or researcher about this specific research report and its findings.

### EXECUTIVE RESEARCH REPORT:
{report}

### KEY RESEARCH FINDINGS & SOURCES:
{findings}

### CONVERSATION HISTORY:
{history}

### USER'S NEW QUESTION:
{user_message}

### INSTRUCTIONS:
- Answer the user's question accurately, concisely, and professionally using ONLY the provided research report, findings, and context.
- When referencing specific facts or claims, cite the relevant sources using markdown links or [SRC-X] citations where applicable.
- If the answer cannot be determined from the research report or findings, politely explain that the current research scope doesn't cover it and suggest a relevant sub-topic.
- Keep the response clear, structured, and insightful.

Response:"""
    )

    chat_chain = chat_prompt | llm
    
    try:
        res = robust_invoke(chat_chain, {
            "topic": topic.topic,
            "report": report_text,
            "findings": findings_text,
            "history": history_text,
            "user_message": user_message
        })
        content = res.content if hasattr(res, 'content') else str(res)
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
            return "".join(text_parts).strip()
        return str(content).strip()
    except Exception as e:
        print(f"Error in chat agent: {e}")
        return f"I encountered an issue processing your question: {str(e)}"
