# NyayaAI Setup Guide

## ⚡ Quick Start (5 minutes)

If you already have Docker and Python 3.11+ installed:

```bash
# 1. Navigate to project
cd e:\Hackathons\Convolve\nyayaai

# 2. Start Qdrant in Docker
docker compose up -d qdrant

# 3. Create and activate virtual environment
python -m venv myenv
myenv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 6. Initialize database & Ingest Real Data (NEW)
python database/ingest_multimodal.py
# Press '1' to ingest real legal data (Acts, Cases, Forms, Videos)

# 7. Run everything! (Open 2 terminals)
Terminal 1: python main.py
Terminal 2: streamlit run frontend/app.py

# Done! Access at http://localhost:8501
```

For detailed instructions, see the complete guide below.

---

## Prerequisites
1. **Docker & Docker Compose** - For running Qdrant
2. **Python 3.11+** - For running the application
3. **Groq API Key** - For LLM inference (cloud-based, free tier available)
   - Sign up at: https://console.groq.com
   - Get your API key from the dashboard

## Step-by-Step Setup

### 1. Get Groq API Key

1. Visit https://console.groq.com and sign up
2. Navigate to API Keys section
3. Create a new API key
4. Copy the API key (you'll need it in Step 4)

### 2. Start Qdrant (Docker)

**Make sure Docker is running**, then:

```bash
cd e:\Hackathons\Convolve\nyayaai
docker compose up -d qdrant
```

**Note**: If you get "command not found", try `docker-compose` (with hyphen) for older Docker versions.

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

Expected response:
```json
{"title": "Qdrant", "version": "..."}
```

### 3. Set Up Python Environment

```bash
# Navigate to project
cd e:\Hackathons\Convolve\nyayaai

# Create virtual environment (if not already created)
python -m venv myenv

# Activate virtual environment
myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 4. Configure Environment Variables

**Create/Update `.env` file in the project root:**

```bash
# Windows (PowerShell)
echo "GROQ_API_KEY=your_actual_groq_api_key_here" > .env
```

Or manually create `.env` file with:
```
GROQ_API_KEY=your_actual_groq_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

**Important**: Replace `your_actual_groq_api_key_here` with your actual Groq API key from Step 1.

### 5. Initialize & Ingest Real Data (Recommended)

This single script creates the new `multimodal_legal_data` collection and ingests real Indian legal documents.

```bash
# Ensure virtual environment is activated
myenv\Scripts\activate

# Run the multimodal ingestion script
python database/ingest_multimodal.py
```

It will prompt you:
```
Choose data source:
1. Real legal data (India Code, Landmark Cases, Forms, Videos)
2. Sample multimodal data

Enter choice (1 or 2, default=1): 1
```

**Choose '1'** to fetch and store:
- **Acts**: RTI, Consumer Protection, CrPC, IPC
- **Cases**: Landmark judgments (Kesavananda, Vishaka)
- **Forms**: Official templates (RTI, FIR, Consumer Complaint)
- **Videos**: Educational content descriptions

Expected output:
```
INFO: ✓ Ingested [text]: Right to Information Act, 2005 - Key Sections
INFO: ✓ Ingested [video]: How to File an FIR - Video Guide
...
INFO: ✓ Ingested 18/18 multimodal documents
INFO: ✅ Multimodal ingestion complete!
```

### 6. Initialize Legacy Collections (Optional)

If you plan to use the legacy multi-agent pipeline (not recommended for simple use), run:

```bash
python -m database.setup_collections
python -m database.ingest_sample_data
```


### 7. (Optional) Extend Data Using Connectors

NyayaAI includes specialized connectors to fetch additional legal data from various sources.

#### Available Connectors:
- **indiacode_connector**: Fetch Indian acts/statutes from IndiaCode
- **supremecourt_connector**: Fetch Supreme Court of India judgments  
- **data_gov_connector**: Ingest datasets from Data.gov.in
- **lawcommission_connector**: Ingest Law Commission reports
- **worldlii_connector**: Ingest WorldLII/IndianLII cases

#### Example Usage:

```bash
# Ingest from IndiaCode
python -c "from connectors.indiacode_connector import ingest_act_from_url; ingest_act_from_url('https://www.indiacode.nic.in/...', collection_name='statutes_vectors')"

# Ingest from Supreme Court
python -c "from connectors.supremecourt_connector import ingest_judgment; ingest_judgment('https://main.sci.gov.in/...', collection_name='case_law_vectors')"
```

**Note**: These are optional. The system includes sample data and will work with fallback responses if needed.

### 8. Start Everything (Complete Guide)

Now you're ready to run the entire system! Here are all the commands you need.

#### Terminal 1: Start Qdrant (Docker)
```bash
cd e:\Hackathons\Convolve\nyayaai
docker compose up qdrant
```

Wait for output like:
```
qdrant-1  | ... Qdrant started on ...
```

#### Terminal 2: Start Backend API
```bash
cd e:\Hackathons\Convolve\nyayaai
myenv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

Wait for output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

#### Terminal 3: Start Frontend (Streamlit)
```bash
cd e:\Hackathons\Convolve\nyayaai
myenv\Scripts\activate
streamlit run frontend/app.py
```

Wait for output showing:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://...
```

#### Now Access the Application:
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Qdrant Console**: http://localhost:6333

You're all set! Start asking legal questions in the frontend.

## Complete End-to-End Testing Guide

This guide helps you verify the entire pipeline: data ingestion → vector storage → retrieval → agentic reasoning.

### Test Phase 1: Verify Vector Database Setup

**1. Check Qdrant Connection:**
```bash
curl http://localhost:6333/health
```

Expected response:
```json
{
  "title": "Qdrant",
  "version": "..."
}
```

**2. Check Collections Created:**
```bash
curl http://localhost:6333/collections
```

Expected collections:
```json
{
  "result": {
    "collections": [
      {"name": "legal_taxonomy_vectors"},
      {"name": "statutes_vectors"},
      {"name": "case_law_vectors"},
      {"name": "case_similarity_vectors"}
    ]
  }
}
```

**3. Verify Data Ingestion:**
```bash
curl http://localhost:6333/collections/legal_taxonomy_vectors | jq '.result'
```

You should see point count > 0. This confirms vectors are stored.

### Test Phase 2: Test Vector Retrieval

**Python Script to Test Retrieval:**

Create a file `test_retrieval.py` in the nyayaai directory:

```python
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding

# Get an embedding for a test query
query = "How do I file an RTI application?"
query_embedding = get_embedding(query)

# Search in the statutes collection
results = qdrant_manager.search(
    collection_name="statutes_vectors",
    query_vector=query_embedding,
    limit=5,
    score_threshold=0.5
)

print(f"Found {len(results)} results:")
for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result['score']:.4f}")
    print(f"   Payload: {result['payload']}")
    print()
```

Run it:
```bash
python test_retrieval.py
```

Expected output:
```
Found 3 results:
1. Score: 0.8532
   Payload: {'text': '...', 'source': '...'}
...
```

### Test Phase 3: Test Agentic Pipeline

**Complete Agent Flow Test:**

Create a file `test_agent_pipeline.py` in the nyayaai directory:

```python
import json
from core.agent_base import AgentInput
from agents.intake_agent import IntakeAgent
from agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.reasoning_agent import ReasoningAgent
from agents.recommendation_agent import RecommendationAgent

# Step 1: Intake Agent (Normalize the query)
print("=" * 60)
print("STEP 1: INTAKE AGENT (Query Normalization)")
print("=" * 60)

query = "How do I file an RTI application? What documents do I need?"
intake_input = AgentInput(query=query)
intake_agent = IntakeAgent()
intake_output = intake_agent.process(intake_input)

print(f"Original Query: {query}")
print(f"Normalized Query: {intake_output.result.get('normalized_query', query)}")
print(f"Classification: {intake_output.result.get('classification', 'N/A')}")
print()

# Step 2: Knowledge Retrieval Agent (Fetch relevant statutes)
print("=" * 60)
print("STEP 2: KNOWLEDGE RETRIEVAL AGENT")
print("=" * 60)

kr_input = AgentInput(query=intake_output.result.get('normalized_query', query))
kr_agent = KnowledgeRetrievalAgent()
kr_output = kr_agent.process(kr_input)

retrieved_docs = kr_output.result.get('documents', [])
print(f"Retrieved {len(retrieved_docs)} relevant documents:")
for i, doc in enumerate(retrieved_docs[:3], 1):  # Show first 3
    print(f"{i}. {doc.get('source', 'Unknown')} (Score: {doc.get('score', 'N/A')})")
print()

# Step 3: Reasoning Agent (Analyze the documents)
print("=" * 60)
print("STEP 3: REASONING AGENT")
print("=" * 60)

reasoning_input = AgentInput(
    query=query,
    context={"retrieved_documents": retrieved_docs}
)
reasoning_agent = ReasoningAgent()
reasoning_output = reasoning_agent.process(reasoning_input)

reasoning_result = reasoning_output.result
print(f"Analysis: {reasoning_result.get('reasoning', 'N/A')[:500]}...")
print()

# Step 4: Recommendation Agent (Provide actionable steps)
print("=" * 60)
print("STEP 4: RECOMMENDATION AGENT")
print("=" * 60)

rec_input = AgentInput(
    query=query,
    context={
        "reasoning": reasoning_result,
        "retrieved_documents": retrieved_docs
    }
)
rec_agent = RecommendationAgent()
rec_output = rec_agent.process(rec_input)

recommendations = rec_output.result.get('recommendations', [])
print(f"Recommendations: {len(recommendations)} steps")
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec}")
print()

print("=" * 60)
print("PIPELINE TEST COMPLETE")
print("=" * 60)
```

Run it:
```bash
python test_agent_pipeline.py
```

Expected output shows each agent working in sequence, transforming the query and providing recommendations.

### Test Phase 4: Test Full API

**1. Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**2. Single Query Test:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I file an RTI application?",
    "include_context": true
  }' | jq .
