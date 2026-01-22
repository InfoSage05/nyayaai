@echo off
REM ============================================
REM NyayaAI - Launcher
REM ============================================
REM This script properly launches NyayaAI from the correct directory
REM to ensure Python can import the nyayaai package

cd /d E:\Hackathons\Convolve

echo.
echo ============================================
echo  NyayaAI Multi-Agent Legal AI System
echo ============================================
echo.
echo Running from: %cd%
echo.

if "%1"=="demo" (
    echo Running demo examples...
    python .\nyayaai\demo_examples.py
    goto :end
)

if "%1"=="server" (
    echo Starting API server on http://localhost:8000...
    echo Docs: http://localhost:8000/docs
    echo Health: http://localhost:8000/api/v1/health
    echo.
    python -m uvicorn nyayaai.api.main:app --port 8000 --host 0.0.0.0
    goto :end
)

if "%1"=="setup" (
    echo Setting up Qdrant collections...
    python -m nyayaai.database.setup_collections
    echo.
    echo Ingesting sample data...
    python -m nyayaai.database.ingest_sample_data
    goto :end
)

REM Default: show help
echo Usage:
echo   %0 demo    - Run demo examples
echo   %0 server  - Start API server (port 8000)
echo   %0 setup   - Setup collections and ingest data
echo.

:end
cd /d E:\Hackathons\Convolve\nyayaai
