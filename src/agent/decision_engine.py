"""
Agentic Decision Layer
Converts ML fraud scores into business actions using rule-based + ML logic.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional
import numpy as np

META_PATH = Path(__file__).parent.parent.parent / "models" / "model_meta.json"

# ─────────────────────────────────────────────────────────
# Decision Categories
# ─────────────────────────────────────────────────────────

class Decision(str, Enum):
    ALLOW  = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK  = "BLOCK"


@dataclass
class DecisionResult:
    decision        : str
    fraud_score     : float
    confidence      : str          # HIGH / MEDIUM / LOW
    reasons         : list[str]
    rule_triggers   : list[str]
    recommended_action: str
    processing_ms   : float
    model_version   : str = "v1.0"

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# Risk Thresholds
# ─────────────────────────────────────────────────────────

@dataclass
class RiskThresholds:
    allow_below  : float = 0.30   # score < 0.30 → ALLOW
    review_above : float = 0.30   # score >= 0.30 → REVIEW
    block_above  : float = 0.60   # score >= 0.60 → BLOCK

    # Hard-rule overrides
    max_amount_auto_block  : float = 10_000
    max_velocity_1h_block  : int   = 8
    max_failed_attempts    : int   = 3
    max_distance_km        : float = 500


# ─────────────────────────────────────────────────────────
# Agentic Decision Engine
# ─────────────────────────────────────────────────────────

class FraudDecisionAgent:
    """
    Multi-signal decision engine.

    Decision logic (in priority order):
    1. Hard-coded override rules (extreme signals)
    2. ML score thresholds
    3. Contextual risk modifiers
    """

    def __init__(self, thresholds: Optional[RiskThresholds] = None):
        self._custom_thresholds = thresholds
        self.thresholds = thresholds or RiskThresholds()
        self.model_version = "v1.0"
        if thresholds is None:
            self._load_meta()

    def _load_meta(self):
        if META_PATH.exists():
            with open(META_PATH) as f:
                meta = json.load(f)
            t = meta.get("thresholds", {})
            self.thresholds.allow_below  = t.get("allow",  0.30)
            self.thresholds.block_above  = t.get("block",  0.60)
            self.thresholds.review_above = t.get("review", 0.30)

    # ── Public API ────────────────────────────────────────
    def decide(self, fraud_score: float, transaction: dict) -> DecisionResult:
        t0 = time.time()

        reasons       : list[str] = []
        rule_triggers : list[str] = []

        # Step 1: Hard override rules
        hard_decision = self._apply_hard_rules(transaction, rule_triggers)

        # Step 2: Score-based decision
        score_decision = self._score_decision(fraud_score)

        # Step 3: Contextual modifiers
        modifier = self._contextual_modifier(transaction, fraud_score, reasons)
        effective_score = min(1.0, fraud_score + modifier)

        # Step 4: Merge — hard rules always win
        if hard_decision:
            final = hard_decision
            reasons.insert(0, "Hard override rule triggered")
        else:
            final = self._score_decision(effective_score)

        confidence = self._confidence(fraud_score, final)
        action     = self._recommended_action(final, fraud_score, transaction)

        elapsed_ms = round((time.time() - t0) * 1000, 2)

        return DecisionResult(
            decision         = final.value,
            fraud_score      = round(float(fraud_score), 6),
            confidence       = confidence,
            reasons          = reasons if reasons else [self._default_reason(final, fraud_score)],
            rule_triggers    = rule_triggers,
            recommended_action = action,
            processing_ms    = elapsed_ms,
        )

    # ── Hard Rules ────────────────────────────────────────
    def _apply_hard_rules(self, txn: dict, triggers: list[str]) -> Optional[Decision]:
        th = self.thresholds

        if txn.get("amount", 0) > th.max_amount_auto_block:
            triggers.append(f"AMOUNT_EXCEEDS_{th.max_amount_auto_block}")
            return Decision.BLOCK

        if txn.get("transactions_last_1h", 0) >= th.max_velocity_1h_block:
            triggers.append("HIGH_VELOCITY_1H")
            return Decision.BLOCK

        if txn.get("failed_attempts_last_24h", 0) >= th.max_failed_attempts:
            triggers.append("EXCESS_FAILED_ATTEMPTS")
            return Decision.BLOCK

        if txn.get("distance_from_home_km", 0) > th.max_distance_km and \
           txn.get("is_international", 0) == 1:
            triggers.append("DISTANCE_INTERNATIONAL_COMBO")
            return Decision.REVIEW

        if txn.get("device_change", 0) == 1 and \
           txn.get("is_international", 0) == 1:
            triggers.append("DEVICE_CHANGE_INTERNATIONAL")
            return Decision.REVIEW

        return None

    # ── Score-Based Decision ──────────────────────────────
    def _score_decision(self, score: float) -> Decision:
        if score >= self.thresholds.block_above:
            return Decision.BLOCK
        if score >= self.thresholds.review_above:
            return Decision.REVIEW
        return Decision.ALLOW

    # ── Contextual Modifiers ──────────────────────────────
    def _contextual_modifier(self, txn: dict, score: float, reasons: list) -> float:
        modifier = 0.0

        if txn.get("is_night", 0) and txn.get("amount", 0) > 500:
            modifier += 0.05
            reasons.append("Night-time high-value transaction")

        if txn.get("new_account", 0) and txn.get("amount", 0) > 200:
            modifier += 0.08
            reasons.append("New account with elevated transaction amount")

        if txn.get("velocity_ratio", 0) > 0.5:
            modifier += 0.04
            reasons.append("High transaction velocity ratio")

        if txn.get("card_present", 1) == 0 and txn.get("is_international", 0):
            modifier += 0.06
            reasons.append("Card-not-present international transaction")

        if txn.get("merchant_category") in ("travel", "entertainment") and score > 0.15:
            modifier += 0.03
            reasons.append("High-risk merchant category")

        return modifier

    # ── Confidence Level ──────────────────────────────────
    def _confidence(self, score: float, decision: Decision) -> str:
        if decision == Decision.ALLOW:
            return "HIGH" if score < 0.10 else "MEDIUM"
        if decision == Decision.BLOCK:
            return "HIGH" if score > 0.80 else "MEDIUM"
        # REVIEW
        margin = abs(score - 0.45)
        return "LOW" if margin < 0.08 else "MEDIUM"

    # ── Recommended Actions ───────────────────────────────
    def _recommended_action(self, decision: Decision, score: float, txn: dict) -> str:
        if decision == Decision.ALLOW:
            return "Process transaction normally"
        if decision == Decision.BLOCK:
            return (
                "Block transaction. Notify cardholder via SMS/email. "
                "Flag account for manual review within 24h."
            )
        # REVIEW
        if score > 0.50:
            return "Hold transaction. Request OTP / step-up authentication."
        return "Flag for analyst review. Allow with enhanced logging."

    def _default_reason(self, decision: Decision, score: float) -> str:
        if decision == Decision.ALLOW:
            return f"Fraud score {score:.3f} is below risk threshold"
        if decision == Decision.BLOCK:
            return f"Fraud score {score:.3f} exceeds block threshold"
        return f"Fraud score {score:.3f} falls in review range"


# ─────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────
_agent: Optional[FraudDecisionAgent] = None

def get_agent() -> FraudDecisionAgent:
    global _agent
    if _agent is None:
        _agent = FraudDecisionAgent()
    return _agent


# ─────────────────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = FraudDecisionAgent()

    tests = [
        (0.05, {"amount": 45, "transactions_last_1h": 1, "is_international": 0,
                "device_change": 0, "is_night": 0, "merchant_category": "grocery",
                "distance_from_home_km": 5, "account_age_days": 500,
                "failed_attempts_last_24h": 0, "velocity_ratio": 0.1,
                "card_present": 1, "new_account": 0}),
        (0.45, {"amount": 350, "transactions_last_1h": 3, "is_international": 0,
                "device_change": 1, "is_night": 1, "merchant_category": "travel",
                "distance_from_home_km": 80, "account_age_days": 20,
                "failed_attempts_last_24h": 1, "velocity_ratio": 0.4,
                "card_present": 0, "new_account": 1}),
        (0.87, {"amount": 2200, "transactions_last_1h": 9, "is_international": 1,
                "device_change": 1, "is_night": 1, "merchant_category": "entertainment",
                "distance_from_home_km": 600, "account_age_days": 10,
                "failed_attempts_last_24h": 3, "velocity_ratio": 0.8,
                "card_present": 0, "new_account": 1}),
    ]

    print("=" * 55)
    print("  AGENTIC DECISION LAYER — TEST")
    print("=" * 55)
    for i, (score, txn) in enumerate(tests, 1):
        result = agent.decide(score, txn)
        print(f"\n[Test {i}] Score={score}")
        print(f"  Decision    : {result.decision}")
        print(f"  Confidence  : {result.confidence}")
        print(f"  Rules       : {result.rule_triggers}")
        print(f"  Reasons     : {result.reasons}")
        print(f"  Action      : {result.recommended_action[:70]}…")
        print(f"  Latency     : {result.processing_ms}ms")

    print("\n✅ Phase 2 Complete — Decision Layer OK!\n")
