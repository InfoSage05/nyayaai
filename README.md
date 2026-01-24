# NyayaAI - Multi-Agent Legal Rights & Civic Access System

## Problem Statement

Legal rights and civic remedies in India exist on paper, but are inaccessible in practice due to legal complexity, language barriers, and procedural opacity. Citizens cannot discover applicable laws, understand them, or navigate civic/legal processes.

## Solution Overview

NyayaAI is a multi-agent AI system that uses Qdrant vector search to provide:
- **Search**: Semantic retrieval of legal statutes, case law, and civic processes
- **Memory**: Long-term case memory and user interaction history
- **Recommendations**: Context-aware civic action recommendations

## Architecture

The system now offers two pipelines:

1.  **Simplified Pipeline (Recommended)**:
    *   **Architecture**: RAG (Qdrant) + Web Search (Tavily) + ONE LLM Call (Groq)
    *   **Features**:
        *   **Multimodal Retrieval**: Searches Text, PDF, Images, Audio, Video, Code, and Forms
        *   **Fast**: Single LLM call ensures low latency (~2-3s)
        *   **Reliable**: No complex agent chaining failures
        *   **Clear**: Displays source-grounded answers directly

2.  **Legacy Multi-Agent Pipeline (Advanced)**:
    *   Complex LangGraph orchestration with 8 specialized agents
    *   Best for deep research requiring multi-step reasoning

## Key Features

*   **Multimodal Search**: Retrieve laws, cases, forms, and educational videos in one go.
*   **Real Legal Data**: Includes statutes (India Code), landmark judgments (Supreme Court), and official forms.
*   **Simple & Fast**: Designed for immediate, helpful answers without agent overhead.
*   **Semantic Search**: Qdrant vector database understands legal context.
*   ** Civic Guidance**: Provides practical "Next Steps" alongside legal info.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Pipeline**: Simplified RAG + Multi-Modal Qdrant
- **Vector DB**: Qdrant (Docker) - Stores Text, Audio, Video metadata
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: Groq (Llama3-70b/8b) - Fast inference
- **Web Search**: Tavily API
- **Frontend**: Streamlit

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
