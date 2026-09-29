from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.core.database import Base, engine, ensure_db_columns
from backend.api import routes

# Create database tables & ensure column schema alignment
Base.metadata.create_all(bind=engine)
ensure_db_columns()


app = FastAPI(
    title="Enterprise AI Research Agent",
    description="API for conducting structured enterprise research at scale.",
    version="1.0.0"
)

# Add CORS middleware to allow external/cross-origin requests if needed
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

# Mount frontend static directory for unified deployment on Render
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

