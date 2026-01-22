# NyayaAI - Detailed Architecture & Workflow Guide

## 🎯 Executive Summary

**NyayaAI** is a **multi-agent AI system** designed to democratize access to legal rights and civic remedies in India. It addresses the critical problem that legal information, while technically available, remains practically inaccessible due to complexity, language barriers, and procedural opacity.

### The Core Problem
- Citizens don't know what laws apply to them
- Legal language is complex and inaccessible
- Civic processes are opaque and confusing
- No guidance on actionable next steps

### The Solution
A sophisticated **8-agent orchestrated system** that:
1. **Understands** what users are asking (Intake Agent)
2. **Classifies** the legal domain (Classification Agent)
3. **Searches** relevant laws (Knowledge Agent)
4. **Finds** similar past cases (Case Agent)
5. **Reasons** through the information (Reasoning Agent)
6. **Recommends** actionable steps (Recommendation Agent)
7. **Validates** safety and ethics (Ethics Agent)
8. **Remembers** for future use (Memory Agent)

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERACTION LAYER                      │
├──────────────────────────┬──────────────────────────────────────┤
│     FastAPI REST API     │      Streamlit Frontend UI           │
│  (Production Use)        │     (Demo/Testing)                   │
└──────────────────────────┴──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                           │
│                    (LangGraph Workflow)                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          Agent State Management                         │    │
│  │  - Tracks query context                                 │    │
│  │  - Passes data between agents                           │    │
│  │  - Collects agent outputs                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
     │        │        │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│ Intake ││ Class- ││ Know-  ││ Case   ││ Reason ││ Civic  │
│ Agent  ││ ify    ││ ledge  ││ Sim.   ││ Agent  ││ Rec.   │
│        ││ Agent  ││ Agent  ││ Agent  ││        ││ Agent  │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
                                                      │
                                                      ▼
                                                 ┌──────────┐
                                                 │  Ethics  │
                                                 │  Agent   │
                                                 └────┬─────┘
                                                      │
                                                      ▼
                                                 ┌──────────┐
                                                 │  Memory  │
                                                 │  Agent   │
                                                 └──────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RETRIEVAL LAYER                               │
│                  (Vector Database)                              │
│                      Qdrant                                     │
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  legal_      │  statutes_   │  case_law_   │ civic_       │  │
│  │  taxonomy    │  vectors     │  vectors     │ process_     │  │
│  │  _vectors    │              │              │ _vectors     │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                 │
│  ┌──────────────┬──────────────┐                                │
│  │ case_memory_ │user_interact-│                                │
│  │ vectors      │ion_memory    │                                │
│  └──────────────┴──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI LAYER                                      │
├──────────────────────────┬──────────────────────────────────────┤
│  Embeddings Model        │         LLM                          │
│  (SentenceTransformers)  │     (Ollama)                         │
│  all-MiniLM-L6-v2        │     Llama 3 / Mistral                │
│  384 dimensions          │     Local inference                  │
└──────────────────────────┴──────────────────────────────────────┘
```

---

## 📊 Detailed Data Flow Diagram

```
┌─────────────┐
│   USER      │
│   QUERY     │
│             │
│"What are my │
│ rights when │
│ my landlord │
│ evicts me?" │
└──────┬──────┘
       │
       ▼ [Raw Query String]
