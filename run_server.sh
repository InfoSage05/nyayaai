#!/usr/bin/env bash
# Alternative: Use Windows Subsystem for Linux or Git Bash instead of PowerShell
# This avoids Anaconda conflicts entirely

# Navigate to project
cd /e/Hackathons/Convolve/nyayaai

# Activate venv
source venv/Scripts/activate

# Export variables
export PYTHONPATH=/e/Hackathons/Convolve/nyayaai
export PATH=/c/Program\ Files/Docker/Docker/resources/bin:$PATH

# Run server
python -m uvicorn nyayaai.api.main:app --no-reload --port 8000 --host 0.0.0.0
