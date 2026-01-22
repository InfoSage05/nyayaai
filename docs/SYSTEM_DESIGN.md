# NyayaAI System Design

## Problem Statement

Legal rights and civic remedies in India exist on paper, but are inaccessible in practice due to:
- **Legal Complexity**: Laws are written in complex legal language
- **Language Barriers**: Many citizens don't understand English legal terminology
- **Procedural Opacity**: Citizens don't know how to navigate legal/civic processes

## Solution Design

NyayaAI addresses this through a **multi-agent AI system** that:
1. **Searches** across legal corpus using semantic similarity
2. **Remembers** past queries and cases for context
3. **Recommends** actionable civic steps

## Why Qdrant is Critical

### 1. Multimodal Legal Data
- **Text**: Statutes, case law, processes
- **Metadata**: Jurisdiction, domain, dates, citations
- **Future**: Images (legal documents), audio (court recordings)

### 2. Semantic Search Requirements
- **Similarity Search**: Find similar cases, statutes
- **Domain Filtering**: Filter by legal domain
- **Hybrid Search**: Combine semantic + keyword + metadata

### 3. Long-Term Memory
- **Case Memory**: Store and retrieve past queries
- **User History**: Track user interactions
- **Evolving Knowledge**: Update and reinforce memory

### 4. Performance Requirements
- **Low Latency**: Real-time retrieval (<100ms)
- **Scalability**: Handle thousands of queries
- **Consistency**: Strong consistency for legal data

## Multi-Agent Architecture Rationale

### Why Multiple Agents?

1. **Separation of Concerns**: Each agent has a single responsibility
2. **Modularity**: Easy to modify or replace individual agents
3. **Traceability**: Clear reasoning path through agents
4. **Retrieval-First**: Each agent retrieves before reasoning

### Agent Responsibilities

| Agent | Responsibility | Qdrant Collection | Retrieval Type |
|-------|---------------|-------------------|----------------|
| Intake | Normalize query | None | Preprocessing |
| Classification | Identify domain | legal_taxonomy_vectors | Semantic |
| Knowledge | Retrieve statutes | statutes_vectors | Semantic + Filter |
| Case Similarity | Find similar cases | case_law_vectors | Semantic + Filter |
| Reasoning | Generate explanation | None | LLM (bounded) |
| Recommendation | Suggest actions | civic_process_vectors | Semantic + Filter |
| Ethics | Validate safety | None | Validation |
| Memory | Store/retrieve | case_memory_vectors, user_interaction_memory | Semantic |

## Retrieval Strategy

### 1. Semantic Search
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Distance Metric**: Cosine similarity
- **Threshold**: 0.4-0.5 (configurable per collection)

### 2. Metadata Filtering
- **Domain Filtering**: Filter by legal domain
- **Jurisdiction Filtering**: Filter by jurisdiction (India, state)
- **Date Filtering**: Filter by date ranges (future)

### 3. Hybrid Search
- **Semantic**: Vector similarity
- **Keyword**: Metadata matching
- **Combined**: Weighted combination

## Memory Design

### Case Memory
- **Purpose**: Store complete query context
- **Storage**: case_memory_vectors collection
- **Retrieval**: Semantic search for similar past cases
- **Updates**: New cases added, old cases can be updated

### User Interaction Memory
- **Purpose**: Track user interactions
- **Storage**: user_interaction_memory collection
- **Retrieval**: Search by user ID or query similarity
- **Privacy**: User IDs can be anonymous

## Evidence-Based Outputs

### Retrieval Grounding
- **Statutes Cited**: All statutes referenced are retrieved
- **Cases Cited**: All cases referenced are retrieved
- **Recommendations**: All recommendations are retrieved
- **No Hallucination**: LLM only uses retrieved context

### Traceability
- **What Retrieved**: Shows retrieved documents
- **Why Retrieved**: Shows similarity scores
- **How Used**: Shows how documents influenced output
- **What Missing**: Indicates when information is unavailable

## Safety & Ethics

### 1. No Legal Advice
- **System Behavior**: Provides information, not advice
- **Validation**: Ethics agent checks for advice language
- **Disclaimers**: Automatic disclaimers added

### 2. Retrieval-Bounded Reasoning
- **Constraint**: LLM only uses retrieved documents
- **Validation**: Reasoning agent validates retrieval usage
- **Fallback**: Returns "no information available" if no retrieval

### 3. Bias Mitigation
- **Awareness**: System acknowledges potential biases
- **Transparency**: Shows sources and reasoning
- **Regular Updates**: Corpus updates recommended

## Scalability Considerations

### Horizontal Scaling
- **Qdrant**: Can scale horizontally
- **API**: Stateless, can scale with load balancer
- **Agents**: Stateless, can scale independently

### Performance Optimization
- **Embedding Caching**: Cache embeddings for common queries
- **Collection Sharding**: Shard large collections
- **Index Optimization**: Optimize Qdrant indexes

## Future Enhancements

### 1. Multimodal Support
- **Images**: Legal documents, forms
- **Audio**: Court recordings, legal proceedings
- **Video**: Legal education videos

### 2. Language Support
- **Hindi**: Full Hindi support
- **Regional Languages**: Tamil, Telugu, Bengali, etc.
- **Translation**: Automatic translation of legal documents

### 3. Advanced Features
- **Legal Document Parsing**: Extract information from PDFs
- **Form Filling**: Help fill legal forms
- **Legal Aid Integration**: Connect with legal aid organizations

## Deployment Architecture

### Development
- **Local Qdrant**: Docker container
- **Local Ollama**: Local installation
- **Local API**: FastAPI development server

### Production (Recommended)
- **Qdrant Cloud**: Managed Qdrant instance
- **Ollama Server**: Dedicated Ollama server
- **API Server**: Deployed FastAPI application
- **Load Balancer**: For high availability
- **Monitoring**: Logging and metrics

## Evaluation Metrics

### Retrieval Quality
- **Precision**: Relevant documents retrieved
- **Recall**: All relevant documents found
- **F1 Score**: Balance of precision and recall

### System Performance
- **Latency**: Query processing time
- **Throughput**: Queries per second
- **Accuracy**: Correct information provided

### User Experience
- **Clarity**: Explanation clarity
- **Actionability**: Recommendation usefulness
- **Trust**: User trust in system

---

**Version**: 1.0.0
**Last Updated**: 2024