┌──────────────────────────────────────────────────────────┐
│  AGENT 1: INTAKE & NORMALIZATION                         │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                 │
│    • Raw user query                                      │
│  PROCESS:                                                │
│    1. Clean and normalize text                           │
│    2. Convert to lowercase                               │
│    3. Generate embedding (384-dim vector)                │
│  OUTPUTS:                                                │
│    • normalized_query: "what are my rights when my..."   │
│    • embedding: [0.234, -0.156, 0.872, ...]              │
│  RETRIEVAL: None (Preprocessing only)                    │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Query + Embedding]
┌──────────────────────────────────────────────────────────┐
│  AGENT 2: LEGAL DOMAIN CLASSIFICATION                    │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Normalized query                                     │
│    • Query embedding                                      │
│  PROCESS:                                                 │
│    1. Search legal_taxonomy_vectors collection            │
│    2. Find similar legal domains (cosine similarity)      │
│    3. Use keyword matching as fallback                    │
│  RETRIEVAL:                                               │
│    Collection: legal_taxonomy_vectors                    │
│    Threshold: 0.4                                         │
│    Top-K: 3 results                                       │
│  OUTPUTS:                                                 │
│    • domains: ["property_law", "tenant_rights"]          │
│    • primary_domain: "property_law"                       │
│    • confidence: 0.85                                     │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Query + Domain + Embedding]
┌──────────────────────────────────────────────────────────┐
│  AGENT 3: LEGAL KNOWLEDGE RETRIEVAL                      │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Query + embedding                                    │
│    • Primary domain (from Classification)                 │
│  PROCESS:                                                 │
│    1. Search statutes_vectors with domain filter          │
│    2. Retrieve top statute matches                        │
│    3. Extract title, section, content, jurisdiction       │
│  RETRIEVAL:                                               │
│    Collection: statutes_vectors                          │
│    Filter: domain = "property_law"                        │
│    Threshold: 0.5                                         │
│    Top-K: 5 results                                       │
│  OUTPUTS:                                                 │
│    statutes: [                                            │
│      {                                                     │
│        title: "Landlord & Tenant Act...",                │
│        section: "Section 21",                             │
│        content: "A landlord must provide...",             │
│        act_name: "Rent Control Act",                      │
│        jurisdiction: "India/State",                       │
│        score: 0.78                                        │
│      },                                                    │
│      ...                                                   │
│    ]                                                       │
│    count: 5                                               │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Query + Statutes + Domain]
┌──────────────────────────────────────────────────────────┐
│  AGENT 4: CASE SIMILARITY                                │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Query + embedding                                    │
│    • Primary domain                                       │
│  PROCESS:                                                 │
│    1. Search case_law_vectors with domain filter          │
│    2. Find similar past cases                             │
│    3. Extract case details and outcomes                   │
│  RETRIEVAL:                                               │
│    Collection: case_law_vectors                          │
│    Filter: domain = "property_law"                        │
│    Threshold: 0.45                                        │
│    Top-K: 5 results                                       │
│  OUTPUTS:                                                 │
│    similar_cases: [                                       │
│      {                                                     │
│        case_name: "Tenant v. Landlord...",               │
│        court: "High Court",                               │
│        year: 2023,                                        │
│        summary: "Illegal eviction case...",              │
│        key_points: ["Due process required", ...],        │
│        citation: "2023 (5) SCC 123",                      │
│        domain: "property_law",                            │
│        score: 0.72                                        │
│      },                                                    │
│      ...                                                   │
│    ]                                                       │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Query + Statutes + Cases]
┌──────────────────────────────────────────────────────────┐
│  AGENT 5: LEGAL REASONING                                │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Original query                                       │
│    • Retrieved statutes (5 items)                         │
│    • Retrieved cases (5 items)                            │
│  PROCESS:                                                 │
│    1. Build context from retrieved documents              │
│    2. Send to LLM with retrieval-bounded prompts          │
│    3. Enforce "only use retrieved info" constraint        │
│    4. Generate plain-language explanation                 │
│  LLM:                                                      │
│    Model: Ollama (Llama 3 / Mistral)                      │
│    Temperature: 0.3 (factual, not creative)              │
│    Max tokens: 1500                                       │
│  OUTPUTS:                                                 │
│    explanation: "Based on the Rent Control Act...         │
│                  Section 21 requires that landlords...    │
│                  Similar cases (case 1, case 2) show...   │
│                  What is missing: Specific jurisdiction..." │
│    statutes_cited: [3 statute titles]                     │
│    cases_cited: [3 case names]                            │
│    confidence: 0.76                                       │
│  NO HALLUCINATION: Only uses retrieved documents          │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Query + Statutes + Cases + Explanation]
┌──────────────────────────────────────────────────────────┐
│  AGENT 6: CIVIC ACTION RECOMMENDATION                    │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Query                                                │
│    • Legal explanation (from Reasoning)                   │
│    • Retrieved statutes                                   │
│  PROCESS:                                                 │
│    1. Search civic_process_vectors                        │
│    2. Find applicable civic procedures/actions            │
│    3. Recommend specific, actionable steps                │
│  RETRIEVAL:                                               │
│    Collection: civic_process_vectors                     │
│    Threshold: 0.50                                        │
│    Top-K: 5 results                                       │
│  OUTPUTS:                                                 │
│    recommendations: [                                     │
│      {                                                     │
│        action: "File complaint with District Authority",  │
│        description: "Lodge formal complaint...",          │
│        steps: ["Gather documents", "Fill form 1", ...],   │
│        authority: "District Magistrate Office",           │
│        required_documents: ["ID", "Lease", "Notice"],     │
│        timeline: "30 days",                               │
│        cost: "Free",                                      │
│        score: 0.80                                        │
│      },                                                    │
│      ...                                                   │
│    ]                                                       │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [All Previous Context]
┌──────────────────────────────────────────────────────────┐
│  AGENT 7: ETHICS & SAFETY VALIDATION                     │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Full explanation                                     │
│    • All recommendations                                  │
│  PROCESS:                                                 │
│    1. Check for problematic phrases ("sue them", etc)     │
│    2. Validate no legal advice is given                   │
│    3. Ensure appropriate disclaimers                      │
│    4. Add safety disclaimers if needed                    │
│  SAFETY CHECKS:                                           │
│    ✓ NOT providing legal advice                           │
│    ✓ NOT suggesting litigation strategies                 │
│    ✓ NOT making absolute claims                          │
│  OUTPUTS:                                                 │
│    is_safe: true                                          │
│    issues: []                                             │
│    safety_disclaimer: "This is information only..."       │
│    standard_disclaimer: "Not a substitute for..."         │
│    approved: true                                         │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Complete Context + Safety Validation]
┌──────────────────────────────────────────────────────────┐
│  AGENT 8: LONG-TERM MEMORY                               │
├──────────────────────────────────────────────────────────┤
│  INPUTS:                                                  │
│    • Complete query context                              │
│    • All retrieved documents                              │
│    • Explanation and recommendations                      │
│  PROCESS:                                                 │
│    1. Create case memory object                           │
│    2. Generate embedding for case memory                  │
│    3. Store in case_memory_vectors collection             │
│    4. Log user interaction                                │
│    5. Make retrievable for future queries                 │
│  STORAGE:                                                 │
│    Collection 1: case_memory_vectors                     │
│      - Complete case context                              │
│      - Retrieved documents                                │
│      - Final output                                       │
│      - Timestamp                                          │
│                                                            │
│    Collection 2: user_interaction_memory                  │
│      - User ID / Session                                  │
│      - Query history                                      │
│      - Patterns and preferences                           │
│  OUTPUTS:                                                 │
│    case_id: "case_20260120_00123"                        │
│    stored: true                                           │
│    retrieval_enabled: true                               │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼ [Complete Result Ready]
┌──────────────────────────────────────────────────────────┐
│                  FINAL OUTPUT                             │
├──────────────────────────────────────────────────────────┤
│  {                                                        │
│    "query": "What are my rights when...",                │
│    "domains": ["property_law", "tenant_rights"],         │
│    "explanation": "Based on the Rent Control Act...",   │
│    "statutes": [Retrieved 5 statutes],                   │
│    "similar_cases": [Retrieved 5 cases],                 │
│    "recommendations": [                                   │
│      {                                                     │
│        "action": "File complaint",                        │
│        "steps": [...],                                    │
│        "timeline": "30 days",                             │
│        ...                                                │
│      }                                                     │
│    ],                                                      │
│    "disclaimers": [                                       │
│      "This is legal information only, not advice",       │
│      "Consult with a qualified lawyer..."                │
│    ],                                                      │
│    "case_id": "case_20260120_00123",                     │
│    "confidence": 0.76                                     │
│  }                                                         │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  DELIVERED TO USER VIA:                                   │
│  • FastAPI REST API (JSON response)                       │
│  • Streamlit UI (Formatted display)                       │
│  • Case retrieved in future queries (Memory)              │
└──────────────────────────────────────────────────────────┘
```

---

## 🧠 Agent Specifications & Responsibilities

### Agent 1: Intake & Normalization Agent
```
PURPOSE: Prepare raw user input for processing

