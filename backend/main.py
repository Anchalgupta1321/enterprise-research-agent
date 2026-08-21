from fastapi import FastAPI
from backend.core.database import Base, engine
from backend.api import routes

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise AI Research Agent",
    description="API for conducting structured enterprise research at scale.",
    version="1.0.0"
)

app.include_router(routes.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
