@echo off
REM Check AI Inbox Manager Setup Status
REM This script runs the setup checker to verify everything is configured correctly

echo ============================================================
echo AI Inbox Manager - Setup Checker
echo ============================================================
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please create it first:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Running setup checker...
echo.

venv\Scripts\python.exe setup.py

echo.
pause