INPUT:
  - Raw text query (any format, any length)

PROCESSING:
  1. Strip whitespace & normalize spacing
  2. Convert to lowercase
  3. Generate 384-dimensional vector embedding
  4. Extract metadata (word count, language)

OUTPUT:
  - Normalized query text
  - Vector embedding (384-dim)
  - Query metadata

RETRIEVAL: None
LLM: None
QDRANT: None

KEY FEATURE: Deterministic preprocessing (no ML variability)
```

### Agent 2: Legal Domain Classification Agent
```
PURPOSE: Identify which area of law applies (property, criminal, etc)

INPUT:
  - Normalized query + embedding

PROCESSING:
  1. Search legal_taxonomy_vectors collection
     - Uses cosine similarity between query vector and taxonomy vectors
     - Threshold: 0.4 (medium confidence needed)
     - Returns top 3 matches
  2. Extract domain names from retrieved taxonomy
  3. Identify primary domain (highest score)
  4. Fallback: Keyword matching if no semantic match

OUTPUT:
  - List of applicable domains
  - Primary domain (most relevant)
  - Confidence score

RETRIEVAL: 
  Collection: legal_taxonomy_vectors
  Threshold: 0.4
  Top-K: 3
  Metric: Cosine similarity

LLM: None
KEY FEATURE: Classifies into 14 legal domains (constitutional, criminal, civil, etc)
```

### Agent 3: Knowledge Retrieval Agent
```
PURPOSE: Find applicable laws, statutes, and regulations

INPUT:
  - Query + embedding
  - Primary legal domain

