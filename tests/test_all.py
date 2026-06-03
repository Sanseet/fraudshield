import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.extend([
    str(ROOT / "src" / "ml"),
    str(ROOT / "src" / "agent"),
    str(ROOT / "src" / "db"),
    str(ROOT / "src" / "api"),
])


class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        import pandas as pd
        self.sample = pd.DataFrame([{
            "amount": 250.0, "hour_of_day": 14, "day_of_week": 2,
            "merchant_category": "retail", "country_code": "IN",
            "card_present": 1, "transactions_last_1h": 2,
            "transactions_last_24h": 5, "avg_amount_last_7d": 180.0,
            "distance_from_home_km": 10.0, "account_age_days": 400.0,
            "failed_attempts_last_24h": 0, "is_international": 0, "device_change": 0,
        }])

    def test_feature_columns_present(self):
        from features import engineer_features, FEATURE_COLUMNS
        df = engineer_features(self.sample)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, df.columns, f"Missing feature: {col}")

    def test_log_amount_positive(self):
        from features import engineer_features
        df = engineer_features(self.sample)
        self.assertGreater(df["log_amount"].iloc[0], 0)

    def test_amount_vs_avg(self):
        from features import engineer_features
        df = engineer_features(self.sample)
        expected = 250.0 / (180.0 + 1e-9)
        self.assertAlmostEqual(df["amount_vs_avg"].iloc[0], expected, places=3)

    def test_is_night_daytime(self):
        from features import engineer_features
        df = engineer_features(self.sample)
        self.assertEqual(df["is_night"].iloc[0], 0)  

    def test_velocity_ratio(self):
        from features import engineer_features
        df = engineer_features(self.sample)
        self.assertAlmostEqual(df["velocity_ratio"].iloc[0], 2 / (5 + 1e-9), places=4)

class TestDecisionEngine(unittest.TestCase):

    def setUp(self):
        from decision_engine import FraudDecisionAgent, RiskThresholds
        self.agent = FraudDecisionAgent(RiskThresholds(
            allow_below=0.30, review_above=0.30, block_above=0.60
        ))
        self.base_txn = {
            "amount": 100, "transactions_last_1h": 1, "is_international": 0,
            "device_change": 0, "is_night": 0, "merchant_category": "grocery",
            "distance_from_home_km": 5, "account_age_days": 400,
            "failed_attempts_last_24h": 0, "velocity_ratio": 0.1,
            "card_present": 1, "new_account": 0, "avg_amount_last_7d": 80,
        }

    def test_allow_low_score(self):
        result = self.agent.decide(0.05, self.base_txn)
        self.assertEqual(result.decision, "ALLOW")

    def test_review_mid_score(self):
        result = self.agent.decide(0.50, self.base_txn)
        self.assertEqual(result.decision, "REVIEW")

    def test_block_high_score(self):
        result = self.agent.decide(0.85, self.base_txn)
        self.assertEqual(result.decision, "BLOCK")

    def test_hard_rule_velocity_block(self):
        txn = {**self.base_txn, "transactions_last_1h": 10}
        result = self.agent.decide(0.10, txn)
        self.assertEqual(result.decision, "BLOCK")
        self.assertIn("HIGH_VELOCITY_1H", result.rule_triggers)

    def test_hard_rule_failed_attempts(self):
        txn = {**self.base_txn, "failed_attempts_last_24h": 3}
        result = self.agent.decide(0.10, txn)
        self.assertEqual(result.decision, "BLOCK")
        self.assertIn("EXCESS_FAILED_ATTEMPTS", result.rule_triggers)

    def test_hard_rule_large_amount(self):
        txn = {**self.base_txn, "amount": 15000}
        result = self.agent.decide(0.10, txn)
        self.assertEqual(result.decision, "BLOCK")

    def test_confidence_high_allow(self):
        result = self.agent.decide(0.02, self.base_txn)
        self.assertEqual(result.confidence, "HIGH")

    def test_result_has_all_fields(self):
        result = self.agent.decide(0.5, self.base_txn)
        self.assertIsNotNone(result.recommended_action)
        self.assertIsInstance(result.reasons, list)
        self.assertIsInstance(result.rule_triggers, list)
        self.assertGreaterEqual(result.processing_ms, 0)


