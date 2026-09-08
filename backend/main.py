from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import Base, engine
from backend.api import routes

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise AI Research Agent",
    description="API for conducting structured enterprise research at scale.",
    version="1.0.0"
)

# Add CORS middleware to allow Streamlit Cloud to connect to Render API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