PROCESSING:
  1. Filter statutes by domain
  2. Search statutes_vectors with domain filter
     - Only retrieves statutes in identified domain
     - Threshold: 0.5 (high confidence)
     - Returns top 5 matches
  3. Extract statute details (title, section, content, jurisdiction)

OUTPUT:
  - List of 5 most relevant statutes
  - Full statute content
  - Section numbers and references
  - Jurisdiction info

RETRIEVAL:
  Collection: statutes_vectors
  Filter: domain = primary_domain
  Threshold: 0.5
  Top-K: 5
  Metadata: title, section, act_name, content, jurisdiction

LLM: None
KEY FEATURE: Evidence-based legal retrieval - all statutes are real documents
```

### Agent 4: Case Similarity Agent
```
PURPOSE: Find similar past cases to provide precedent context

INPUT:
  - Query + embedding
  - Primary legal domain

PROCESSING:
  1. Filter cases by domain
  2. Search case_law_vectors with domain filter
     - Finds cases with similar fact patterns
     - Threshold: 0.45 (medium-high confidence)
     - Returns top 5 matches
  3. Extract case information (name, court, year, summary, key points)

OUTPUT:
  - List of similar past cases
  - Court decisions
  - Case citations
  - Key legal points from judgments

RETRIEVAL:
  Collection: case_law_vectors
  Filter: domain = primary_domain
  Threshold: 0.45
  Top-K: 5
  Metadata: case_name, court, year, summary, key_points, citation

LLM: None
KEY FEATURE: Precedent-aware - shows what courts have decided before
```

### Agent 5: Legal Reasoning Agent
```
PURPOSE: Generate plain-language legal explanation from retrieved documents

INPUT:
  - Query
  - Retrieved statutes (5 items)
  - Retrieved cases (5 items)

PROCESSING:
  1. Build context string from retrieved documents
  2. Create system prompt enforcing retrieval-bounded reasoning
  3. Create user prompt with query + context
  4. Send to LLM with constraints:
     - ONLY use retrieved documents
     - Cite specific sections
     - Indicate missing information
     - NO legal advice
     - NO litigation strategy
  5. Generate explanation with citations

OUTPUT:
  - Plain-language explanation
  - Cited statutes (3 main ones)
  - Cited cases (3 main ones)
  - Gaps/unknowns clearly stated

RETRIEVAL:
  Uses statutes + cases from earlier retrieval (pass-through)

LLM:
  Model: Ollama (Llama 3 / Mistral)
  Temperature: 0.3 (factual, not creative)
  Max tokens: 1500

SAFETY: 
  - System prompt enforces "NO hallucination"
  - If no retrieved docs, returns "no information available"
  - Never makes up laws or cases
```

### Agent 6: Civic Action Recommendation Agent
```
PURPOSE: Recommend specific, actionable civic steps user can take

INPUT:
  - Query
  - Legal explanation
  - Retrieved statutes

PROCESSING:
  1. Identify types of actions from explanation
  2. Search civic_process_vectors collection
     - Finds applicable procedures/actions
     - Threshold: 0.50
     - Returns top 5 matches
  3. Extract action details (steps, authority, documents, timeline, cost)

OUTPUT:
  - List of 5 actionable recommendations
  - Specific steps for each action
  - Required documents
  - Authority to contact
  - Timeline and costs

RETRIEVAL:
  Collection: civic_process_vectors
  Threshold: 0.50
  Top-K: 5
  Metadata: action, description, steps, authority, required_documents, timeline

LLM: None
KEY FEATURE: Practical action-oriented - "Here's what YOU can do"
```

### Agent 7: Ethics & Safety Agent
```
PURPOSE: Validate outputs for safety, ethics, and legal compliance

INPUT:
  - Full explanation text
  - All recommendations
  - Complete context

PROCESSING:
  1. Scan for problematic phrases:
     - "sue them" (litigation strategy)
     - "file a lawsuit" (legal advice)
     - "guaranteed win" (unrealistic claims)
     - "definitely illegal" (absolute claims)
     - "you should sue" (direct legal advice)
  2. Validate no legal advice is provided
  3. Check recommendations are actionable, not litigation-focused
  4. Add appropriate disclaimers
  5. Flag any safety issues

OUTPUT:
  - is_safe: boolean
  - issues: list of problems found
  - safety_disclaimer: strong warning (if issues found)
  - standard_disclaimer: always added
  - approved: boolean (safe to send to user)

RETRIEVAL: None
LLM: None
KEY FEATURE: Hard safety validation - prevents problematic outputs
```

### Agent 8: Memory Agent
```
PURPOSE: Store case context for future reference and learning

INPUT:
  - Complete case context
  - All retrieved documents
  - Final output
  - User session info

PROCESSING:
  1. Create case memory object with all context
  2. Generate embedding for case memory
  3. Store in case_memory_vectors collection
  4. Store user interaction in user_interaction_memory
  5. Assign case ID for future retrieval

