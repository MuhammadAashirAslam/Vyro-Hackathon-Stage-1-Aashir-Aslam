"""
Grabpic — Intelligent Identity & Retrieval Engine
FastAPI application entry point.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.routers import ingest, auth, users, upload
from app.models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Grabpic",
    description=(
        "Intelligent Identity & Retrieval Engine for large-scale event photo management. "
        "Uses facial recognition to automatically group images and provides a "
        "Selfie-as-a-Key retrieval system."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(upload.router)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def root():
    """Serve the Grabpic frontend."""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    frontend_path = os.path.abspath(frontend_path)
    if os.path.isfile(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)
