from __future__ import annotations

import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.extend([
    str(ROOT / "src" / "ml"),
    str(ROOT / "src" / "agent"),
    str(ROOT / "src" / "db"),
    str(ROOT / "src" / "api"),
])

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from schemas import (
    TransactionRequest, BatchTransactionRequest,
    PredictionResponse, BatchPredictionResponse,
    FraudScoreResponse, HealthResponse, MetricsResponse, ErrorResponse,
)
from predictor       import get_predictor
from decision_engine import get_agent
from database        import (
    get_db, get_engine,
    save_transaction, save_fraud_score,
    save_decision, save_prediction_log,
    FraudScoreRecord,
)
from monitoring import get_metrics

app = FastAPI(
    title       = "Real-Time Fraud Detection API",
    description = "ML-powered fraud detection with agentic decision layer",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sanseet.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    get_engine()           
    get_predictor()        
    get_agent()            
    get_metrics()          
    print("✅ Fraud Detection Service started")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())[:8]
    t0 = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - t0) * 1000, 2)
    response.headers["X-Request-ID"]  = request.state.request_id
    response.headers["X-Process-Time"] = f"{elapsed}ms"
    return response


def _run_prediction(payload: TransactionRequest, db: Session) -> PredictionResponse:
    txn_dict   = payload.to_dict()
    txn_id     = payload.transaction_id
    predictor  = get_predictor()
    agent      = get_agent()
    metrics    = get_metrics()
    error_msg  = None

    try:
        fraud_score, latency_ms = predictor.predict(txn_dict)

        result = agent.decide(fraud_score, txn_dict)

        save_transaction(db, txn_id, txn_dict)
        save_fraud_score(
            db, txn_id, fraud_score,
            result.decision, result.confidence, result.processing_ms
        )
        save_decision(db, txn_id, result.to_dict())
        save_prediction_log(
            db, txn_id, txn_dict,
            fraud_score, result.decision, latency_ms
        )

        metrics.record(fraud_score, result.decision, latency_ms)

        return PredictionResponse(
            transaction_id     = txn_id,
            fraud_score        = round(fraud_score, 6),
            decision           = result.decision,
            confidence         = result.confidence,
            reasons            = result.reasons,
            rule_triggers      = result.rule_triggers,
            recommended_action = result.recommended_action,
            processing_ms      = round(latency_ms + result.processing_ms, 3),
            model_version      = result.model_version,
            timestamp          = datetime.utcnow(),
        )

    except Exception as e:
        error_msg = str(e)
        metrics.record(0.0, "ERROR", 0.0, is_error=True)
        save_prediction_log(
            db, txn_id, txn_dict,
            0.0, "ERROR", 0.0, error=error_msg
        )
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = f"Prediction failed: {error_msg}",
        )

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service" : "Real-Time Fraud Detection API",
        "version" : "1.0.0",
        "docs"    : "/docs",
        "health"  : "/health",
        "metrics" : "/metrics",
    }


@app.get(
    "/health",
    response_model = HealthResponse,
    summary        = "System health check",
    tags           = ["System"],
)
async def health_check(db: Session = Depends(get_db)):
    predictor = get_predictor()
    metrics   = get_metrics()
    snap      = metrics.snapshot()

    db_ok = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status         = "healthy" if (predictor._loaded and db_ok) else "degraded",
        model_loaded   = predictor._loaded,
        db_connected   = db_ok,
        uptime_seconds = snap.uptime_seconds,
        version        = "1.0.0",
    )


@app.get(
    "/metrics",
    response_model = MetricsResponse,
    summary        = "Real-time monitoring metrics",
    tags           = ["System"],
)
async def get_monitoring_metrics():
    snap = get_metrics().snapshot()
    return MetricsResponse(**snap.to_dict())



@app.post(
    "/predict",
    response_model = PredictionResponse,
    status_code    = status.HTTP_200_OK,
    summary        = "Predict fraud score for a single transaction",
    tags           = ["Prediction"],
)
async def predict(
    payload : TransactionRequest,
    db      : Session = Depends(get_db),
):
    """
    Analyse a transaction in real time.
    Returns fraud probability score, decision (ALLOW/REVIEW/BLOCK),
    confidence level, reasons, and recommended action.
    """
    return _run_prediction(payload, db)


@app.post(
    "/predict/batch",
    response_model = BatchPredictionResponse,
    status_code    = status.HTTP_200_OK,
    summary        = "Batch fraud scoring (up to 100 transactions)",
    tags           = ["Prediction"],
)
async def predict_batch(
    payload : BatchTransactionRequest,
    db      : Session = Depends(get_db),
):
    t0      = time.time()
    results = []
    for txn in payload.transactions:
        results.append(_run_prediction(txn, db))

    fraud_detected = sum(1 for r in results if r.fraud_score > 0.60)
    blocked        = sum(1 for r in results if r.decision == "BLOCK")
    review         = sum(1 for r in results if r.decision == "REVIEW")
    total_ms       = round((time.time() - t0) * 1000, 2)

    return BatchPredictionResponse(
        results         = results,
        total_processed = len(results),
        fraud_detected  = fraud_detected,
        blocked_count   = blocked,
        review_count    = review,
        total_ms        = total_ms,
    )



@app.get(
    "/fraud-score/{transaction_id}",
    response_model = FraudScoreResponse,
    summary        = "Retrieve fraud score for a past transaction",
    tags           = ["Scores"],
)
async def get_fraud_score(
    transaction_id : str,
    db             : Session = Depends(get_db),
):
    rec = (
        db.query(FraudScoreRecord)
        .filter(FraudScoreRecord.transaction_id == transaction_id)
        .order_by(FraudScoreRecord.created_at.desc())
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail      = f"No score found for transaction_id='{transaction_id}'",
        )
    return FraudScoreResponse(
        transaction_id = rec.transaction_id,
        fraud_score    = rec.fraud_score,
        decision       = rec.decision,
        confidence     = rec.confidence,
        model_version  = rec.model_version,
        created_at     = rec.created_at,
    )


@app.get(
    "/transactions/recent",
    summary = "List recent scored transactions",
    tags    = ["Scores"],
)
async def recent_transactions(
    limit  : int     = 20,
    db     : Session = Depends(get_db),
):
    recs = (
        db.query(FraudScoreRecord)
        .order_by(FraudScoreRecord.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        {
            "transaction_id" : r.transaction_id,
            "fraud_score"    : r.fraud_score,
            "decision"       : r.decision,
            "confidence"     : r.confidence,
            "created_at"     : r.created_at.isoformat(),
        }
        for r in recs
    ]



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code = 500,
        content     = {"error": "Internal server error", "detail": str(exc), "code": 500},
    )