class TestPredictor(unittest.TestCase):

    def setUp(self):
        from predictor import FraudPredictor
        self.predictor = FraudPredictor()
        self.predictor.load()

    def _make_txn(self, **overrides):
        base = {
            "amount": 100.0, "hour_of_day": 10, "day_of_week": 2,
            "merchant_category": "grocery", "country_code": "IN",
            "card_present": 1, "transactions_last_1h": 1,
            "transactions_last_24h": 4, "avg_amount_last_7d": 90.0,
            "distance_from_home_km": 5.0, "account_age_days": 500.0,
            "failed_attempts_last_24h": 0, "is_international": 0, "device_change": 0,
        }
        return {**base, **overrides}

    def test_returns_score_in_range(self):
        score, ms = self.predictor.predict(self._make_txn())
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_latency_reasonable(self):
        _, ms = self.predictor.predict(self._make_txn())
        self.assertLess(ms, 500)  # under 500ms

    def test_high_risk_scores_higher(self):
        legit_score, _ = self.predictor.predict(self._make_txn())
        fraud_score, _ = self.predictor.predict(self._make_txn(
            amount=9000, transactions_last_1h=8,
            distance_from_home_km=700, account_age_days=5,
            is_international=1, device_change=1,
            failed_attempts_last_24h=3
        ))
        self.assertGreater(fraud_score, legit_score)

    def test_model_loaded(self):
        self.assertTrue(self.predictor._loaded)
        self.assertIsNotNone(self.predictor.model)
        self.assertIsNotNone(self.predictor.scaler)

class TestSchemas(unittest.TestCase):

    def _valid_payload(self):
        return {
            "transaction_id": "TXN_SCHEMA_001",
            "amount": 120.0, "hour_of_day": 10, "day_of_week": 2,
            "merchant_category": "retail", "country_code": "IN",
            "card_present": 1, "transactions_last_1h": 1,
            "transactions_last_24h": 3, "avg_amount_last_7d": 100.0,
            "distance_from_home_km": 10.0, "account_age_days": 365.0,
            "failed_attempts_last_24h": 0, "is_international": 0, "device_change": 0,
        }

    def test_valid_request(self):
        from schemas import TransactionRequest
        req = TransactionRequest(**self._valid_payload())
        self.assertEqual(req.transaction_id, "TXN_SCHEMA_001")

    def test_invalid_category(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        payload = {**self._valid_payload(), "merchant_category": "casino"}
        with self.assertRaises(ValidationError):
            TransactionRequest(**payload)

    def test_negative_amount_rejected(self):
        from schemas import TransactionRequest
        from pydantic import ValidationError
        payload = {**self._valid_payload(), "amount": -50}
        with self.assertRaises(ValidationError):
            TransactionRequest(**payload)

    def test_country_code_uppercased(self):
        from schemas import TransactionRequest
        payload = {**self._valid_payload(), "country_code": "in"}
        req = TransactionRequest(**payload)
        self.assertEqual(req.country_code, "IN")


class TestDatabase(unittest.TestCase):

    def setUp(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from database import Base, save_transaction, save_fraud_score

        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    def test_save_transaction(self):
        from database import save_transaction, TransactionRecord
        rec = save_transaction(self.db, "TXN_DB_001", {
            "amount": 100, "hour_of_day": 10, "day_of_week": 1,
            "merchant_category": "grocery", "country_code": "IN",
        })
        self.assertEqual(rec.transaction_id, "TXN_DB_001")

    def test_save_fraud_score(self):
        from database import save_fraud_score
        rec = save_fraud_score(self.db, "TXN_DB_002", 0.75, "BLOCK", "HIGH", 12.3)
        self.assertEqual(rec.decision, "BLOCK")
        self.assertAlmostEqual(rec.fraud_score, 0.75)

    def test_save_decision(self):
        from database import save_decision
        rec = save_decision(self.db, "TXN_DB_003", {
            "decision": "REVIEW", "fraud_score": 0.45,
            "confidence": "MEDIUM", "reasons": ["Night transaction"],
            "rule_triggers": [], "recommended_action": "Flag for review",
        })
        self.assertEqual(rec.decision, "REVIEW")


class TestMonitoring(unittest.TestCase):

    def setUp(self):
        from monitoring import MetricsCollector
        self.collector = MetricsCollector()

    def test_empty_snapshot(self):
        snap = self.collector.snapshot()
        self.assertEqual(snap.total_transactions, 0)
        self.assertEqual(snap.avg_fraud_score, 0.0)

    def test_record_and_snapshot(self):
        self.collector.record(0.85, "BLOCK", 12.5)
        self.collector.record(0.05, "ALLOW", 8.3)
        snap = self.collector.snapshot()
        self.assertEqual(snap.total_transactions, 2)
        self.assertIn("BLOCK", snap.decision_distribution)
        self.assertIn("ALLOW", snap.decision_distribution)

    def test_error_tracking(self):
        self.collector.record(0.0, "ERROR", 0.0, is_error=True)
        snap = self.collector.snapshot()
        self.assertEqual(snap.error_count, 1)
        self.assertGreater(snap.error_rate_pct, 0)


if __name__ == "__main__":
    print("=" * 55)
    print("  FRAUD DETECTION — TEST SUITE")
    print("=" * 55)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestFeatureEngineering, TestDecisionEngine,
        TestPredictor, TestSchemas, TestDatabase, TestMonitoring,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n{'✅ ALL TESTS PASSED' if result.wasSuccessful() else '❌ SOME TESTS FAILED'}")
