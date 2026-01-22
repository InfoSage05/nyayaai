# NyayaAI - Quick Command Reference

## One-Time Setup (Do This First)

```bash
# 1. Navigate to project
cd e:\Hackathons\Convolve\nyayaai

# 2. Create virtual environment
python -m venv myenv
myenv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .

# 4. Set Groq API Key
echo "GROQ_API_KEY=your_actual_groq_api_key_here" > .env

# 5. Start Docker & initialize Qdrant
docker compose up -d qdrant
python -m database.setup_collections

# Optional: Ingest sample data (if first time)
python -m database.ingest_sample_data
```

---

## Run Everything (Do This Every Time)

**Open 3 separate terminals in the project directory:**

### Terminal 1: Start Qdrant
```bash
cd e:\Hackathons\Convolve\nyayaai
docker compose up qdrant
```
✓ Wait for: `qdrant-1 | ... Qdrant started on ...`

### Terminal 2: Start Backend API
```bash
cd e:\Hackathons\Convolve\nyayaai
myenv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```
✓ Wait for: `INFO: Uvicorn running on http://127.0.0.1:8000`

### Terminal 3: Start Frontend
```bash
cd e:\Hackathons\Convolve\nyayaai
myenv\Scripts\activate
streamlit run frontend/app.py
```
✓ Wait for: `Local URL: http://localhost:8501`

---

## Access the Application

- **Frontend (UI)**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health
- **Qdrant Console**: http://localhost:6333

---

## Verify Everything Works

```bash
# Test Groq LLM
python test_error_handling.py

# Check Qdrant
curl http://localhost:6333/health

# Check API
curl http://localhost:8000/health

# Query through API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the Indian Constitution?"}'
```

---

## Troubleshooting Quick Fixes

### Groq API Error
```bash
# Verify API key is set
echo %GROQ_API_KEY%

# Test Groq directly
python -c "
from groq import Groq
import os
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Say hello'}],
    model='mixtral-8x7b-32768'
)
print('✓ Groq working!')
"
```

### Qdrant Not Running
```bash
# Check if running
docker ps | grep qdrant

# Restart Qdrant
docker compose restart qdrant

# View logs
docker logs nyayaai-qdrant
```

### Port Already in Use
```bash
# Kill processes on ports
taskkill /F /IM python.exe  # Kills all Python
taskkill /F /IM docker.exe  # Kills Docker

# Or restart everything
docker compose down
```

### API Won't Start
```bash
# Clear Python cache
rmdir /s __pycache__

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Clear virtual environment
rmdir /s myenv
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```

---

## Environment Variables

```bash
# Required
GROQ_API_KEY=your_actual_key

# Optional (defaults work fine)
QDRANT_HOST=localhost
QDRANT_PORT=6333
LOG_LEVEL=INFO
DEBUG=False
```

---

## Common Tasks

### Query the API
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I file an RTI application?",
    "include_context": true
  }' | jq .
```

### Add New Data to Qdrant
```bash
# Via IndiaCode connector
python -c "
from connectors.indiacode_connector import ingest_act_from_url
ingest_act_from_url('https://example.com/act', collection_name='statutes_vectors')
"
```

### Test Specific Agent
```python
from agents.reasoning_agent import ReasoningAgent
from core.agent_base import AgentInput

agent = ReasoningAgent()
result = agent.process(AgentInput(query="Your query here"))
print(result.result)
```

### View Qdrant Collections
```bash
curl http://localhost:6333/collections | jq .
```

### Check Database Stats
```bash
# Python script
from database.qdrant_client import qdrant_manager
stats = qdrant_manager.client.get_collection_info('legal_taxonomy_vectors')
print(f"Points: {stats.points_count}")
```

---

## Helpful Shortcuts

```bash
# Create a Windows batch file to start everything at once
# save as: start_all.bat

@echo off
cd e:\Hackathons\Convolve\nyayaai

start "Qdrant" cmd /k "docker compose up qdrant"
start "Backend API" cmd /k "myenv\Scripts\activate && uvicorn api.main:app --reload --port 8000"
start "Frontend" cmd /k "myenv\Scripts\activate && streamlit run frontend/app.py"

echo.
echo Started all services! Open:
echo - Frontend: http://localhost:8501
echo - API Docs: http://localhost:8000/docs
pause
```

Then just run: `start_all.bat`

---

## Useful VS Code Settings

Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/myenv/Scripts/python.exe",
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  }
}
```

---

## Performance Tips

- **API slow?** Increase `max_tokens` in groq_client.py
- **Streamlit slow?** Use `--logger.level=warning` flag
- **Qdrant slow?** Check disk space, possibly need more RAM
- **LLM slow?** Normal for first request, caches after

---

## Status Check Commands

```bash
# Everything working?
docker ps                                    # Check Docker
echo %GROQ_API_KEY%                         # Check API key
pip list | findstr groq                      # Check Groq installed
pip list | findstr qdrant                    # Check Qdrant SDK
where python                                 # Check Python location
```

---

**Need help?** Check:
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Full documentation
2. [ERROR_NONE_FIXED.md](ERROR_NONE_FIXED.md) - Error handling details
3. [docs/](docs/) - Architecture & design docs

**Last Updated**: January 22, 2026
