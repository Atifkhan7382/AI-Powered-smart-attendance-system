@echo off
echo ================================
echo Smart Attendance System - Backend Server
echo ================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo.
echo Checking if virtual environment exists...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/updating dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check requirements.txt and try again
    pause
    exit /b 1
)

echo.
echo Checking attendance system setup...
python -c "from smart_attendance_system import OptimizedAttendanceSystem; system = OptimizedAttendanceSystem(); system.verify_system_setup()"

echo.
echo ================================
echo Starting Flask API Server...
echo ================================
echo Server will be available at: http://localhost:5000
echo API endpoints will be at: http://localhost:5000/api/
echo.
echo Press Ctrl+C to stop the server
echo ================================
echo.

python flask_api.py

echo.
echo Server stopped.
pause
