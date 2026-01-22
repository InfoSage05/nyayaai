# NyayaAI Server Launcher for PowerShell
# Fixes Anaconda multiprocessing conflicts

# Clear Anaconda environment variables
$env:CONDA_PREFIX = ""
$env:CONDA_DEFAULT_ENV = ""

# Set Docker path
$env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path

# Set Python path for module resolution
$env:PYTHONPATH = "E:\Hackathons\Convolve\nyayaai"

# Change directory
cd E:\Hackathons\Convolve\nyayaai

# Use venv Python explicitly
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NyayaAI Server Starting..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python: $((.\venv\Scripts\python.exe --version) 2>&1)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Server: http://localhost:8000" -ForegroundColor Green
Write-Host "Docs:   http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health: http://localhost:8000/api/v1/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run WITHOUT reloader (--no-reload) to avoid multiprocessing issues
.\venv\Scripts\python.exe -m uvicorn nyayaai.api.main:app --no-reload --port 8000 --host 0.0.0.0