STORAGE:

  Collection 1: case_memory_vectors
    Fields:
      - case_id (unique identifier)
      - query (original user query)
      - domains (identified legal domains)
      - statutes (retrieved statutes)
      - cases (retrieved cases)
      - explanation (final output)
      - recommendations (civic actions)
      - timestamp (when processed)
      - vector (384-dim embedding)

  Collection 2: user_interaction_memory
    Fields:
      - user_id (anonymous or real)
      - query
      - timestamp
      - retrieved_domains
      - retrieved_statutes_count
      - retrieved_cases_count
      - interaction_timestamp

OUTPUT:
  - case_id: for future retrieval
  - stored: confirmation
  - retrieval_enabled: can be used in future queries

RETRIEVAL: Write to collections, enables semantic search for similar cases
LLM: None
KEY FEATURE: Enables learning - future queries can find and reference past cases
```

---

## 🗄️ Qdrant Vector Database Schema

### Collection 1: legal_taxonomy_vectors
**Purpose**: Legal domain taxonomy for classification
```
Collection Name: legal_taxonomy_vectors
Vector Size: 384 (all-MiniLM-L6-v2)
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer (unique),
  vector: float[384] (embedding of domain description),
  payload: {
    domain: string (e.g., "property_law", "criminal_law"),
    description: string (what this domain covers),
    keywords: string[] (search keywords),
    examples: string[] (example queries)
  }
}

Use Case: Classification Agent searches this to identify legal domain
Sample Query: "What are my rights as a tenant?" → matches "property_law"
```

### Collection 2: statutes_vectors
**Purpose**: Legal statutes, acts, and regulations
```
Collection Name: statutes_vectors
Vector Size: 384
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer,
  vector: float[384] (embedding of statute content),
  payload: {
    title: string (statute name),
    section: string (section number),
    act_name: string (name of act),
    content: string (full text of statute),
    domain: string (legal domain),
    jurisdiction: string (India/state),
    year: integer (when enacted),
    amendments: string (amendment history)
  }
}

Use Case: Knowledge Retrieval Agent searches this for applicable laws
Sample Query: Tenant rights → retrieves Rent Control Act sections
```

### Collection 3: case_law_vectors
**Purpose**: Court cases and legal judgments
```
Collection Name: case_law_vectors
Vector Size: 384
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer,
  vector: float[384] (embedding of case summary),
  payload: {
    case_name: string,
    court: string (Supreme Court, High Court, etc),
    year: integer,
    judge: string (if notable),
    summary: string (what was the case about),
    key_points: string[] (important rulings),
    citation: string (case citation e.g., "2023 SCC 123"),
    domain: string (legal domain),
    outcome: string (judgment direction),
    relevant_statutes: string[] (statutes cited in judgment)
  }
}

Use Case: Case Similarity Agent finds precedent cases
Sample Query: Unfair eviction → retrieves similar tenant cases
```

### Collection 4: civic_process_vectors
**Purpose**: Civic procedures and actionable processes
```
Collection Name: civic_process_vectors
Vector Size: 384
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer,
  vector: float[384] (embedding of process description),
  payload: {
    action: string (e.g., "File complaint with authorities"),
    description: string (what this action does),
    steps: string[] (step-by-step instructions),
    authority: string (which authority handles this),
    required_documents: string[] (documents needed),
    timeline: string (how long it takes),
    cost: string (free/fee amount),
    success_rate: string (if known),
    similar_actions: string[] (related actions),
    domain: string (applicable legal domain)
  }
}

Use Case: Recommendation Agent suggests practical next steps
Sample Query: Eviction → retrieves "File complaint with magistrate" action
```

### Collection 5: case_memory_vectors
**Purpose**: Long-term case memory for learning
```
Collection Name: case_memory_vectors
Vector Size: 384
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer,
  vector: float[384] (embedding of case query),
  payload: {
    case_id: string (unique ID, e.g., "case_20260120_00123"),
    user_id: string (anonymous or real user ID),
    query: string (original user query),
    domains: string[] (identified domains),
    statutes_retrieved: integer (count),
    cases_retrieved: integer (count),
    explanation: string (generated explanation),
    recommendations: string[] (civic actions recommended),
    timestamp: string (ISO timestamp),
    status: string (resolved/pending/archived)
  }
}

Use Case: Future queries can find and reference similar past cases
Sample Query: Similar tenant question → finds previous case → reuses context
```

### Collection 6: user_interaction_memory
**Purpose**: Track user interactions and patterns
```
Collection Name: user_interaction_memory
Vector Size: 384
Distance Metric: Cosine Similarity

