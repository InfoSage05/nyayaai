# NyayaAI Architecture

## System Overview

NyayaAI is a multi-agent AI system that uses Qdrant vector search to provide legal information and civic action recommendations. The system follows a retrieval-first approach, ensuring all outputs are grounded in retrieved documents.

## Architecture Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI / Streamlit Frontend               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Orchestrator (LangGraph)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Agent Workflow Pipeline                  │   │
│  └──────────────────────────────────────────────────┘   │
└──────┬──────┬──────┬──────┬──────┬──────┬──────┬────────┘
       │      │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼      ▼
   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
   │Intake│ │Class│ │Know │ │Case │ │Reas │ │Rec  │ │Ethic│
   │Agent │ │Agent│ │Agent│ │Agent│ │Agent│ │Agent│ │Agent│
   └──┬───┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
      │        │       │       │       │       │       │
      └────────┴───────┴───────┴───────┴───────┴───────┘
                       │
                       ▼
              ┌────────────────┐
              │  Memory Agent  │
              └────────┬───────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    Qdrant Vector DB                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │legal_taxonomy│  │  statutes_   │  │  case_law_   │  │
│  │   _vectors   │  │   vectors    │  │   vectors    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ civic_process│  │ case_memory_ │  │user_interact │  │
│  │   _vectors   │  │   vectors    │  │ion_memory    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Embeddings    │
              │ (SentenceTrans│
              │   formers)      │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Ollama LLM    │
              │  (Llama 3)     │
              └────────────────┘
```

## Agent Responsibilities

### 1. Intake & Normalization Agent
- **Input**: Raw user query
- **Output**: Normalized query, embedding
- **Qdrant**: None (preprocessing only)

### 2. Legal Domain Classification Agent
- **Input**: Normalized query + embedding
- **Output**: Legal domain(s), primary domain
- **Qdrant**: `legal_taxonomy_vectors`

### 3. Legal Knowledge Retrieval Agent
- **Input**: Query + domain classification
- **Output**: Relevant statutes and acts
- **Qdrant**: `statutes_vectors`

### 4. Case Similarity Agent
- **Input**: Query + domain classification
- **Output**: Similar past cases
- **Qdrant**: `case_law_vectors`

### 5. Legal Reasoning Agent
- **Input**: Query + retrieved statutes + cases
- **Output**: Legal explanation (retrieval-bounded)
- **Qdrant**: None (uses LLM with retrieved context)
- **LLM**: Ollama (Llama 3)

### 6. Civic Action Recommendation Agent
- **Input**: Query + legal reasoning
- **Output**: Actionable civic steps
- **Qdrant**: `civic_process_vectors`

### 7. Ethics & Safety Agent
- **Input**: Final output
- **Output**: Safety validation, disclaimers
- **Qdrant**: None (validation only)

### 8. Long-Term Case Memory Agent
- **Input**: Complete query context
- **Output**: Stored case memory, case ID
- **Qdrant**: `case_memory_vectors`, `user_interaction_memory`

## Data Flow

1. **User Query** → Intake Agent (normalization)
2. **Normalized Query** → Classification Agent (domain identification)
3. **Query + Domain** → Knowledge Agent (statute retrieval)
4. **Query + Domain** → Case Agent (case retrieval)
5. **Query + Statutes + Cases** → Reasoning Agent (explanation generation)
6. **Query + Explanation** → Recommendation Agent (civic actions)
7. **Final Output** → Ethics Agent (safety check)
8. **Complete Context** → Memory Agent (storage)

## Qdrant Collections

### 1. legal_taxonomy_vectors
- **Purpose**: Legal domain taxonomy
- **Vector Size**: 384 (all-MiniLM-L6-v2)
- **Payload**: domain, description, text

### 2. statutes_vectors
- **Purpose**: Legal statutes and acts
- **Vector Size**: 384
- **Payload**: title, section, act_name, content, domain, jurisdiction

### 3. case_law_vectors
- **Purpose**: Case law and judgments
- **Vector Size**: 384
- **Payload**: case_name, court, year, summary, key_points, citation, domain

### 4. civic_process_vectors
- **Purpose**: Civic processes and procedures
- **Vector Size**: 384
- **Payload**: action, description, steps, authority, required_documents, timeline, cost

### 5. case_memory_vectors
- **Purpose**: Long-term case memory
- **Vector Size**: 384
- **Payload**: case_id, query, domains, statutes, cases, explanation, recommendations, timestamp

### 6. user_interaction_memory
- **Purpose**: User interaction history
- **Vector Size**: 384
- **Payload**: user_id, query, interaction_type, timestamp, full context

## Retrieval Strategy

- **Similarity Threshold**: 0.4-0.5 (configurable per collection)
- **Top-K**: 3-5 documents per retrieval
- **Metadata Filtering**: By domain, jurisdiction
- **Hybrid Search**: Semantic (vector) + metadata filtering

## Safety & Ethics

- **No Legal Advice**: System explicitly refuses to provide legal advice
- **No Litigation Strategy**: Does not suggest litigation strategies
- **Retrieval-Bounded**: All outputs grounded in retrieved documents
- **Disclaimers**: Automatic safety disclaimers added to outputs
- **Ethics Validation**: All outputs validated before presentation

## Technology Stack

- **Orchestration**: LangGraph
- **Vector DB**: Qdrant (Docker)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (Llama 3 / Mistral)
- **API**: FastAPI
- **Frontend**: Streamlit
- **Language**: Python 3.11+
