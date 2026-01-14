#!/bin/bash

echo "🚀 Starting Excel QA Application..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your credentials before running again."
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Starting server on http://localhost:8000"
echo ""
echo "📝 Login Credentials:"
echo "   Admin: admin / admin123"
echo "   User:  user / user123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
