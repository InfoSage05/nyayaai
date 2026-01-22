# NyayaAI - Project Summary

## Overview

NyayaAI is a **multi-agent AI system** that addresses the problem of legal rights and civic remedies accessibility in India. The system uses **Qdrant vector search** to provide search, memory, and recommendations for legal and civic information.

## Problem Addressed

**Societal Challenge**: Legal rights and civic remedies in India exist on paper, but are inaccessible in practice due to:
- Legal complexity
- Language barriers  
- Procedural opacity

## Solution

A multi-agent system that:
1. **Searches** across legal corpus** using semantic similarity
2. **Remembers** past queries and cases for context
3. **Recommends** actionable civic steps

## Key Features

### ✅ Multi-Agent Architecture
- 8 specialized agents with single responsibilities
- No overlapping duties
- Explicit inputs and outputs
- Retrieval-first behavior (no hallucination)

### ✅ Qdrant Integration
- 6 Qdrant collections for different data types
- Semantic search with metadata filtering
- Long-term memory storage
- Real-time retrieval

### ✅ Evidence-Based Outputs
- All outputs grounded in retrieved documents
- Traceable reasoning paths
- Citations to statutes and cases
- Clear indication of what is unknown

### ✅ Safety & Ethics
- No legal advice provided
- No litigation strategies
- Automatic safety disclaimers
- Ethics validation before output

## Deliverables

### ✅ Code (Reproducible)
- Complete end-to-end system
- Clear setup instructions
- Docker Compose for Qdrant
- Sample data ingestion

### ✅ Documentation
- README with setup guide
- Architecture documentation
- System design document
- Ethics and limitations document

### ✅ Demo
- Sample queries
- Demo script
- API endpoints
- Streamlit frontend

## Project Structure

```
nyayaai/
├── agents/              # 8 agent implementations
├── core/               # Orchestrator (LangGraph)
├── database/           # Qdrant setup and utilities
├── api/                # FastAPI endpoints
├── utils/              # Embeddings and LLM utilities
├── frontend/           # Streamlit UI
├── docs/               # Documentation
├── data/               # Sample data
└── config/             # Configuration
```

## Technology Stack

- **Orchestration**: LangGraph
- **Vector DB**: Qdrant (Docker)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (Llama 3 / Mistral)
- **API**: FastAPI
- **Frontend**: Streamlit
- **Language**: Python 3.11+

## Qdrant Collections

1. `legal_taxonomy_vectors` - Legal domain taxonomy
2. `statutes_vectors` - Legal statutes and acts
3. `case_law_vectors` - Case law and judgments
4. `civic_process_vectors` - Civic processes
5. `case_memory_vectors` - Long-term case memory
6. `user_interaction_memory` - User interaction history

## Agents

1. **Intake & Normalization Agent** - Processes queries
2. **Legal Domain Classification Agent** - Classifies domains
3. **Legal Knowledge Retrieval Agent** - Retrieves statutes
4. **Case Similarity Agent** - Finds similar cases
5. **Legal Reasoning Agent** - Generates explanations
6. **Civic Action Recommendation Agent** - Recommends actions
7. **Ethics & Safety Agent** - Validates outputs
8. **Long-Term Case Memory Agent** - Manages memory

## Quick Start

1. Install Ollama and pull model: `ollama pull llama3`
2. Start Qdrant: `docker-compose up -d qdrant`
3. Install dependencies: `pip install -r requirements.txt`
4. Setup collections: `python -m nyayaai.database.setup_collections`
5. Ingest data: `python -m nyayaai.database.ingest_sample_data`
6. Start API: `uvicorn nyayaai.api.main:app --reload`

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## Evaluation Criteria Alignment

### ✅ Correct and Meaningful Use of Qdrant
- 6 collections with proper schemas
- Semantic search with metadata filtering
- Memory storage and retrieval
- Real-time updates

### ✅ Quality of Retrieval and Memory Design
- Retrieval-first approach
- Long-term memory storage
- Similarity-based case retrieval
- User interaction tracking

### ✅ Societal Relevance and Impact
- Addresses real-world problem
- Legal rights accessibility
- Civic process navigation
- Evidence-based information

### ✅ System Clarity and Robustness
- Clear agent responsibilities
- Error handling
- Logging and monitoring
- Documentation

### ✅ Thoughtful Documentation and Reasoning
- Architecture documentation
- System design document
- Ethics and limitations
- Setup guide

### ✅ Creativity Without Sacrificing Correctness
- Multi-agent architecture
- Retrieval-bounded reasoning
- Ethics validation
- Memory management

## Limitations

- Limited to available legal corpus
- Primarily English language
- Requires Ollama for LLM
- Sample data for demonstration

## Future Enhancements

- Hindi and regional language support
- Expanded legal corpus
- Legal document parsing
- Form filling assistance
- Legal aid integration

## License

MIT License - Open Source

## Contact

For questions or issues, see documentation in `docs/` folder.

---

**Version**: 1.0.0
**Created for**: Convolve 4.0 - Qdrant Challenge
**Date**: 2024
