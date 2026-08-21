import traceback
from backend.core.database import SessionLocal
from backend.models import domain
from backend.agents.question_gen import generate_questions

db = SessionLocal()
topic = db.query(domain.ResearchTopic).order_by(domain.ResearchTopic.id.desc()).first()

print(f"Topic: {topic.topic}")
try:
    questions = generate_questions(topic, db)
    print("Questions:", questions)
except Exception as e:
    traceback.print_exc()
