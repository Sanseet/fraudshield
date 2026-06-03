"""
Fraud Detection Model — Training Pipeline
XGBoost + SMOTE + Full Evaluation Suite
"""

import json
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix, average_precision_score,
)
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

from features import engineer_features, FEATURE_COLUMNS

ROOT = Path(__file__).parent.parent.parent
DATA_PATH   = ROOT / "data" / "transactions.csv"
MODEL_DIR   = ROOT / "models"
MODEL_PATH  = MODEL_DIR / "fraud_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
META_PATH   = MODEL_DIR / "model_meta.json"


# ─────────────────────────────────────────
# 1. Load & Preprocess
# ─────────────────────────────────────────
def load_and_preprocess(path: Path) -> tuple:
    print("📂 Loading dataset …")
    df = pd.read_csv(path, parse_dates=["timestamp"])

    print(f"   Shape           : {df.shape}")
    print(f"   Missing values  : {df.isnull().sum().sum()}")
    print(f"   Fraud rate      : {df['is_fraud'].mean()*100:.2f}%")

    # Drop leakage columns
    df = df.drop(columns=["transaction_id", "timestamp"], errors="ignore")

    # Engineer features
    df_feat = engineer_features(df)
    X = df_feat[FEATURE_COLUMNS]
    y = df_feat["is_fraud"]

    print(f"   Features used   : {len(FEATURE_COLUMNS)}")
    return X, y, df


# ─────────────────────────────────────────
# 2. Handle Class Imbalance with SMOTE
# ─────────────────────────────────────────
def apply_smote(X_train, y_train):
    print("\n⚖️  Applying SMOTE …")
    before = dict(zip(*np.unique(y_train, return_counts=True)))
    sm = SMOTE(random_state=42, k_neighbors=5)
    X_res, y_res = sm.fit_resample(X_train, y_train)
    after = dict(zip(*np.unique(y_res, return_counts=True)))
    print(f"   Before SMOTE    : {before}")
    print(f"   After SMOTE     : {after}")
    return X_res, y_res


# ─────────────────────────────────────────
# 3. Train XGBoost Model
# ─────────────────────────────────────────
def train_model(X_train, y_train):
    print("\n🚀 Training XGBoost model …")
    t0 = time.time()

    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=1,          # SMOTE already balanced
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, verbose=False)
    elapsed = time.time() - t0
    print(f"   Training time   : {elapsed:.1f}s")
    return model


# ─────────────────────────────────────────
# 4. Evaluate
# ─────────────────────────────────────────
def evaluate(model, X_test, y_test, scaler=None) -> dict:
    print("\n📊 Evaluating model …")

    X_eval = scaler.transform(X_test) if scaler else X_test
    y_pred = model.predict(X_eval)
    y_prob = model.predict_proba(X_eval)[:, 1]

    metrics = {
        "precision"       : round(precision_score(y_test, y_pred), 4),
        "recall"          : round(recall_score(y_test, y_pred), 4),
        "f1_score"        : round(f1_score(y_test, y_pred), 4),
        "roc_auc"         : round(roc_auc_score(y_test, y_prob), 4),
        "avg_precision"   : round(average_precision_score(y_test, y_prob), 4),
        "test_samples"    : int(len(y_test)),
        "fraud_samples"   : int(y_test.sum()),
    }

    print(f"\n{'─'*45}")
    print(f"  Precision        : {metrics['precision']:.4f}")
    print(f"  Recall           : {metrics['recall']:.4f}")
    print(f"  F1 Score         : {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC          : {metrics['roc_auc']:.4f}")
    print(f"  Avg Precision    : {metrics['avg_precision']:.4f}")
    print(f"{'─'*45}")

    print("\n  Classification Report:\n")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))

    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:")
    print(f"    TN={cm[0,0]:5d}  FP={cm[0,1]:5d}")
    print(f"    FN={cm[1,0]:5d}  TP={cm[1,1]:5d}")

    return metrics


# ─────────────────────────────────────────
# 5. Feature Importance
# ─────────────────────────────────────────
def print_feature_importance(model, top_n=10):
    importance = model.feature_importances_
    fi = sorted(zip(FEATURE_COLUMNS, importance), key=lambda x: x[1], reverse=True)
    print(f"\n🏆 Top {top_n} Feature Importances:")
    for name, score in fi[:top_n]:
        bar = "█" * int(score * 200)
        print(f"   {name:<30s} {score:.4f}  {bar}")
    return fi


# ─────────────────────────────────────────
# 6. Save Artifacts
# ─────────────────────────────────────────
def save_artifacts(model, scaler, metrics, feature_importance):
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    meta = {
        "model_type"        : "XGBoostClassifier",
        "feature_columns"   : FEATURE_COLUMNS,
        "metrics"           : metrics,
        "feature_importance": {k: float(v) for k, v in feature_importance[:15]},
        "thresholds": {
            "allow"  : 0.30,
            "review" : 0.60,
            "block"  : 0.60,
        },
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n✅ Artifacts saved:")
    print(f"   Model    → {MODEL_PATH}")
    print(f"   Scaler   → {SCALER_PATH}")
    print(f"   Metadata → {META_PATH}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    print("=" * 50)
    print("  FRAUD DETECTION — TRAINING PIPELINE")
    print("=" * 50)

    X, y, _ = load_and_preprocess(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\n   Train size : {len(X_train):,}")
    print(f"   Test size  : {len(X_test):,}")

    X_train_res, y_train_res = apply_smote(X_train.values, y_train.values)

    # Scale after SMOTE
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled  = scaler.transform(X_test.values)

    model = train_model(X_train_scaled, y_train_res)

    metrics = evaluate(model, X_test_scaled, y_test.values)
    fi = print_feature_importance(model)
    save_artifacts(model, scaler, metrics, fi)

    print("\n🎉 Phase 1 Complete — Model Training Done!\n")


if __name__ == "__main__":
    main()
