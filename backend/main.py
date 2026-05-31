from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from api.routes import router as api_router
from api.collaboration_routes import router as collab_router
from api.auth_routes import router as auth_router
from databases.models import init_db

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="DataChat API",
    description="Talk to your database with natural language",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router)
app.include_router(collab_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "DataChat API Running",
        "version": "1.0.0",
        "status": "healthy",
        "features": [
            "Multi-agent system (SQL, validation, insights)",
            "Data profiling on upload",
            "Context-aware follow-up questions",
            "Custom dashboards",
            "Scheduled reports",
            "Team collaboration",
            "CSV/PDF export",
            "PostgreSQL/MySQL/SQLite support",
            "Advanced visualizations"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DataChat API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )