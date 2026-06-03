# Real-Time Fraud Detection System

An intelligent, production-oriented fraud detection system with ML-powered risk scoring and an agentic decision layer. Built as a complete Applied AI Engineer portfolio project.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | XGBoost, Scikit-Learn, imbalanced-learn (SMOTE) |
| Data | Pandas, NumPy |
| API | FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy ORM |
| Testing | Python unittest |

---

## Project Structure

```
fraud_detection/
├── data/
│   ├── transactions.csv          # Synthetic dataset (50k rows)
│   └── fraud_detection.db        # SQLite database
├── models/
│   ├── fraud_model.joblib        # Trained XGBoost model
│   ├── scaler.joblib             # Fitted StandardScaler
│   └── model_meta.json           # Thresholds, feature list, eval metrics
├── src/
│   ├── ml/
│   │   ├── generate_data.py      # Synthetic fraud dataset generator
│   │   ├── features.py           # Feature engineering pipeline (23 features)
│   │   ├── train.py              # Training pipeline: SMOTE + XGBoost + eval
│   │   └── predictor.py          # Inference engine (singleton)
│   ├── agent/
│   │   └── decision_engine.py    # Agentic decision layer: ALLOW/REVIEW/BLOCK
│   ├── db/
│   │   └── database.py           # SQLAlchemy ORM models + CRUD helpers
│   └── api/
│       ├── main.py               # FastAPI app + all endpoints
│       ├── schemas.py            # Pydantic request/response models
│       └── monitoring.py         # Real-time metrics collector
├── tests/
│   └── test_all.py               # 27 unit tests across all layers
├── requirements.txt
├── setup.sh                      # One-shot setup script
└── README.md
```

---

## Setup

```bash
git clone <repo>
cd fraud_detection
pip install -r requirements.txt

# Generate dataset → Train model → Run tests
bash setup.sh

# Start API
uvicorn src.api.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `GET` | `/metrics` | Real-time monitoring metrics |
| `POST` | `/predict` | Score a single transaction |
| `POST` | `/predict/batch` | Score up to 100 transactions |
| `GET` | `/fraud-score/{id}` | Retrieve score for past transaction |
| `GET` | `/transactions/recent` | List recent scored transactions |

### Example — Single Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN001",
    "amount": 2500,
    "hour_of_day": 2,
    "day_of_week": 6,
    "merchant_category": "travel",
    "country_code": "US",
    "card_present": 0,
    "transactions_last_1h": 7,
    "transactions_last_24h": 18,
    "avg_amount_last_7d": 120,
    "distance_from_home_km": 400,
    "account_age_days": 8,
    "failed_attempts_last_24h": 2,
    "is_international": 1,
    "device_change": 1
  }'
```

### Example Response

```json
{
  "transaction_id": "TXN001",
  "fraud_score": 0.999993,
  "decision": "BLOCK",
  "confidence": "HIGH",
  "reasons": [
    "Hard override rule triggered",
    "Card-not-present international transaction",
    "High-risk merchant category"
  ],
  "rule_triggers": ["HIGH_VELOCITY_1H"],
  "recommended_action": "Block transaction. Notify cardholder via SMS/email.",
  "processing_ms": 26.7,
  "model_version": "v1.0",
  "timestamp": "2024-01-15T02:33:29"
}
```

---

## ML Pipeline

### Dataset
- 50,000 synthetic transactions, 3% fraud rate
- 15 raw features including amount, velocity, geolocation, device signals

### Feature Engineering (23 features)
- Log-transformed and normalized amounts
- Cyclic time encoding (sin/cos of hour)
- Velocity ratios (1h / 24h transaction counts)
- Composite risk score
- Distance and account age transforms

### Class Imbalance
SMOTE oversampling balances the training set from 97/3 to 50/50 before model training.

### Model
XGBoost with 400 estimators, depth 6, learning rate 0.05, L1/L2 regularization.

### Evaluation Results

| Metric | Score |
|---|---|
| Precision | 0.9768 |
| Recall | 0.9833 |
| F1 Score | 0.9801 |
| ROC-AUC | 0.9996 |
| Avg Precision | 0.9963 |

---

## Agentic Decision Layer

The decision engine converts raw fraud scores into business actions using a three-tier logic:

```
Score < 0.30  →  ALLOW   (process normally)
Score 0.30–0.60  →  REVIEW  (flag / step-up auth)
Score > 0.60  →  BLOCK   (halt + notify)
```

Hard override rules fire regardless of score:
- `transactions_last_1h >= 8` → BLOCK
- `failed_attempts_last_24h >= 3` → BLOCK
- `amount > 10,000` → BLOCK
- `device_change=1 AND is_international=1` → REVIEW

Contextual modifiers bump the effective score for night-time high-value transactions, new accounts, high velocity ratios, and card-not-present international combinations.

---

## Database Schema

```sql
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    transaction_id TEXT UNIQUE NOT NULL,
    amount REAL, hour_of_day INTEGER, day_of_week INTEGER,
    merchant_category TEXT, country_code TEXT,
    card_present BOOLEAN, transactions_last_1h INTEGER,
    transactions_last_24h INTEGER, avg_amount_last_7d REAL,
    distance_from_home_km REAL, account_age_days REAL,
    failed_attempts_last_24h INTEGER, is_international BOOLEAN,
    device_change BOOLEAN, created_at DATETIME
);

CREATE TABLE fraud_scores (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    fraud_score REAL, decision TEXT, confidence TEXT,
    model_version TEXT, processing_ms REAL, created_at DATETIME
);

CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    decision TEXT, fraud_score REAL, confidence TEXT,
    reasons JSON, rule_triggers JSON,
    recommended_action TEXT, created_at DATETIME
);

CREATE TABLE prediction_logs (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    input_features JSON, fraud_score REAL,
    decision TEXT, latency_ms REAL,
    error TEXT, created_at DATETIME
);
```

---

## Monitoring Metrics

Available at `GET /metrics`:

- `total_transactions` — lifetime count
- `fraud_rate_pct` — % transactions scoring above block threshold
- `avg_fraud_score` — rolling mean score
- `avg_latency_ms`, `p95_latency_ms`, `p99_latency_ms` — inference latency
- `decision_distribution` — ALLOW/REVIEW/BLOCK counts + percentages
- `transactions_last_1min`, `transactions_last_5min` — throughput rate
- `error_count`, `error_rate_pct` — failure tracking
- `uptime_seconds` — service uptime

---

## Running Tests

```bash
cd tests
python test_all.py
```

27 tests across: feature engineering, decision engine, ML predictor, Pydantic schemas, database CRUD, metrics collector.

---

## Skills Demonstrated

- End-to-end ML pipeline: EDA → feature engineering → SMOTE → XGBoost → evaluation
- Production API design: FastAPI, Pydantic v2 validation, structured error handling
- Agentic system design: multi-signal rule engine with contextual modifiers
- Database engineering: SQLAlchemy ORM, indexed schema, CRUD abstraction
- Observability: real-time metrics, percentile latency, sliding window rates
- Software engineering: modular architecture, singleton patterns, 27-test suite