Point Structure:
{
  id: integer,
  vector: float[384] (embedding of interaction),
  payload: {
    user_id: string (session or anonymous ID),
    session_id: string (unique session ID),
    query: string,
    timestamp: string,
    domains_searched: string[] (legal domains queried),
    retrieval_success: boolean,
    interaction_duration: integer (seconds),
    user_feedback: string (if provided),
    similar_past_queries: integer (count of similar queries)
  }
}

Use Case: Personalization, analytics, and learning about user patterns
Sample Query: Understand user's legal area of interest → improves recommendations
```

---

## 🔄 Complete Request/Response Cycle

### Example: "What are my rights as a tenant being illegally evicted?"

**PHASE 1: INTAKE**
```
Input: "What are my rights as a tenant being illegally evicted?"

Agent 1 Processing:
  • Normalize: "what are my rights as a tenant being illegally evicted?"
  • Generate embedding: [0.234, -0.156, 0.872, 0.441, ...]
  • Extract metadata: word_count=12, query_length=54
  
Output State:
  normalized_query: "what are my rights as a tenant being illegally evicted?"
  embedding: [384-dim vector]
```

**PHASE 2: CLASSIFICATION**
```
Agent 2 Processing:
  • Search legal_taxonomy_vectors with embedding
  • Cosine similarity scores:
    - "property_law": 0.82 ✓
    - "tenant_rights": 0.78 ✓
    - "civil_law": 0.65
    
Output State:
  domains: ["property_law", "tenant_rights"]
  primary_domain: "property_law"
  confidence: 0.82
```

**PHASE 3: KNOWLEDGE RETRIEVAL**
```
Agent 3 Processing:
  • Filter statutes where domain="property_law"
  • Search statutes_vectors with query embedding
  • Top matches with scores:
    1. "Rent Control Act, Section 21" - score: 0.78
    2. "Protection of Tenancy Act, Section 15" - score: 0.74
    3. "Delhi Rent Control Act, Section 12" - score: 0.71
    4. "Model Tenancy Act, Section 8" - score: 0.68
    5. "Constitution Article 21" - score: 0.65
    
Output State:
  statutes: [full content of 5 statutes above]
  statute_scores: [0.78, 0.74, 0.71, 0.68, 0.65]
  retrieved_count: 5
```

**PHASE 4: CASE SIMILARITY**
```
Agent 4 Processing:
  • Filter cases where domain="property_law"
  • Search case_law_vectors with query embedding
  • Top matches:
    1. "State v. Landlord - Illegal Eviction 2023" - score: 0.76
    2. "Tenant Union v. Property Owner 2022" - score: 0.72
    3. "Due Process Eviction Case 2021" - score: 0.68
    4. "Tenant Rights Judgment 2023" - score: 0.65
    5. "Housing Rights Case 2022" - score: 0.61
    
Output State:
  similar_cases: [full case details, judgments, precedents]
  case_scores: [0.76, 0.72, 0.68, 0.65, 0.61]
```

**PHASE 5: REASONING**
```
Agent 5 Processing:
  Receives: query + 5 statutes + 5 cases
  
  System Prompt:
    "You MUST only use the retrieved documents.
     Cite specific sections.
     Do NOT provide legal advice.
     Clearly indicate what is NOT in documents."
  
  User Prompt:
    "Query: What are my rights as tenant being illegally evicted?
     
     Retrieved Statutes:
     1. Rent Control Act, Section 21 - Landlords must follow due process
     2. Protection of Tenancy Act, Section 15 - Tenants have 30 days notice
     [... 3 more statutes ...]
     
     Retrieved Cases:
     1. State v. Landlord (2023) - Held that eviction without court order is illegal
     [... 4 more cases ...]
     
     Based ONLY on these, explain the tenant's rights."
  
  LLM Generation (Ollama Llama 3, temp=0.3):
    "Based on the retrieved documents:
    
     YOUR RIGHTS:
     • Rent Control Act, Section 21 establishes that landlords must follow legal 
       procedures before eviction
     • Protection of Tenancy Act, Section 15 requires 30 days written notice
     • The case 'State v. Landlord (2023)' established that eviction without court 
       order is illegal and constitutes wrongful eviction
    
     KEY PROTECTIONS:
     • Due process is mandatory
     • Court order required (from the cases cited)
     • Notice period must be provided
    
     WHAT IS NOT CLEAR (not in documents):
     • Your specific state's additional protections
     • Exact compensation for illegal eviction
     • Timeline for court relief
     
     NEXT STEPS (from documents):
     • Check local jurisdiction rules (your state may have stricter rules)"
  
Output State:
  explanation: [full text above]
  statutes_cited: ["Rent Control Act", "Protection of Tenancy Act", "Article 21"]
  cases_cited: ["State v. Landlord 2023", "Tenant Union v. Owner 2022", ...]
  confidence: 0.76
