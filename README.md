# Real-Time Fraud Detection System

A production-grade fraud detection system combining an XGBoost ML model with an agentic decision layer to score financial transactions in real time. Built with a clean, modular architecture covering the full lifecycle from data generation to a monitored REST API.

---

## Highlights

- **98% F1 Score** on a 50k-transaction synthetic dataset with a 3% fraud rate
- **Sub-30ms inference** with p95/p99 latency tracking
- **Three-tier decision engine** (ALLOW / REVIEW / BLOCK) with hard override rules and contextual modifiers
- **27-test suite** covering every layer — features, model, agent, API, and database

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | XGBoost, Scikit-Learn, imbalanced-learn (SMOTE) |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Database | SQLite, SQLAlchemy ORM |
| Testing | Python unittest |
| Data | Pandas, NumPy |

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
│   │   ├── train.py              # SMOTE + XGBoost training pipeline
│   │   └── predictor.py          # Inference engine (singleton pattern)
│   ├── agent/
│   │   └── decision_engine.py    # Agentic decision layer
│   ├── db/
│   │   └── database.py           # SQLAlchemy ORM models + CRUD helpers
│   └── api/
│       ├── main.py               # FastAPI app and endpoints
│       ├── schemas.py            # Pydantic request/response models
│       └── monitoring.py         # Real-time metrics collector
├── tests/
│   └── test_all.py               # 27 unit tests
├── requirements.txt
└── setup.sh                      # One-shot setup script
```

---

## Getting Started

```bash
git clone <repo>
cd fraud_detection
pip install -r requirements.txt

# Generate dataset → train model → run tests
bash setup.sh

# Start the API
uvicorn src.api.main:app --reload --port 8000
```

Interactive API docs available at `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `GET` | `/metrics` | Real-time monitoring metrics |
| `POST` | `/predict` | Score a single transaction |
| `POST` | `/predict/batch` | Score up to 100 transactions |
| `GET` | `/fraud-score/{id}` | Retrieve score for a past transaction |
| `GET` | `/transactions/recent` | List recently scored transactions |

### Example Request

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
50,000 synthetic transactions with a 3% fraud rate across 15 raw features — including transaction amount, velocity signals, geolocation, and device indicators.

### Feature Engineering
23 engineered features built from the raw inputs:
- Log-transformed and normalized amounts
- Cyclic time encoding (sin/cos of hour of day)
- Velocity ratios (1h vs. 24h transaction counts)
- Composite risk score
- Distance and account age transforms

### Class Imbalance
SMOTE oversampling rebalances the training set from 97/3 to 50/50 before model training, preventing the classifier from ignoring the minority fraud class.

### Model
XGBoost with 400 estimators, max depth 6, learning rate 0.05, and L1/L2 regularization.

### Evaluation

| Metric | Score |
|---|---|
| Precision | 0.9768 |
| Recall | 0.9833 |
| F1 Score | 0.9801 |
| ROC-AUC | 0.9996 |
| Avg Precision | 0.9963 |

---

## Agentic Decision Layer

The decision engine translates raw model scores into business actions using a three-tier threshold system, layered with hard override rules and contextual score modifiers.

### Decision Thresholds

| Score Range | Decision | Action |
|---|---|---|
| < 0.30 | ALLOW | Process normally |
| 0.30 – 0.60 | REVIEW | Flag for step-up authentication |
| > 0.60 | BLOCK | Halt and notify cardholder |

### Hard Override Rules
These fire regardless of the model score:

- `transactions_last_1h >= 8` → **BLOCK**
- `failed_attempts_last_24h >= 3` → **BLOCK**
- `amount > 10,000` → **BLOCK**
- `device_change = 1 AND is_international = 1` → **REVIEW**

### Contextual Modifiers
The effective score is bumped upward for:
- Night-time high-value transactions
- New accounts (low `account_age_days`)
- High velocity ratios
- Card-not-present international combinations

---

## Database Schema

Four tables persist the full transaction lifecycle — raw inputs, model scores, agent decisions, and a complete prediction audit log.

```sql
transactions      -- raw input features per transaction
fraud_scores      -- model score, confidence, and latency
decisions         -- agent decision, reasons, and recommended action
prediction_logs   -- full audit log with input features and errors
```

---

## Monitoring

The `/metrics` endpoint exposes real-time observability:

- **Throughput** — transactions per minute and per 5-minute window
- **Fraud rate** — percentage of transactions above the block threshold
- **Latency** — average, p95, and p99 inference times
- **Decision distribution** — ALLOW / REVIEW / BLOCK counts and percentages
- **Error tracking** — error count and error rate
- **Uptime** — service uptime in seconds

---

## Tests

```bash
cd tests && python test_all.py
```

27 tests covering feature engineering, the decision engine, ML predictor, Pydantic schemas, database CRUD operations, and the metrics collector.
