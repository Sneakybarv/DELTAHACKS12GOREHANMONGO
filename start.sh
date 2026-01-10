#!/bin/bash

# Receipt Scanner - Quick Start Script
# This script starts both backend and frontend servers

echo "🧾 Starting Receipt Scanner..."
echo ""

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "❌ Error: backend/.env not found!"
    echo "Please create backend/.env from backend/.env.example and add your API keys"
    echo ""
    echo "Required:"
    echo "  - MONGODB_URI (from MongoDB Atlas)"
    echo "  - GEMINI_API_KEY (from ai.google.dev)"
    echo ""
    exit 1
fi

# Start backend in background
echo "🐍 Starting backend server..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    touch venv/installed
fi

# Start backend
python main.py &
BACKEND_PID=$!
echo "✅ Backend running on http://localhost:8000 (PID: $BACKEND_PID)"

cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend
echo "⚛️  Starting frontend server..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies... (this may take a few minutes)"
    npm install > /dev/null 2>&1
fi

# Start frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend running on http://localhost:3000 (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "=================================================="
echo "🚀 Receipt Scanner is running!"
echo "=================================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Store PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for Ctrl+C
trap cleanup INT

cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f .backend.pid .frontend.pid
    echo "✅ Servers stopped"
    exit 0
}

# Keep script running
wait