```

**3. Memory Operations:**
```bash
# Store case memory
curl -X POST http://localhost:8000/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE001",
    "user_id": "USER001",
    "information": "User asked about RTI. We provided basic guidance."
  }' | jq .

# Retrieve case memory
curl http://localhost:8000/api/v1/memory/retrieve/CASE001 | jq .
```

### Test Phase 5: Continuous Testing

**Demo Script (Comprehensive Test):**

```bash
# Make sure Qdrant is running
docker ps | grep qdrant

# Make sure you're in the nyayaai directory
cd e:\Hackathons\Convolve\nyayaai

# Run the demo
python demo_examples.py
```

## Verification Checklist

- [ ] Docker & Qdrant running: `docker ps | grep qdrant`
- [ ] Python environment activated: `where python` should show myenv path
- [ ] All dependencies installed: `pip list | grep -i groq`
- [ ] Environment variables configured: `echo %GROQ_API_KEY%`
- [ ] Groq API key is valid: Try the test below
- [ ] Collections created in Qdrant: Phase 1 Test 2
- [ ] Sample data ingested: Phase 1 Test 3  
- [ ] Vector retrieval working: Phase 2 Test passes
- [ ] Agent pipeline working: Phase 3 Test passes
- [ ] API responding: Phase 4 Test 1 passes
- [ ] Full demo completed: Phase 5 runs without errors

## Troubleshooting

### SSL/Connection Errors When Running Database Setup

**Problem**: `[SSL: WRONG_VERSION_NUMBER] wrong version number` or connection errors when running `python -m database.setup_collections`

**Root Cause**: Usually Qdrant is not running, or the client is trying to connect with wrong settings.

**Solution**:
```bash
# 1. Check if Qdrant is running
docker ps | findstr qdrant

