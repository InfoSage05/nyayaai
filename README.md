# NyayaAI - Multi-Agent Legal Rights & Civic Access System

## Problem Statement

Legal rights and civic remedies in India exist on paper, but are inaccessible in practice due to legal complexity, language barriers, and procedural opacity. Citizens cannot discover applicable laws, understand them, or navigate civic/legal processes.

## Solution Overview

NyayaAI is a multi-agent AI system that uses Qdrant vector search to provide:
- **Search**: Semantic retrieval of legal statutes, case law, and civic processes
- **Memory**: Long-term case memory and user interaction history
- **Recommendations**: Context-aware civic action recommendations

## Architecture

The system consists of 8 specialized agents:

1. **Intake & Normalization Agent**: Processes and normalizes user queries
2. **Legal Domain Classification Agent**: Classifies queries into legal domains
3. **Legal Knowledge Retrieval Agent**: Retrieves relevant statutes and laws
4. **Case Similarity Agent**: Finds similar past cases
5. **Legal Reasoning Agent**: Provides retrieval-bounded legal reasoning
6. **Civic Action Recommendation Agent**: Recommends actionable civic steps
7. **Ethics & Safety Agent**: Monitors outputs for safety and ethics
8. **Long-Term Case Memory Agent**: Manages persistent case memory

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Orchestration**: LangGraph
- **Vector DB**: Qdrant (Docker)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (Llama 3 / Mistral)
- **Frontend**: Streamlit (minimal)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Ollama installed locally

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

1. `legal_taxonomy_vectors` - Legal domain taxonomy
2. `statutes_vectors` - Legal statutes and acts
3. `case_law_vectors` - Case law and judgments
4. `civic_process_vectors` - Civic processes and procedures
5. `case_memory_vectors` - Long-term case memory
6. `user_interaction_memory` - User interaction history

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