```

**PHASE 6: CIVIC RECOMMENDATIONS**
```
Agent 6 Processing:
  • Search civic_process_vectors for actions
  • Top matches:
    1. "File complaint with District Magistrate" - score: 0.81
    2. "File case in District Court" - score: 0.78
    3. "Contact Legal Aid Services" - score: 0.72
    4. "File complaint with Police" - score: 0.65
    5. "Contact Tenant Union" - score: 0.58
  
Output State:
  recommendations: [
    {
      action: "File complaint with District Magistrate",
      description: "Lodge formal complaint of illegal eviction",
      steps: [
        "1. Gather proof of tenancy (rent receipts, lease, etc)",
        "2. Get eviction notice in writing (if possible)",
        "3. Go to District Magistrate's office",
        "4. File form with all documents",
        "5. Attend hearings"
      ],
      authority: "District Magistrate Office",
      required_documents: ["ID", "Lease/Rent Agreement", "Eviction Notice", "Rent Receipts"],
      timeline: "Complaint reviewed within 30 days",
      cost: "Free"
    },
    {
      action: "File case in District Court",
      description: "Seek injunction against eviction",
      steps: ["1. Hire lawyer", "2. Prepare case", "3. File petition", ...],
      authority: "District Court",
      required_documents: ["Lawyer", "Evidence of tenancy", "Violation proof"],
      timeline: "3-6 months for hearing",
      cost: "Court fees + lawyer fees"
    },
    ... 3 more recommendations
  ]
```

**PHASE 7: ETHICS VALIDATION**
```
Agent 7 Processing:
  • Scan explanation: "Based on retrieved documents..." ✓
  • Check for "sue them": NOT FOUND ✓
  • Check for absolute claims: NOT FOUND ✓
  • Check for litigation strategy: NOT FOUND ✓
  • Recommendations are civic actions, not legal advice ✓
  
Output State:
  is_safe: true
  issues: []
  safety_disclaimer: "" (none needed, content is safe)
  standard_disclaimer: "This is legal information only, not professional legal advice..."
  approved: true
```

**PHASE 8: MEMORY STORAGE**
```
Agent 8 Processing:
  • Create case_id: "case_20260120_00847"
  • Generate case memory embedding
  • Store in case_memory_vectors:
    {
      case_id: "case_20260120_00847",
      user_id: "anonymous",
      query: "What are my rights as a tenant being illegally evicted?",
      domains: ["property_law", "tenant_rights"],
      statutes_retrieved: 5,
      cases_retrieved: 5,
      explanation: [full explanation text],
      recommendations: [all 5 recommendations],
      timestamp: "2026-01-20T14:32:45Z"
    }
  
Output State:
  case_id: "case_20260120_00847"
  stored: true
  retrieval_enabled: true
```

**FINAL OUTPUT TO USER**
```json
{
  "status": "success",
  "query": "What are my rights as a tenant being illegally evicted?",
  "domains": ["property_law", "tenant_rights"],
  "primary_domain": "property_law",
  "explanation": "Based on the retrieved documents: [full explanation]...",
  "statutes": [
    {
      "title": "Rent Control Act",
      "section": "Section 21",
      "content": "Full statute text...",
      "jurisdiction": "India",
      "score": 0.78
    },
    ... 4 more
  ],
  "similar_cases": [
    {
      "case_name": "State v. Landlord",
      "court": "High Court",
      "year": 2023,
      "citation": "2023 (5) SCC 123",
      "key_points": ["Eviction without court order is illegal"],
      "score": 0.76
    },
    ... 4 more
  ],
  "recommendations": [
    {
      "action": "File complaint with District Magistrate",
      "description": "Lodge formal complaint...",
      "steps": [...],
      "authority": "District Magistrate Office",
      "required_documents": [...],
      "timeline": "30 days",
      "cost": "Free"
    },
    ... 4 more
  ],
  "disclaimers": [
    "This is legal information only, not professional legal advice.",
    "Every case is unique. Consult with a qualified lawyer for guidance specific to your situation.",
    "This system does not provide litigation strategy or legal representation."
  ],
  "case_id": "case_20260120_00847",
  "confidence": 0.76,
  "processing_time_ms": 2847,
  "agent_outputs": {
    "intake": { "confidence": 1.0 },
    "classification": { "confidence": 0.82 },
    "knowledge": { "confidence": 0.78 },
    "case_similarity": { "confidence": 0.76 },
    "reasoning": { "confidence": 0.76 },
    "recommendation": { "confidence": 0.81 },
    "ethics": { "approved": true },
    "memory": { "stored": true }
  }
}
```

---

## 🔐 Safety & Retrieval-Bounded Guarantees

### What NyayaAI GUARANTEES:
1. **No Hallucination**: All outputs grounded in retrieved documents
2. **No Legal Advice**: System only provides information
3. **No Litigation Strategy**: Recommendations are civic, not legal tactics
4. **Traceable**: All claims cite specific statutes/cases
5. **Honest About Gaps**: Clearly states missing information
6. **Ethical Output**: Safety validation on all responses

### How It Prevents Hallucination:
```
LLM System Prompt:
  "You MUST only use information from the provided retrieved documents.
   You MUST cite specific statutes, sections, and cases when making claims.
   You MUST clearly state when information is NOT available.
   You MUST NOT provide legal advice or litigation strategy.
   If you do not have the information in retrieved documents, say so."

