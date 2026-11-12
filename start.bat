@echo off
title EduConnect (Render & Git Ready)
cd /d "%~dp0"

echo ======================================================================
echo              EduConnect - 3-Step Hyperlocal Platform
echo ======================================================================
echo  Step 1: User Data & GPS Coordinates
echo  Step 2: Haversine Distance Trigonometry
echo  Step 3: Tuition Cohorts & Real-Time Chat
echo ======================================================================
echo.

set PYTHON_EXE=C:\src\online education website\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    python app.py
) else (
    start "" http://127.0.0.1:5000
    "%PYTHON_EXE%" app.py
)
pause
