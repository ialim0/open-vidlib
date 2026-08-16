import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.init_db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gandalab")

# Ensure static/dubs directory exists
os.makedirs("static/dubs", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing GandaLab database...")
    init_db()
    logger.info("GandaLab Video Library API ready.")
    yield
    logger.info("Shutting down GandaLab Video Library API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Open-source interactive STEM video library API with Mistral AI semantic search, PGVector embeddings, RAG Q&A, and Voxtral dubbing.",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files for Dubbed Audio
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/docs")