# 2. If not running, start it
docker compose up -d qdrant

# 3. Wait 10-15 seconds for Qdrant to fully initialize
# 4. Verify connection
curl http://localhost:6333/health

# 5. Try again
python -m database.setup_collections

# If still failing, restart Qdrant
docker compose restart qdrant
python -m database.setup_collections
```

**Also check**: The `database/qdrant_client.py` should NOT pass `api_key` for local Qdrant. This has been fixed in the latest version.

### Groq API Issues

**Problem**: "Error: Invalid API Key" or "No such model"
**Solution**:
```bash
# Verify Groq API key is set correctly
echo %GROQ_API_KEY%

# Test Groq connection directly
python -c "
import os
from groq import Groq
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Say hello'}],
    model='mixtral-8x7b-32768'
)
print('✓ Groq API working:', response.choices[0].message.content)
"

# If that fails:
# 1. Check GROQ_API_KEY is correct: https://console.groq.com
# 2. Verify model name is active: https://console.groq.com/docs/models
# 3. Restart the backend: kill Python processes and restart
```

### Qdrant Connection Issues

**Problem**: Cannot connect to Qdrant
**Solution**:
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check Qdrant logs
docker logs nyayaai-qdrant

# Restart Qdrant
docker compose restart qdrant
# Or for older Docker: docker-compose restart qdrant
```

### Import Errors

**Problem**: Module not found errors
**Solution**:
```bash
# Ensure you're in the project root
cd nyayaai

# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Embedding Model Download

**Problem**: Slow first run (downloading model)
**Solution**: This is normal. The SentenceTransformers model downloads on first use (~90MB).

## Production Deployment

### Docker Deployment (Future)

```bash
# Build image
docker build -t nyayaai:latest .

# Run container
docker run -p 8000:8000 nyayaai:latest
```

### Environment Variables

Key environment variables for production:
- `GROQ_API_KEY` - Your Groq API key (required)
- `QDRANT_HOST` - Qdrant host (default: localhost)
- `QDRANT_PORT` - Qdrant port (default: 6333)
- `QDRANT_API_KEY` - Qdrant API key (if using cloud Qdrant)
- `DEBUG` - Set to `False` in production
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING)

## Next Steps

1. **Expand Legal Corpus**: Add more statutes, cases, and processes
2. **Customize Agents**: Modify agent behavior as needed
3. **Add Languages**: Extend to Hindi and regional languages
4. **Deploy**: Set up production deployment
5. **Monitor**: Add monitoring and logging

## Support

For issues or questions:
- Check documentation in `docs/` folder
- Review architecture in `docs/architecture.md`
- See ethics and limitations in `docs/ETHICS_AND_LIMITATIONS.md`
