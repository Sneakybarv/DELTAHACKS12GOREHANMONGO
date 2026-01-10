@echo off
REM Receipt Scanner - Quick Start Script for Windows

echo 🧾 Starting Receipt Scanner...
echo.

REM Check if .env exists
if not exist backend\.env (
    echo ❌ Error: backend\.env not found!
    echo Please create backend\.env from backend\.env.example and add your API keys
    echo.
    echo Required:
    echo   - MONGODB_URI ^(from MongoDB Atlas^)
    echo   - GEMINI_API_KEY ^(from ai.google.dev^)
    echo.
    pause
    exit /b 1
)

REM Start backend
echo 🐍 Starting backend server...
cd backend

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate

if not exist venv\installed (
    echo Installing Python dependencies...
    pip install -r requirements.txt >nul 2>&1
    type nul > venv\installed
)

REM Start backend in new window
start "Receipt Scanner Backend" cmd /k "venv\Scripts\activate && python main.py"
echo ✅ Backend starting on http://localhost:8000

cd ..

REM Wait for backend to start
echo ⏳ Waiting for backend to start...
timeout /t 3 /nobreak >nul

REM Start frontend
echo ⚛️  Starting frontend server...
cd frontend

REM Install dependencies if needed
if not exist node_modules (
    echo Installing Node dependencies... ^(this may take a few minutes^)
    call npm install >nul 2>&1
)

REM Start frontend in new window
start "Receipt Scanner Frontend" cmd /k "npm run dev"
echo ✅ Frontend starting on http://localhost:3000

cd ..

echo.
echo ==================================================
echo 🚀 Receipt Scanner is running!
echo ==================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Close the terminal windows to stop the servers
echo.
pause
