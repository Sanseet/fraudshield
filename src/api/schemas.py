from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

class TransactionRequest(BaseModel):
    transaction_id          : str   = Field(..., examples=["TXN00012345"])
    amount                  : float = Field(..., gt=0, examples=[250.0])
    hour_of_day             : int   = Field(..., ge=0, le=23, examples=[14])
    day_of_week             : int   = Field(..., ge=0, le=6,  examples=[2])
    merchant_category       : str   = Field(..., examples=["retail"])
    country_code            : str   = Field(..., examples=["IN"])
    card_present            : int   = Field(1,   ge=0, le=1)
    transactions_last_1h    : int   = Field(0,   ge=0)
    transactions_last_24h   : int   = Field(0,   ge=0)
    avg_amount_last_7d      : float = Field(0.0, ge=0)
    distance_from_home_km   : float = Field(0.0, ge=0)
    account_age_days        : float = Field(365.0, ge=0)
    failed_attempts_last_24h: int   = Field(0,   ge=0)
    is_international        : int   = Field(0,   ge=0, le=1)
    device_change           : int   = Field(0,   ge=0, le=1)

    @field_validator("merchant_category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"grocery","restaurant","gas","retail","travel","entertainment","healthcare"}
        if v not in allowed:
            raise ValueError(f"merchant_category must be one of {allowed}")
        return v

    @field_validator("country_code")
    @classmethod
    def validate_country(cls, v):
        if len(v) < 2 or len(v) > 3:
            raise ValueError("country_code must be 2-3 characters")
        return v.upper()

    def to_dict(self) -> dict:
        return self.model_dump()


class BatchTransactionRequest(BaseModel):
    transactions: list[TransactionRequest] = Field(..., min_length=1, max_length=100)

class PredictionResponse(BaseModel):
    transaction_id     : str
    fraud_score        : float
    decision           : str
    confidence         : str
    reasons            : list[str]
    rule_triggers      : list[str]
    recommended_action : str
    processing_ms      : float
    model_version      : str
    timestamp          : datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchPredictionResponse(BaseModel):
    results         : list[PredictionResponse]
    total_processed : int
    fraud_detected  : int
    blocked_count   : int
    review_count    : int
    total_ms        : float


class FraudScoreResponse(BaseModel):
    transaction_id : str
    fraud_score    : float
    decision       : str
    confidence     : str
    model_version  : str
    created_at     : datetime

    class Config:
        from_attributes = True
        json_encoders   = {datetime: lambda v: v.isoformat()}


class HealthResponse(BaseModel):
    status          : str
    model_loaded    : bool
    db_connected    : bool
    uptime_seconds  : float
    version         : str


class MetricsResponse(BaseModel):
    total_transactions      : int
    fraud_rate_pct          : float
    avg_fraud_score         : float
    avg_confidence_score    : float
    avg_latency_ms          : float
    p95_latency_ms          : float
    p99_latency_ms          : float
    decision_distribution   : dict[str, Any]
    transactions_last_1min  : int
    transactions_last_5min  : int
    uptime_seconds          : float
    error_count             : int
    error_rate_pct          : float


class ErrorResponse(BaseModel):
    error   : str
    detail  : Optional[str] = None
    code    : int
