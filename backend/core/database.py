"""AURA-EAGLE — Database Layer (PostgreSQL + SQLAlchemy async)"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, JSON, DateTime, Text, Integer, Boolean
from sqlalchemy import text
from datetime import datetime
from typing import AsyncGenerator
import os
import structlog

log = structlog.get_logger()


class Base(DeclarativeBase):
    pass


# ── ORM Models ────────────────────────────────────────────────────────────────

class MemoryRecord(Base):
    __tablename__ = "memory_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    layer: Mapped[str] = mapped_column(String(32))          # sensory/working/semantic/episodic/causal
    content: Mapped[dict] = mapped_column(JSON)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity: Mapped[str] = mapped_column(String(256))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(64))
    relation: Mapped[str] = mapped_column(String(128))
    probability: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DecisionRecord(Base):
    __tablename__ = "decisions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[str] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    risk: Mapped[float] = mapped_column(Float)
    ethical_score: Mapped[float] = mapped_column(Float)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    conclusion: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentActivityRecord(Base):
    __tablename__ = "agent_activity"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(128))
    metric_value: Mapped[float] = mapped_column(Float)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Engine Setup ──────────────────────────────────────────────────────────────

def _build_async_url(url: str) -> str:
    """Convert postgres:// → postgresql+asyncpg://, strip unsupported params."""
    if not url:
        return ""
    # Swap scheme
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    # asyncpg handles SSL natively via connect_args; strip query params that
    # the DBAPI layer doesn't understand (e.g. sslmode from Replit's URL).
    if "?" in url:
        base, qs = url.split("?", 1)
        # Keep nothing — asyncpg uses connect_args for SSL
        url = base
    return url


_raw_url = os.environ.get("DATABASE_URL", "")
_db_url = _build_async_url(_raw_url)
_ssl_required = "sslmode=require" in _raw_url or "sslmode=prefer" in _raw_url

engine = None
AsyncSessionLocal = None

if _db_url:
    _connect_args: dict = {}
    if _ssl_required:
        import ssl as _ssl
        _ctx = _ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = _ssl.CERT_NONE
        _connect_args["ssl"] = _ctx

    engine = create_async_engine(
        _db_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        connect_args=_connect_args,
    )
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    if engine is None:
        log.warning("database.no_url", msg="DATABASE_URL not set — running without persistence")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database.initialized")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
