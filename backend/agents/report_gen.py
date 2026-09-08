from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session
from backend.core.utils import robust_invoke

def generate_report(topic: domain.ResearchTopic, questions: list[domain.Question], findings: list[domain.Finding], contradictions: list[domain.Contradiction], db: Session) -> str:
    """Compiles the final traceable research report using a Multi-Agent Debate."""
    llm = get_llm()
    
    # Format the input data
    q_text = "\n".join([f"- {q.question_text}" for q in questions])
    
    f_text = ""
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
            f_text += f"- [SRC-{item.id}] {item.finding_text} [Source]({source_url})\n"
            
    c_text = ""
    if contradictions:
        for c in contradictions:
            c_text += f"- **Conflict:** {c.description}\n  *Details:* {c.reason}\n"
    else:
        c_text = "No major contradictions detected across sources."
        
    # 1. Optimist Agent
    optimist_prompt = PromptTemplate.from_template(
        """You are an optimistic research analyst.
Analyze the following findings for the topic: {topic}
Focus strictly on the positive potential, opportunities, benefits, and best-case scenarios.
Cite your claims using the [SRC-X] tags provided.

Findings:
{findings}

Optimistic Analysis:"""
    )
    optimist_chain = optimist_prompt | llm
    
    # 2. Skeptic Agent
    skeptic_prompt = PromptTemplate.from_template(
        """You are a skeptical, highly critical research analyst.
Analyze the following findings for the topic: {topic}
Focus strictly on the risks, limitations, downsides, potential failures, and worst-case scenarios.
Cite your claims using the [SRC-X] tags provided.

Findings:
{findings}

Skeptical Analysis:"""
    )
    skeptic_chain = skeptic_prompt | llm

    # 3. Judge Agent
    judge_prompt = PromptTemplate.from_template(
        """You are an expert enterprise research AI, acting as the final judge.
Synthesize a highly balanced, nuanced research report based on the original findings, and the debate between the Optimist and the Skeptic.

Topic: {topic}

Research Questions Addressed:
{questions}

Original Categorized Findings:
{findings}

Contradictions/Conflicts Found:
{contradictions}

Optimist's View:
{optimist_view}

Skeptic's View:
{skeptic_view}

Format the report beautifully using Markdown. Include the following sections:
1. Executive Summary
2. Key Findings (synthesize the raw findings)
3. Balanced Perspectives (synthesize the Optimist vs. Skeptic debate)
4. Strategic Conclusion
5. References (A numbered list of the sources linked in the text)

Ensure all claims in the report STRICTLY cite the exact [SRC-X] tag provided in the findings list (e.g., [SRC-1], [SRC-23]). Do NOT use generic [1] citations.
Do not invent information. Rely solely on the provided inputs.
"""
    )
    judge_chain = judge_prompt | llm
    
    try:
        print("Running Optimist Agent...")
        opt_res = robust_invoke(optimist_chain, {"topic": topic.topic, "findings": f_text})
        optimist_view = opt_res.content if hasattr(opt_res, 'content') else str(opt_res)
        
        print("Running Skeptic Agent...")
        skp_res = robust_invoke(skeptic_chain, {"topic": topic.topic, "findings": f_text})
        skeptic_view = skp_res.content if hasattr(skp_res, 'content') else str(skp_res)
        
        print("Running Judge Agent...")
        final_res = robust_invoke(judge_chain, {
            "topic": topic.topic,
            "questions": q_text,
            "findings": f_text,
            "contradictions": c_text,
            "optimist_view": optimist_view,
            "skeptic_view": skeptic_view
        })
        
        report_content = final_res.content
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
