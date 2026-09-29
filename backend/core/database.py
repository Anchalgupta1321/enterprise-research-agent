from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# Create engine, setting check_same_thread=False for SQLite
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def ensure_db_columns():
    """Migrate missing columns automatically for SQLite database."""
    try:
        inspector = inspect(engine)
        if "research_topics" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("research_topics")]
            with engine.connect() as conn:
                for col_name, col_type in [
                    ("audit_score", "FLOAT"),
                    ("audit_verdict", "VARCHAR"),
                    ("audit_feedback", "TEXT"),
                    ("charts_data", "TEXT"),
                    ("boardroom_data", "TEXT"),
                    ("knowledge_graph_data", "TEXT"),
                ]:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE research_topics ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        print(f"[DB Migration Note] {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

