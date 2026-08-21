from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class ResearchTopic(Base):
    __tablename__ = "research_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending") # pending, processing, completed
    final_report = Column(Text, nullable=True)

    questions = relationship("Question", back_populates="topic_obj")
    sources = relationship("Source", back_populates="topic_obj")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id"))
    question_text = Column(String)

    topic_obj = relationship("ResearchTopic", back_populates="questions")
    findings = relationship("Finding", back_populates="question_obj")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id"))
    title = Column(String)
    url = Column(String)
    content = Column(Text) # Extracted or snippet
    source_name = Column(String)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    topic_obj = relationship("ResearchTopic", back_populates="sources")
    findings = relationship("Finding", back_populates="source_obj")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    finding_text = Column(Text)
    category = Column(String) # Benefits, Risks, etc.
    confidence = Column(String) # High, Medium, Low

    question_obj = relationship("Question", back_populates="findings")
    source_obj = relationship("Source", back_populates="findings")
    
class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id"))
    description = Column(Text)
    reason = Column(Text)
