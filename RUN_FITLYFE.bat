@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo              FITLYFE
echo ========================================
echo.

if not exist "..\.venv\Scripts\python.exe" (
    echo [FitLyfe] ERROR: Virtual environment not found.
    echo Expected location:
    echo ..\.venv
    echo.
    pause
    exit /b 1
)

echo [FitLyfe] Using existing virtual environment...
echo.

call "..\.venv\Scripts\activate.bat"

if errorlevel 1 (
    echo [FitLyfe] ERROR: Could not activate virtual environment.
    echo.
    pause
    exit /b 1
)

echo [FitLyfe] Starting server...
echo.
echo Open: http://127.0.0.1:5000
echo.
echo Press CTRL+C to stop FitLyfe.
echo.

python app.py

echo.
echo [FitLyfe] Server stopped.
pause