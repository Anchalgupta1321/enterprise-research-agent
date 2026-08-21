from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session

def generate_report(topic: domain.ResearchTopic, questions: list[domain.Question], findings: list[domain.Finding], contradictions: list[domain.Contradiction], db: Session) -> str:
    """Compiles the final traceable research report."""
    llm = get_llm()
    
    # Format the input data
    q_text = "\n".join([f"- {q.question_text}" for q in questions])
    
    f_text = ""
    # Group findings by category
    categories = {}
    for f in findings:
        cat = f.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)
        
    for cat, items in categories.items():
        f_text += f"\n### {cat}\n"
        for item in items:
            source_url = item.source_obj.url if item.source_obj else "Unknown"
            f_text += f"- {item.finding_text} [Source]({source_url})\n"
            
    c_text = ""
    if contradictions:
        for c in contradictions:
            c_text += f"- **Conflict:** {c.description}\n  *Details:* {c.reason}\n"
    else:
        c_text = "No major contradictions detected across sources."
        
    prompt = PromptTemplate.from_template(
        """You are an expert enterprise research AI.
Generate a comprehensive, professional research report based on the gathered findings.

Topic: {topic}

Research Questions Addressed:
{questions}

Categorized Findings:
{findings}

Contradictions/Conflicts Found:
{contradictions}

Format the report beautifully using Markdown. Include the following sections:
1. Executive Summary
2. Key Findings (synthesize the categorized findings)
3. Discrepancies and Contradictions
4. Strategic Conclusion
5. References (A numbered list of the sources linked in the text)

Ensure all claims in the Key Findings and Conclusion cite the original source URLs provided in the findings list (e.g. using inline links like [1], [2]).
Do not invent information. Rely solely on the provided findings.
"""
    )
    
    chain = prompt | llm
    
    try:
        from backend.core.utils import robust_invoke
        response = robust_invoke(chain, {
            "topic": topic.topic,
            "questions": q_text,
            "findings": f_text,
            "contradictions": c_text
        })
        
        report_content = response.content
        if isinstance(report_content, list):
            text_parts = []
            for block in report_content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
            report = "".join(text_parts).strip()
        else:
            report = str(report_content).strip()
            
        topic.final_report = report
        db.commit()
        return report
    except Exception as e:
        print(f"Error generating report: {e}")
        return "Error generating the final report."
