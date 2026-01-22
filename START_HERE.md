# NyayaAI - Quick Start Guide

## ✅ Code Status
All code has been updated and tested:
- ✅ All agents use LLM-based generation
- ✅ Summarization agent created and connected
- ✅ All syntax errors fixed
- ✅ Streamlit frontend updated to display unified summary
- ✅ Orchestrator properly connects all agents

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment
Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_groq_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Step 3: Start Qdrant (Vector Database)
```bash
docker compose up -d qdrant
```

Wait a few seconds for Qdrant to start, then verify:
```bash
curl http://localhost:6333/collections
```

### Step 4: Initialize Qdrant Collections
```bash
python3 -m database.setup_collections
```

### Step 5: Ingest Sample Data (Optional)
```bash
python3 -m database.ingest_sample_data
```

### Step 6: Start the API Server
In one terminal:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Start Streamlit Frontend
In another terminal:
```bash
streamlit run frontend/app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## 🧪 Testing

### Test the API
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I file an RTI application?"}'
```

### Test Streamlit
1. Open http://localhost:8501 in your browser
2. Enter a query like: "How do I file an RTI application?"
3. Click "Submit Query"
4. You should see the unified summary from the summarization agent

## 📋 System Architecture

The system now follows this flow:
1. **Intake Agent** - Normalizes query
2. **Classification Agent** (LLM) - Classifies legal domain
3. **Knowledge Retrieval Agent** - Retrieves statutes
4. **Case Similarity Agent** (LLM) - Finds similar cases
5. **Reasoning Agent** (LLM) - Generates legal reasoning
6. **Recommendation Agent** (LLM) - Generates civic actions
7. **Ethics Agent** (LLM) - Validates safety
8. **Memory Agent** - Stores case memory
9. **Summarization Agent** (LLM) - **Generates unified final response**

## 🔍 Troubleshooting

### API not responding
- Check if Qdrant is running: `docker ps | grep qdrant`
- Check API logs for errors
- Verify GROQ_API_KEY is set in .env

### Streamlit shows errors
- Make sure API is running on port 8000
- Check browser console for errors
- Verify the API endpoint: `curl http://localhost:8000/api/v1/health`

### No unified summary displayed
- Check if summarization agent is working (check API logs)
- Verify all previous agents completed successfully
- Check if LLM (Groq) is accessible

## 📝 Notes

- All agents now use LLM first, with fallbacks for reliability
- The summarization agent collects outputs from all agents
- The unified summary is the primary response shown in Streamlit
- Legacy format (explanation) is still supported for backward compatibility
