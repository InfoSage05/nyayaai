@echo off
REM ============================================
REM NyayaAI Server Launcher (Windows Batch)
REM ============================================

REM Add Docker to PATH
set PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%

REM Change to project directory
cd /d E:\Hackathons\Convolve\nyayaai

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Set PYTHONPATH
set PYTHONPATH=E:\Hackathons\Convolve\nyayaai

REM Clear any conda activation
set CONDA_PREFIX=
set CONDA_DEFAULT_ENV=

echo.
echo ============================================
echo  NyayaAI Server Starting...
echo ============================================
echo.
echo Python: 
.\venv\Scripts\python.exe --version
echo.
echo Server: http://localhost:8000
echo Docs:   http://localhost:8000/docs
echo Health: http://localhost:8000/api/v1/health
echo.
echo Press Ctrl+C to stop
echo.

REM Run WITHOUT reloader (--no-reload) to avoid multiprocessing issues with Anaconda
.\venv\Scripts\python.exe -m uvicorn nyayaai.api.main:app --no-reload --port 8000 --host 0.0.0.0

pause
