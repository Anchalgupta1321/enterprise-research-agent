import json
import math
from langchain_core.prompts import PromptTemplate
from backend.core.llm import get_llm
from backend.models import domain
from sqlalchemy.orm import Session
from backend.core.utils import robust_invoke
from typing import Dict, Any, List

def extract_knowledge_graph(topic: domain.ResearchTopic, findings: List[domain.Finding], report: str, db: Session) -> Dict[str, Any]:
    """Entity-Relationship & Knowledge Graph Extraction Agent.
    Parses findings and synthesized report into an entity-relationship network
    with classified nodes (Technologies, Entities, Regulations, Risks, Outcomes)
    and semantic directed edges with spatial coordinates for interactive 2D visualization.
    """
    llm = get_llm()

    findings_summary = []
    for f in findings[:25]:
        findings_summary.append(f"- [{f.category}] {f.finding_text}")
    findings_text = "\n".join(findings_summary) if findings_summary else "No findings."

    kg_prompt = PromptTemplate.from_template(
        """You are an elite Knowledge Graph & Semantic Entity Extraction Agent.
Analyze the strategic research findings below and construct a connected Knowledge Graph network for the topic.

Topic: {topic}

### REPORT DRAFT:
{report}

### RAW FINDINGS:
{findings}

### EXTRACTION INSTRUCTIONS:
1. Extract 7 to 10 distinct entities (Nodes).
   Categorize each entity into one of: 'Technology', 'Organization', 'Regulation', 'Risk', 'Market Driver'.
2. Extract 8 to 14 semantic relationship links (Edges) connecting pairs of nodes.
   Relationship verbs should be concise (e.g., 'enables', 'regulates', 'competes_with', 'accelerates', 'mitigates', 'threatens').
3. Include the root topic entity as the central hub node.

Respond ONLY with a valid JSON object in this exact schema:
{{
  "nodes": [
    {{"id": "node_0", "label": "{topic}", "category": "Technology", "size": 35, "description": "Core subject of investigation"}},
    {{"id": "node_1", "label": "Enterprise Adoption", "category": "Market Driver", "size": 22, "description": "Key commercial growth catalyst"}},
    {{"id": "node_2", "label": "Compliance & Security", "category": "Regulation", "size": 22, "description": "Mandatory governance standards"}},
    {{"id": "node_3", "label": "Latency Bottlenecks", "category": "Risk", "size": 20, "description": "Core infrastructure friction point"}}
  ],
  "edges": [
    {{"source": "node_0", "target": "node_1", "relation": "drives", "weight": 2}},
    {{"source": "node_2", "target": "node_0", "relation": "governs", "weight": 1.5}},
    {{"source": "node_0", "target": "node_3", "relation": "exposes", "weight": 1.2}}
  ]
}}
"""
    )

    prompt_val = kg_prompt.invoke({
        "topic": topic.topic,
        "report": report[:3500],
        "findings": findings_text
    })

    try:
        from backend.core.utils import parse_json_from_llm
        response = robust_invoke(llm, prompt_val)
        kg_data = parse_json_from_llm(response)
        
        # Calculate layout positions if not present
        nodes = kg_data.get("nodes", [])
        n_nodes = len(nodes)
        for i, node in enumerate(nodes):
            if i == 0:
                node["x"] = 0.0
                node["y"] = 0.0
            else:
                angle = (2 * math.pi * (i - 1)) / max(1, (n_nodes - 1))
                radius = 2.0 + (0.5 if i % 2 == 0 else -0.3)
                node["x"] = round(radius * math.cos(angle), 2)
                node["y"] = round(radius * math.sin(angle), 2)

        payload_str = json.dumps(kg_data)
        topic.knowledge_graph_data = payload_str
        db.commit()
        return kg_data
    except Exception as e:
        print(f"Knowledge graph generation fallback triggered: {e}")
        fallback_graph = {
            "nodes": [
                {"id": "node_0", "label": topic.topic[:30], "category": "Technology", "size": 35, "description": "Core research focal entity", "x": 0.0, "y": 0.0},
                {"id": "node_1", "label": "Enterprise Market", "category": "Market Driver", "size": 22, "description": "Commercial application vector", "x": 2.2, "y": 0.0},
                {"id": "node_2", "label": "Regulatory Standards", "category": "Regulation", "size": 22, "description": "Global compliance framework", "x": 1.1, "y": 1.9},
                {"id": "node_3", "label": "Engineering Feasibility", "category": "Technology", "size": 22, "description": "Technical scalability factors", "x": -1.1, "y": 1.9},
                {"id": "node_4", "label": "Infrastructure Risk", "category": "Risk", "size": 20, "description": "Operational and cost risks", "x": -2.2, "y": 0.0},
                {"id": "node_5", "label": "Ecosystem Partners", "category": "Organization", "size": 22, "description": "Key industry consortia", "x": 0.0, "y": -2.2}
            ],
            "edges": [
                {"source": "node_0", "target": "node_1", "relation": "accelerates", "weight": 2.0},
                {"source": "node_2", "target": "node_0", "relation": "regulates", "weight": 1.5},
                {"source": "node_0", "target": "node_3", "relation": "validates", "weight": 1.8},
                {"source": "node_4", "target": "node_0", "relation": "challenges", "weight": 1.3},
                {"source": "node_5", "target": "node_0", "relation": "integrates_with", "weight": 1.6}
            ]
        }
        topic.knowledge_graph_data = json.dumps(fallback_graph)
        db.commit()
        return fallback_graph