Process:
  1. User query → Generate embedding
  2. Retrieve ONLY from Qdrant (5 statutes + 5 cases)
  3. Build context from ONLY retrieved documents
  4. Send retrieval context to LLM
  5. LLM constrained to use only that context
  6. Ethics agent validates output
  7. Safety disclaimers added

Result:
  ✓ No making up laws
  ✓ No inventing precedents
  ✓ No speculating about outcomes
  ✓ Only facts from Qdrant collections
```

---

## 🚀 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | LangGraph | Manages 8-agent workflow |
| **Vector Database** | Qdrant | Stores and searches legal documents |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) | Converts text to 384-dim vectors |
| **LLM** | Ollama (Llama 3 / Mistral) | Local inference for reasoning |
| **API** | FastAPI | REST endpoints for queries |
| **Frontend** | Streamlit | Web UI for demo |
| **Containerization** | Docker Compose | Easy deployment with Qdrant |
| **Language** | Python 3.11+ | Primary implementation language |

---

## 📈 Performance Characteristics

```
Typical Query Latency Breakdown:

Intake Agent:           50ms   (normalize + embed)
Classification Agent:   200ms  (Qdrant search + taxonomy)
Knowledge Agent:        250ms  (Qdrant search statutes)
Case Agent:             250ms  (Qdrant search cases)
Reasoning Agent:        1500ms (LLM inference)
Recommendation Agent:   250ms  (Qdrant search civic_process)
Ethics Agent:           100ms  (text scanning)
Memory Agent:           200ms  (Qdrant upsert)
───────────────────────────────
TOTAL:                  ~2850ms (2.85 seconds)

Qdrant Characteristics:
  • Search latency: ~50ms per query (on standard hardware)
  • Supports 6 collections with 384-dim vectors
  • Can handle thousands of documents
  • Highly scalable with proper infrastructure

Bottleneck:
  • LLM Inference (1500ms) - depends on model and hardware
  • Can be optimized by using smaller models or GPU inference
```

---

## 🎓 Learning & Future Enhancements

### Current Learning Mechanism:
```
Every query stores:
  • Query text
  • Domains identified
  • Retrieved documents
  • Generated explanation
  • Recommendations given

Future queries can:
  • Find similar past queries
  • Reuse case memory
  • Learn from patterns
  • Improve recommendations
```

### Potential Future Enhancements:
1. **Multimodal Support**: Images (legal documents), audio (court recordings)
2. **Language Support**: Hindi, Tamil, Telugu, Bengali translations
3. **Advanced Features**: Form filling, legal document parsing
4. **Integration**: Legal aid organizations, court systems
5. **Personalization**: User-specific recommendations
6. **Analytics**: Understanding what legal areas are most searched

---

## 🎯 What You've Built

### Summary
You've created a **sophisticated, safety-focused, retrieval-grounded legal AI system** that:

1. **Understands** user queries through intelligent normalization
2. **Classifies** legal domains with semantic search
3. **Retrieves** evidence-based legal information from Qdrant
4. **Reasons** about legal situations using constrained LLMs
5. **Recommends** actionable civic steps
6. **Validates** safety and ethics
7. **Remembers** for future learning

### Key Innovations:
- **Retrieval-bounded reasoning** (no hallucination)
- **Multi-agent separation of concerns** (modularity)
- **Safety-first design** (ethics validation)
- **Evidence-based outputs** (all claims cited)
- **Scalable architecture** (can handle thousands of queries)

### Real-World Impact:
- Citizens can discover applicable laws
- Accessible legal information without lawyers
- Guidance on civic processes
- Precedent-aware recommendations
- Transparent, traceable reasoning

---

## 📚 Related Documentation

For more details, see:
- [README.md](../README.md) - Quick start guide
- [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) - Technical design decisions
- [ETHICS_AND_LIMITATIONS.md](./ETHICS_AND_LIMITATIONS.md) - Safety and ethics framework
- [SETUP_GUIDE.md](../SETUP_GUIDE.md) - Installation instructions

