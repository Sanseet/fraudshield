"""
Database Layer — SQLite with SQLAlchemy ORM
Stores transactions, fraud scores, decisions, prediction logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, Text, JSON, create_engine, Index,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool

DB_PATH = Path(__file__).parent.parent.parent / "data" / "fraud_detection.db"
DB_URL  = f"sqlite:///{DB_PATH}"


# ─────────────────────────────────────────────────────────
# ORM Base
# ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────
# Tables
# ─────────────────────────────────────────────────────────

class TransactionRecord(Base):
    __tablename__ = "transactions"

    id                      = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id          = Column(String(64), unique=True, nullable=False, index=True)
    amount                  = Column(Float,   nullable=False)
    hour_of_day             = Column(Integer, nullable=False)
    day_of_week             = Column(Integer, nullable=False)
    merchant_category       = Column(String(64))
    country_code            = Column(String(8))
    card_present            = Column(Boolean, default=True)
    transactions_last_1h    = Column(Integer, default=0)
    transactions_last_24h   = Column(Integer, default=0)
    avg_amount_last_7d      = Column(Float,   default=0.0)
    distance_from_home_km   = Column(Float,   default=0.0)
    account_age_days        = Column(Float,   default=0.0)
    failed_attempts_last_24h= Column(Integer, default=0)
    is_international        = Column(Boolean, default=False)
    device_change           = Column(Boolean, default=False)
    created_at              = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_txn_created_at", "created_at"),
    )


class FraudScoreRecord(Base):
    __tablename__ = "fraud_scores"

    id             = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(64), nullable=False, index=True)
    fraud_score    = Column(Float,  nullable=False)
    decision       = Column(String(16), nullable=False)
    confidence     = Column(String(16))
    model_version  = Column(String(32), default="v1.0")
    processing_ms  = Column(Float)
    created_at     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_score_created_at", "created_at"),
        Index("ix_score_decision",   "decision"),
    )


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id                 = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id     = Column(String(64), nullable=False, index=True)
    decision           = Column(String(16), nullable=False)
    fraud_score        = Column(Float)
    confidence         = Column(String(16))
    reasons            = Column(JSON)
    rule_triggers      = Column(JSON)
    recommended_action = Column(Text)
    created_at         = Column(DateTime, default=datetime.utcnow)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id             = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(64), nullable=False, index=True)
    input_features = Column(JSON)
    fraud_score    = Column(Float)
    decision       = Column(String(16))
    latency_ms     = Column(Float)
    error          = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_log_created_at", "created_at"),
    )


# ─────────────────────────────────────────────────────────
# Engine & Session
# ─────────────────────────────────────────────────────────

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            DB_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(_engine)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db() -> Session:
    """FastAPI dependency."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# CRUD helpers
# ─────────────────────────────────────────────────────────

def save_transaction(db: Session, txn_id: str, payload: dict) -> TransactionRecord:
    rec = TransactionRecord(
        transaction_id           = txn_id,
        amount                   = payload.get("amount", 0),
        hour_of_day              = payload.get("hour_of_day", 0),
        day_of_week              = payload.get("day_of_week", 0),
        merchant_category        = payload.get("merchant_category"),
        country_code             = payload.get("country_code"),
        card_present             = bool(payload.get("card_present", True)),
        transactions_last_1h     = payload.get("transactions_last_1h", 0),
        transactions_last_24h    = payload.get("transactions_last_24h", 0),
        avg_amount_last_7d       = payload.get("avg_amount_last_7d", 0),
        distance_from_home_km    = payload.get("distance_from_home_km", 0),
        account_age_days         = payload.get("account_age_days", 0),
        failed_attempts_last_24h = payload.get("failed_attempts_last_24h", 0),
        is_international         = bool(payload.get("is_international", False)),
        device_change            = bool(payload.get("device_change", False)),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def save_fraud_score(db: Session, txn_id: str, score: float,
                     decision: str, confidence: str,
                     processing_ms: float) -> FraudScoreRecord:
    rec = FraudScoreRecord(
        transaction_id = txn_id,
        fraud_score    = score,
        decision       = decision,
        confidence     = confidence,
        processing_ms  = processing_ms,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def save_decision(db: Session, txn_id: str, result: dict) -> DecisionRecord:
    rec = DecisionRecord(
        transaction_id     = txn_id,
        decision           = result["decision"],
        fraud_score        = result["fraud_score"],
        confidence         = result["confidence"],
        reasons            = result.get("reasons", []),
        rule_triggers      = result.get("rule_triggers", []),
        recommended_action = result.get("recommended_action", ""),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def save_prediction_log(db: Session, txn_id: str, features: dict,
                        score: float, decision: str,
                        latency_ms: float, error: str = None) -> PredictionLog:
    rec = PredictionLog(
        transaction_id = txn_id,
        input_features = features,
        fraud_score    = score,
        decision       = decision,
        latency_ms     = latency_ms,
        error          = error,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# ─────────────────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = get_engine()
    tables = Base.metadata.tables.keys()
    print("✅ Database initialized")
    print(f"   Tables: {list(tables)}")
    print(f"   Path  : {DB_PATH}")
