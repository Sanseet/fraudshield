#!/bin/bash
set -e
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Generating dataset..."
python src/ml/generate_data.py

echo "Training model..."
python src/ml/train.py

echo "Build complete!"
