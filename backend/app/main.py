"""
FastAPI application entrypoint — Legal Intelligence Platform (Phase 1).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import upload, analyze, ask, report, compare, compliance, risk_analysis, download

logging.basicConfig(
    level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Intelligence Platform API",
    description="Enterprise-grade Multi-Agent Legal Intelligence Platform (Phase 2) — "
                 "LangGraph + FastAPI + PostgreSQL/pgvector + Groq Llama 3.3. "
                 "Adds Document Intelligence, Compliance, Red Flag Detection, and "
                 "Contract Comparison agents on top of the original Phase 1 pipeline.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(ask.router)
app.include_router(report.router)
app.include_router(compare.router)
app.include_router(compliance.router)
app.include_router(risk_analysis.router)
app.include_router(download.router)


@app.on_event("startup")
def on_startup():
    # Tables are also created via database/schema.sql (recommended for pgvector
    # index creation), but this ensures ORM/DB stay in sync in dev environments.
    Base.metadata.create_all(bind=engine)
    logger.info("Legal Intelligence Platform API started (env=%s)", settings.app_env)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "legal-intelligence-platform", "phase": 2}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
