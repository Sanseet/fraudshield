#!/usr/bin/env bash
# setup.sh — One-shot bootstrap for the Fraud Detection System

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  Fraud Detection System — Setup"
echo "============================================"

# 1. Install dependencies
echo ""
echo "[1/4] Installing Python dependencies..."
pip install -r "$ROOT/requirements.txt" --break-system-packages -q

# 2. Generate dataset
echo ""
echo "[2/4] Generating synthetic dataset..."
cd "$ROOT/src/ml"
python generate_data.py

# 3. Train model
echo ""
echo "[3/4] Training XGBoost model..."
python train.py

# 4. Run tests
echo ""
echo "[4/4] Running test suite..."
cd "$ROOT/tests"
python test_all.py

echo ""
echo "============================================"
echo "  Setup complete! Start the API with:"
echo ""
echo "  cd fraud_detection"
echo "  uvicorn src.api.main:app --reload --port 8000"
echo ""
echo "  Then visit: http://localhost:8000/docs"
echo "============================================"
