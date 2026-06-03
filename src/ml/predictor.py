from __future__ import annotations

import json
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

ROOT        = Path(__file__).parent.parent.parent
MODEL_PATH  = ROOT / "models" / "fraud_model.joblib"
SCALER_PATH = ROOT / "models" / "scaler.joblib"
META_PATH   = ROOT / "models" / "model_meta.json"


class FraudPredictor:

    def __init__(self):
        self.model         = None
        self.scaler        = None
        self.feature_cols  = []
        self.model_version = "v1.0"
        self._loaded       = False

    def load(self):
        if self._loaded:
            return
        self.model   = joblib.load(MODEL_PATH)
        self.scaler  = joblib.load(SCALER_PATH)
        with open(META_PATH) as f:
            meta = json.load(f)
        self.feature_cols = meta["feature_columns"]
        self._loaded = True
        print(f"✅ Model loaded ({len(self.feature_cols)} features)")

    def predict(self, payload: dict) -> tuple[float, float]:
        if not self._loaded:
            self.load()

        t0 = time.perf_counter()

        # Build single-row DataFrame
        df = pd.DataFrame([payload])

        # Engineer features (same pipeline as training)
        import sys
        sys.path.insert(0, str(ROOT / "src" / "ml"))
        from features import engineer_features, FEATURE_COLUMNS

        df_feat = engineer_features(df)

        # Align columns — fill missing with 0
        missing = [c for c in FEATURE_COLUMNS if c not in df_feat.columns]
        for m in missing:
            df_feat[m] = 0.0

        X = df_feat[FEATURE_COLUMNS].values
        X_scaled = self.scaler.transform(X)

        prob = self.model.predict_proba(X_scaled)[0, 1]
        latency_ms = (time.perf_counter() - t0) * 1000

        return float(prob), round(latency_ms, 3)


_predictor: Optional[FraudPredictor] = None


def get_predictor() -> FraudPredictor:
    global _predictor
    if _predictor is None:
        _predictor = FraudPredictor()
        _predictor.load()
    return _predictor
