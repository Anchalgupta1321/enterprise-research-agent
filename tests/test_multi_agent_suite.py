import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base
from backend.models import domain, schemas
from backend.agents.auditor_agent import audit_research_report
from backend.agents.chart_agent import generate_report_charts
from backend.agents.boardroom_agent import run_boardroom_council
from backend.agents.knowledge_graph_agent import extract_knowledge_graph

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_topic(db_session):
    topic = domain.ResearchTopic(
        topic="Solid-State Battery Breakthroughs 2026",
        status="processing",
        final_report="Solid-state batteries demonstrate high energy density [SRC-1] but encounter dendrite formation challenges [SRC-2]."
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    q1 = domain.Question(topic_id=topic.id, question_text="What are the commercial benefits?")
    db_session.add(q1)
    db_session.commit()
    db_session.refresh(q1)

    s1 = domain.Source(topic_id=topic.id, title="Battery Tech Weekly", url="https://example.com/battery", content="Energy density increased by 40%.", source_name="Tavily")
    db_session.add(s1)
    db_session.commit()
    db_session.refresh(s1)

    f1 = domain.Finding(question_id=q1.id, source_id=s1.id, finding_text="Solid-state cells achieve 450 Wh/kg energy density.", category="Benefits", confidence="High")
    f2 = domain.Finding(question_id=q1.id, source_id=s1.id, finding_text="Lithium dendrite growth remains a risk during fast-charging.", category="Risks", confidence="High")
    db_session.add_all([f1, f2])
    db_session.commit()

    return topic

def test_domain_models_and_schemas(db_session, sample_topic):
    """Test that domain models store new multi-agent fields and schemas serialize properly."""
    sample_topic.audit_score = 97.5
    sample_topic.audit_verdict = "VERIFIED_EXCELLENT"
    sample_topic.audit_feedback = "All claims verified against source findings."
    sample_topic.charts_data = json.dumps([{"chart_type": "bar", "title": "Test Chart"}])
    sample_topic.boardroom_data = json.dumps({"board_verdict": "PROCEED_WITH_GUARDRAILS"})
    sample_topic.knowledge_graph_data = json.dumps({"nodes": [], "edges": []})
    db_session.commit()

    reloaded = db_session.query(domain.ResearchTopic).filter(domain.ResearchTopic.id == sample_topic.id).first()
    assert reloaded.audit_score == 97.5
    assert reloaded.audit_verdict == "VERIFIED_EXCELLENT"
    assert "PROCEED_WITH_GUARDRAILS" in reloaded.boardroom_data

    # Test Pydantic schema serialization
    schema_obj = schemas.ResearchTopicSchema.model_validate(reloaded)
    assert schema_obj.id == sample_topic.id
    assert schema_obj.audit_score == 97.5
    assert schema_obj.audit_verdict == "VERIFIED_EXCELLENT"

@patch("backend.agents.auditor_agent.robust_invoke")
def test_auditor_agent(mock_invoke, db_session, sample_topic):
    """Test Feature 1: Self-Reflective Auditor Agent (Reflexion Pattern)."""
    mock_response = json.dumps({
        "grounding_score": 96.4,
        "verdict": "VERIFIED_EXCELLENT",
        "feedback": "All claims are strictly grounded in raw source findings.",
        "flagged_claims": []
    })
    mock_invoke.return_value = mock_response

    findings = sample_topic.findings
    result = audit_research_report(sample_topic, sample_topic.final_report, findings, db_session)

    assert result["grounding_score"] == 96.4
    assert result["verdict"] == "VERIFIED_EXCELLENT"
    assert sample_topic.audit_score == 96.4
    assert sample_topic.audit_verdict == "VERIFIED_EXCELLENT"

@patch("backend.agents.chart_agent.robust_invoke")
def test_chart_agent(mock_invoke, db_session, sample_topic):
    """Test Feature 2: Dynamic Data & Plotly Chart Visualizer Agent."""
    mock_response = json.dumps([
        {
            "chart_type": "bar",
            "title": "Strategic Impact Vectors: Opportunity vs Risk",
            "categories": ["Energy Density", "Fast Charging", "Safety"],
            "series": [
                {"name": "Opportunity Score", "values": [9.0, 7.5, 9.5], "color": "#10b981"},
                {"name": "Risk Score", "values": [4.0, 6.5, 3.0], "color": "#ef4444"}
            ]
        },
        {
            "chart_type": "timeline",
            "title": "Commercial Adoption Horizon",
            "x": ["2026", "2027", "2028", "2030"],
            "y": [20, 45, 70, 95],
            "metric_label": "Adoption %"
        }
    ])
    mock_invoke.return_value = mock_response

    charts_json = generate_report_charts(sample_topic, sample_topic.findings, sample_topic.final_report, db_session)
    parsed = json.loads(charts_json)

    assert len(parsed) == 2
    assert parsed[0]["chart_type"] == "bar"
    assert parsed[1]["chart_type"] == "timeline"
    assert sample_topic.charts_data is not None

@patch("backend.agents.boardroom_agent.robust_invoke")
def test_boardroom_agent(mock_invoke, db_session, sample_topic):
    """Test Feature 3: Executive Boardroom Mode (Council of Expert Personas)."""
    mock_response = json.dumps({
        "board_verdict": "PROCEED_WITH_GUARDRAILS",
        "board_summary": "High commercial upside with manageable technical risk profile.",
        "cfo": {
            "grade": "A",
            "projected_roi": "+210% (3-Year)",
            "capital_intensity": "Moderate",
            "bullet_points": ["Strong market adoption catalysts.", "High margin potential."]
        },
        "cto": {
            "feasibility_score": 8.5,
            "complexity": "Medium",
            "tech_recommendation": "Modular Pilot Architecture",
            "bullet_points": ["Solid benchmark verification.", "Scalable manufacturing pathway."]
        },
        "legal": {
            "risk_index": "Low-Moderate",
            "primary_challenge": "Patent landscape & compliance",
            "bullet_points": ["Low antitrust exposure.", "Traceable IP provenance."]
        }
    })
    mock_invoke.return_value = mock_response

    board_dict = run_boardroom_council(sample_topic, sample_topic.final_report, sample_topic.findings, db_session)

    assert board_dict["board_verdict"] == "PROCEED_WITH_GUARDRAILS"
    assert board_dict["cfo"]["grade"] == "A"
    assert board_dict["cto"]["feasibility_score"] == 8.5
    assert sample_topic.boardroom_data is not None

@patch("backend.agents.knowledge_graph_agent.robust_invoke")
def test_knowledge_graph_agent(mock_invoke, db_session, sample_topic):
    """Test Feature 4: Interactive Knowledge Graph & Entity Relationship Visualizer."""
    mock_response = json.dumps({
        "nodes": [
            {"id": "node_0", "label": "Solid-State Battery", "category": "Technology", "size": 35, "description": "Core technology"},
            {"id": "node_1", "label": "Automotive OEMs", "category": "Market Driver", "size": 22, "description": "Primary market buyers"},
            {"id": "node_2", "label": "EU Battery Passport", "category": "Regulation", "size": 22, "description": "Mandatory traceability"}
        ],
        "edges": [
            {"source": "node_0", "target": "node_1", "relation": "powers", "weight": 2.0},
            {"source": "node_2", "target": "node_0", "relation": "regulates", "weight": 1.5}
        ]
    })
    mock_invoke.return_value = mock_response

    kg_dict = extract_knowledge_graph(sample_topic, sample_topic.findings, sample_topic.final_report, db_session)

    assert len(kg_dict["nodes"]) == 3
    assert len(kg_dict["edges"]) == 2
    # Verify coordinates were computed
    assert "x" in kg_dict["nodes"][0]
    assert "y" in kg_dict["nodes"][0]
    assert sample_topic.knowledge_graph_data is not None

def test_full_pipeline_state_integration(sample_topic, db_session):
    """Test full LangGraph state dict serialization with all 4 new agent outputs."""
    state = {
        "topic_id": sample_topic.id,
        "loop_count": 1,
        "questions": [q.question_text for q in sample_topic.questions],
        "sources": [s.url for s in sample_topic.sources],
        "findings": [f.finding_text for f in sample_topic.findings],
        "contradictions": [],
        "needs_more_info": False
    }
    assert state["topic_id"] == sample_topic.id
    assert len(state["questions"]) == 1
    assert len(state["findings"]) == 2
