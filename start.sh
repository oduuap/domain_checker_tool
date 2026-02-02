#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Domain Finder - Traffic Edition"
echo "=================================="
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "Starting server..."
echo "Open: http://localhost:5000"
echo ""
python3 app.py
