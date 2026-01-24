# NyayaAI - Multi-Agent Legal Rights & Civic Access System

## Problem Statement

Legal rights and civic remedies in India exist on paper, but are inaccessible in practice due to legal complexity, language barriers, and procedural opacity. Citizens cannot discover applicable laws, understand them, or navigate civic/legal processes.

## Solution Overview

NyayaAI is a legal AI assistant powered by **Adaptive RAG** (Retrieval-Augmented Generation) that provides:
- **Hybrid Search**: Combines internal vector database (Qdrant) + real-time web search (Tavily)
- **Evidence-Based Answers**: All responses cite sources from retrieved documents
- **Semantic Memory**: Long-term conversation context using vector similarity
- **Multimodal Support**: Processes text, PDFs, images, audio, video, code, and legal forms

## Architecture

### Adaptive RAG Pipeline (Default)

```
Query → Embedding → Qdrant Search → Web Search (Tavily) → Combined Context → LLM (Groq) → Response
```

**Key Features:**
- **Parallel Retrieval**: Database AND web search run together (not fallback)
- **Smart Collection Search**: Tries multiple collections (`multimodal_legal_data`, `legal_taxonomy_vectors`, etc.)
- **Low Latency**: Single LLM call (~2-3s response time)
- **Source Transparency**: Clearly labels database vs web sources
- **Conversation Memory**: Stores interactions for context continuity

## Key Features

*   **Adaptive RAG**: Combines internal knowledge + web search for comprehensive answers
*   **Real Legal Data**: India Code statutes, Supreme Court judgments, RTI forms
*   **Multimodal Ingestion**: Supports text, PDF, images, audio, video, and code
*   **Evidence-Based Outputs**: LLM responses cite specific sources
*   **Semantic Search**: Qdrant vector database with 384-dim embeddings
*   **Civic Guidance**: Practical next steps alongside legal information

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Pipeline**: Adaptive RAG with parallel retrieval
- **Vector DB**: Qdrant (Docker) - 384-dim embeddings (MiniLM)
- **LLM**: Groq (Llama3-70b/8b) - Fast cloud inference
- **Web Search**: Tavily API - Real-time legal information
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Frontend**: Streamlit
- **Data Connectors**: India Code, Supreme Court, Data.gov.in

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Groq API and Tavily Search API

### Setup

1. **Navigate to project**:
```bash
cd nyayaai
```

2. **Install Ollama and pull model**:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3
```

3. **Start Qdrant**:
```bash
docker compose up -d qdrant
# Or for older Docker: docker-compose up -d qdrant
```

4. **Set up Python environment**:
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

5. **Initialize Qdrant collections**:
```bash
python -m nyayaai.database.setup_collections
```

6. **Ingest sample data**:
```bash
python -m nyayaai.database.ingest_sample_data
```

7. **Start the API**:
```bash
uvicorn nyayaai.api.main:app --reload
```

8. **Start the frontend** (optional):
```bash
streamlit run nyayaai/frontend/app.py
```

**For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

## Qdrant Collections

1. `multimodal_legal_data` - Main collection with all ingested legal data (text, PDF, audio, video, forms)
2. `legal_taxonomy_vectors` - Legal domain taxonomy
3. `user_interaction_memory` - Semantic conversation memory for context

## API Endpoints

- `POST /api/v1/query` - Submit a legal query
- `GET /api/v1/memory/{case_id}` - Retrieve case memory
- `GET /api/v1/health` - Health check

## Ethics & Limitations

### Important Disclaimers

- **Not Legal Advice**: This system provides information only, not legal advice
- **No Litigation Strategy**: The system does not provide litigation strategies
- **Retrieval-Bounded**: All outputs are grounded in retrieved documents
- **Bias Awareness**: The system may reflect biases in training data
- **Jurisdiction**: Primarily designed for Indian legal system

### Known Limitations

- Limited to available legal corpus
- May not cover all legal domains
- Language support primarily English (Hindi extension planned)
- Requires internet for Ollama LLM access

## Project Structure

```
nyayaai/
├── agents/          # All agent implementations
├── core/            # Core orchestration logic
├── database/        # Qdrant setup and utilities
├── api/             # FastAPI endpoints
├── utils/           # Utility functions
├── data/            # Sample data files
├── frontend/        # Streamlit UI
├── config/          # Configuration files
└── tests/           # Unit tests
```

## License

MIT License - Open Source

## Contributing

This is a hackathon project for Convolve 4.0 - Qdrant Challenge.
