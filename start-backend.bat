@echo off
REM Start AI Inbox Manager Backend
REM This script activates the virtual environment and starts the FastAPI server

echo ============================================================
echo Starting AI Inbox Manager Backend
echo ============================================================
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/api/v1/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
