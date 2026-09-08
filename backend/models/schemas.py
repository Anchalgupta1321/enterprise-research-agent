from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class QuestionBase(BaseModel):
    question_text: str

class QuestionSchema(QuestionBase):
    id: int
    topic_id: int
    model_config = ConfigDict(from_attributes=True)

class SourceBase(BaseModel):
    title: str
    url: str
    content: str
    source_name: str

class SourceSchema(SourceBase):
    id: int
    topic_id: int
    retrieved_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FindingBase(BaseModel):
    finding_text: str
    category: str
    confidence: str

class FindingSchema(FindingBase):
    id: int
    question_id: int
    source_id: int
    model_config = ConfigDict(from_attributes=True)
    
class ContradictionBase(BaseModel):
    description: str
    reason: str

class ContradictionSchema(ContradictionBase):
    id: int
    topic_id: int
    model_config = ConfigDict(from_attributes=True)

class AgentLogBase(BaseModel):
    message: str

class AgentLogSchema(AgentLogBase):
    id: int
    topic_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class ResearchTopicBase(BaseModel):
    topic: str

class ResearchTopicSchema(ResearchTopicBase):
    id: int
    created_at: datetime
    status: str
    final_report: Optional[str] = None
    audit_score: Optional[float] = None
    audit_verdict: Optional[str] = None
    audit_feedback: Optional[str] = None
    charts_data: Optional[str] = None
    boardroom_data: Optional[str] = None
    knowledge_graph_data: Optional[str] = None
    questions: List[QuestionSchema] = []
    sources: List[SourceSchema] = []
    findings: List[FindingSchema] = []
    logs: List[AgentLogSchema] = []
    model_config = ConfigDict(from_attributes=True)

class ResearchRequest(BaseModel):
    topic: str

class ApproveRequest(BaseModel):
    questions: List[str]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
