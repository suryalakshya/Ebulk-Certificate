#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "============================================================"
echo "1. Installing Python dependencies..."
echo "============================================================"
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "============================================================"
echo "2. Building React Frontend static assets..."
echo "============================================================"
cd frontend
npm install
npm run build
cd ..

echo "============================================================"
echo "✓ Render Build Completed Successfully!"
echo "============================================================"
