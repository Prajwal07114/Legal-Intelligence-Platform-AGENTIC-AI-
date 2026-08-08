"""
ORM models for the Legal Intelligence Platform.
Mirrors database/schema.sql — kept in sync manually since Phase 1
uses raw SQL migrations rather than Alembic (documented in README).
"""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import settings


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, default=dict)

    documents = relationship("LegalDocument", back_populates="session")
    reports = relationship("Report", back_populates="session")


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(50), default="pdf")
    page_count = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
    status = Column(String(50), default="uploaded")  # uploaded | processing | processed | failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UserSession", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    embedding = Column(Vector(settings.embedding_dim), nullable=True)

    document = relationship("LegalDocument", back_populates="chunks")


class Citation(Base):
    """Reference-corpus entries (statutes, regulations, standard clause library)
    that the Research Agent retrieves against, independent of user-uploaded docs."""
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(512), nullable=False)   # e.g. "Indian Contract Act, 1872 - Sec 73"
    source_type = Column(String(100), default="statute")  # statute | regulation | clause_reference | case_law
    content = Column(Text, nullable=False)
    url = Column(String(1024), nullable=True)
    embedding = Column(Vector(settings.embedding_dim), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=True)
    user_query = Column(Text, nullable=False)
    task_type = Column(String(100), nullable=True)
    report_markdown = Column(Text, nullable=False)
    report_json = Column(JSON, nullable=True)  # structured payload for the frontend
    risk_level = Column(String(50), nullable=True)
    workflow_mode = Column(String(20), default="single")  # Phase 2: "single" | "comparison"
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("UserSession", back_populates="reports")
    document = relationship("LegalDocument", back_populates="reports")


# =========================================================
# Phase 2 models
# =========================================================

class ComplianceResult(Base):
    """Output of Agent 7 — Compliance Agent."""
    __tablename__ = "compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    compliance_score = Column(Integer, default=0)
    missing_clauses = Column(JSON, default=list)
    compliance_issues = Column(JSON, default=list)  # each issue includes its evidence[]
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskFlagResult(Base):
    """Output of Agent 8 — Red Flag Detection Agent."""
    __tablename__ = "risk_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    flags = Column(JSON, default=list)  # list of {flag_type, severity, explanation, evidence[]}
    severity = Column(String(50), default="Low")
    created_at = Column(DateTime, default=datetime.utcnow)


class ComparisonResult(Base):
    """Output of Agent 9 — Contract Comparison Agent."""
    __tablename__ = "comparison_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    document_id_a = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=True)
    document_id_b = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    added_clauses = Column(JSON, default=list)
    removed_clauses = Column(JSON, default=list)
    modified_clauses = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
