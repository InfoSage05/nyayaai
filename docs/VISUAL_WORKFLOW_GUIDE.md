# NyayaAI - Visual Workflow Architecture

## 🎯 The Big Picture: What NyayaAI Does

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   A CITIZEN ASKS A QUESTION                      ┃
┃  "What are my rights when my landlord illegally evicts me?"      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                               │
                               ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          NyayaAI SYSTEM ORCHESTRATES 8 SPECIALIZED AGENTS        ┃
┃           Each agent handles ONE specific responsibility          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
    ┌─────────┐           ┌─────────┐           ┌─────────┐
    │ AGENT 1 │           │ AGENT 2 │           │ AGENT 3 │
    │ INTAKE  │           │ CLASS   │           │ KNOW    │
    │         │           │         │           │         │
    │Clean &  │──────────▶│Identify │──────────▶│Search   │
    │Normalize│           │Domain   │           │Laws     │
    │Query    │           │(Property│           │(Rent    │
    │         │           │ Law)    │           │Control) │
    └─────────┘           └─────────┘           └─────────┘
                                                      │
        ┌───────────────────────────────────────────┬┘
        │                                           │
        ▼                                           ▼
    ┌─────────┐                                 ┌─────────┐
    │ AGENT 4 │                                 │ AGENT 5 │
    │ CASES   │                                 │REASONING│
    │         │                                 │         │
    │Find     │◀─────────────────────────────── │Generate │
    │Similar  │ (Statutes + Cases)              │Explanation
    │Cases    │                                 │         │
    └─────────┘                                 └─────────┘
        │                                           │
        └───────────────┬────────────────────────────┘
                        │
                        ▼
                    ┌─────────┐
                    │ AGENT 6 │
                    │ REC     │
                    │         │
                    │Suggest  │
                    │Civic    │
                    │Actions  │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ AGENT 7 │
                    │ ETHICS  │
                    │         │
                    │Validate │
                    │Safety   │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ AGENT 8 │
                    │ MEMORY  │
                    │         │
                    │Store    │
                    │for      │
                    │Future   │
                    └────┬────┘
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                       CITIZEN GETS ANSWER                     ┃
┃  ✓ Relevant laws explained in plain language                  ┃
┃  ✓ Similar past cases cited as precedent                      ┃
┃  ✓ Specific civic actions to take (with steps)                ┃
┃  ✓ All information traced back to legal sources               ┃
┃  ✓ Clear disclaimers (not legal advice)                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 🔄 Request Journey: Step-by-Step

```
═══════════════════════════════════════════════════════════════════

STEP 1: USER SUBMITS QUERY

Input:
  "What are my rights as a tenant being illegally evicted?"

Channel: 
  • FastAPI REST API (/api/v1/query)
  • Streamlit Web UI
  • Demo Script

═══════════════════════════════════════════════════════════════════

STEP 2: INTAKE AGENT - PREPARE THE QUESTION

What It Does:
  • Cleans up the query
  • Normalizes text (lowercase, remove extra spaces)
  • Creates a mathematical representation (embedding)
  
Input:  "What are my rights as a tenant being illegally evicted?"
Output: 
  normalized: "what are my rights as a tenant being illegally evicted?"
  embedding: [0.234, -0.156, 0.872, 0.441, 0.325, ...]  ← 384 numbers

Why It Matters:
  ✓ All downstream agents work with consistent format
  ✓ Embedding allows semantic searching in Qdrant
  ✓ Sets up for fast retrieval

═══════════════════════════════════════════════════════════════════

STEP 3: CLASSIFICATION AGENT - IDENTIFY THE LEGAL DOMAIN

What It Does:
  • Takes the embedding from Step 2
  • Searches Qdrant collection: legal_taxonomy_vectors
  • Matches to legal domains (14 possible categories)
  
Search Results (Qdrant):
  Match 1: "property_law"      Score: 0.82  ✓✓ BEST MATCH
  Match 2: "tenant_rights"     Score: 0.78  ✓
  Match 3: "civil_law"         Score: 0.65
  
Decision:
  Primary Domain: property_law
  Secondary: tenant_rights

Why It Matters:
  ✓ Filters subsequent searches to relevant legal area
  ✓ Prevents searching criminal law for landlord dispute
  ✓ Improves accuracy of retrieved documents

═══════════════════════════════════════════════════════════════════

STEP 4: KNOWLEDGE RETRIEVAL AGENT - FIND APPLICABLE LAWS

What It Does:
  • Uses domain from Step 3 (property_law)
  • Searches Qdrant collection: statutes_vectors
  • Only retrieves laws from property domain
  • Returns top 5 matching statutes
  
Qdrant Query:
  Vector: [embedding from Step 2]
  Collection: statutes_vectors
  Filter: domain = "property_law"  ← Only property laws!
  Threshold: 0.5  ← Medium-high similarity needed
  Limit: 5 results
  
Retrieved Statutes:
  1. Rent Control Act, Section 21           Score: 0.78
     Content: "Landlords must follow due process..."
  
  2. Protection of Tenancy Act, Section 15  Score: 0.74
     Content: "30 days notice required..."
  
  3. Delhi Rent Control Act, Section 12     Score: 0.71
     Content: "Eviction only by court order..."
  
  4. Model Tenancy Act, Section 8           Score: 0.68
     Content: "Illegal evictions are punishable..."
  
  5. Constitution Article 21                Score: 0.65
     Content: "Right to life includes shelter..."

Why It Matters:
  ✓ User gets actual laws, not made-up information
  ✓ All statutes come from real legal corpus
  ✓ Specific sections quoted
  ✓ Foundation for legal explanation

═══════════════════════════════════════════════════════════════════

STEP 5: CASE SIMILARITY AGENT - FIND RELEVANT PRECEDENTS

What It Does:
  • Uses embedding from Step 2
  • Searches Qdrant collection: case_law_vectors
  • Filter by domain (property_law)
  • Finds 5 similar past court cases
  
Qdrant Query:
  Vector: [embedding from Step 2]
  Collection: case_law_vectors
  Filter: domain = "property_law"  ← Only property cases!
  Threshold: 0.45  ← Medium similarity
  Limit: 5 results
  
Retrieved Cases:
  1. "State v. Landlord - Illegal Eviction 2023"    Score: 0.76
     Court: High Court
     Key Ruling: "Eviction without court order is illegal"
     Citation: "2023 (5) SCC 123"
  
  2. "Tenant Union v. Property Owner 2022"          Score: 0.72
     Court: District Court
     Key Ruling: "Due process must be followed"
     Citation: "2022 (3) SCC 456"
  
  3. "Due Process Eviction Case 2021"               Score: 0.68
     Key Ruling: "Landlords cannot self-help evict"
  
  4. "Tenant Rights Judgment 2023"                  Score: 0.65
     Key Ruling: "Tenants have 30-day notice rights"
  
  5. "Housing Rights Case 2022"                     Score: 0.61
     Key Ruling: "Shelter is fundamental right"

Why It Matters:
  ✓ Shows what courts have decided before
  ✓ Provides legal precedent
  ✓ Shows patterns in how similar cases ruled
  ✓ Gives user confidence in information

═══════════════════════════════════════════════════════════════════

STEP 6: REASONING AGENT - GENERATE EXPLANATION

What It Does:
  • Takes: Query + 5 Statutes + 5 Cases
  • Sends to LLM (Ollama - Llama 3)
  • Uses CONSTRAINED prompts (can't hallucinate)
  • Generates plain-language explanation
  
System Prompt (Hard Constraint):
  "You MUST only use information from the provided documents.
   You MUST cite specific statutes and cases.
   You MUST NOT provide legal advice.
   You MUST NOT invent laws or cases.
   You MUST clearly state what information is NOT available."

User Prompt:
  "Query: What are my rights as a tenant being illegally evicted?
   
   Retrieved Statutes:
   1. Rent Control Act, Section 21: Landlords must follow due process...
   2. Protection of Tenancy Act, Section 15: 30 days notice required...
   [3 more statutes...]
   
   Retrieved Cases:
   1. State v. Landlord (2023): Eviction without court order is illegal...
   [4 more cases...]
   
   Based ONLY on these documents, explain tenant's rights:"

LLM Output (Generated Explanation):
  "Based on the retrieved documents:
   
   YOUR RIGHTS AS A TENANT:
   • Rent Control Act, Section 21 establishes that landlords must follow 
     legal procedures before evicting you
   • Protection of Tenancy Act, Section 15 requires landlords to provide 
     at least 30 days notice in writing
   • The case 'State v. Landlord (2023)' established that eviction without 
     a court order is illegal and can result in damages
   
   WHAT THIS MEANS:
   Your landlord cannot simply remove you or your belongings. They must:
   1. Provide written notice (30 days minimum)
   2. Get a court order
   3. Follow due process
   
   WHAT IS NOT CLEAR (from these documents):
   • Your specific state's additional protections
   • Exact amount of compensation for illegal eviction
   • Timeline for court-ordered relief
   
   NEXT STEP: Consult local legal resources for your jurisdiction."

Why It Matters:
  ✓ Explains legal concepts in plain language
  ✓ Cites specific laws and cases
  ✓ No made-up information (grounded in retrieval)
  ✓ Honest about gaps

═══════════════════════════════════════════════════════════════════

STEP 7: RECOMMENDATION AGENT - SUGGEST CIVIC ACTIONS

What It Does:
  • Takes: Query + Explanation from Step 6
  • Searches Qdrant collection: civic_process_vectors
  • Finds actionable civic processes
  • Returns 5 specific recommended actions
  
Qdrant Query:
  Vector: [embedding from Step 2]
  Collection: civic_process_vectors
  Threshold: 0.50
  Limit: 5 results
  
Retrieved Actions:
  1. "File complaint with District Magistrate"    Score: 0.81
  2. "File case in District Court"                Score: 0.78
  3. "Contact Legal Aid Services"                 Score: 0.72
  4. "File complaint with Police"                 Score: 0.65
  5. "Contact Tenant Union"                       Score: 0.58

Formatted Recommendations:
  ACTION 1: File Complaint with District Magistrate
    Description: Lodge formal complaint of illegal eviction
    Steps:
      1. Gather proof of tenancy (rent receipts, lease copy)
      2. Obtain eviction notice in writing (if possible)
      3. Visit District Magistrate's office
      4. Complete complaint form
      5. Attend scheduled hearings
    Authority: District Magistrate Office
    Required Documents: ID, Lease Agreement, Eviction Notice, Rent Receipts
    Timeline: 30 days for complaint review
    Cost: Free
    
  [4 more recommendations with full details...]

Why It Matters:
  ✓ User knows EXACTLY what to do
  ✓ Clear steps (not abstract legal advice)
  ✓ Knows where to go (authority)
  ✓ Knows what documents to bring
  ✓ Realistic timeline and costs

═══════════════════════════════════════════════════════════════════

STEP 8: ETHICS AGENT - VALIDATE SAFETY

What It Does:
  • Scans explanation for problematic phrases
  • Checks recommendations aren't litigation tactics
  • Validates no legal advice is given
  • Approves output for user
  
Validation Checks:
  ✓ Does it say "sue them"?              NO - SAFE
  ✓ Does it say "file lawsuit"?          NO - SAFE  
  ✓ Does it guarantee outcomes?          NO - SAFE
  ✓ Is it providing legal advice?        NO - SAFE
  ✓ Are recommendations civic/govt?      YES - SAFE
  ✓ Are there appropriate disclaimers?   YES - SAFE
  
Result: ✓ APPROVED FOR DELIVERY

Disclaimers Added:
  "⚠️ IMPORTANT: This is legal information only, not professional 
      legal advice. Every case is unique. Consult with a qualified lawyer 
      for guidance specific to your situation."

Why It Matters:
  ✓ Prevents harmful outputs
  ✓ Ensures ethical compliance
  ✓ Protects both user and system
  ✓ Sets appropriate expectations

═══════════════════════════════════════════════════════════════════

STEP 9: MEMORY AGENT - STORE FOR LEARNING

What It Does:
  • Creates permanent record of this case
  • Stores in Qdrant for future reference
  • Enables learning for future similar queries
  
Memory Storage:
  Case ID: "case_20260120_00847"
  
  Stored in case_memory_vectors:
    query: "What are my rights as a tenant being illegally evicted?"
    domains: ["property_law", "tenant_rights"]
    statutes_retrieved: 5
    cases_retrieved: 5
    explanation: [full explanation text]
    recommendations: [all 5 recommended actions]
    timestamp: "2026-01-20T14:32:45Z"
    embedding: [384-dim vector for future retrieval]
  
  Also Stored in user_interaction_memory:
    user_id: "anonymous"
    session_id: [unique session]
    query: "What are my rights..."
    domains_searched: ["property_law", "tenant_rights"]
    timestamp: "2026-01-20T14:32:45Z"

Why It Matters:
  ✓ Future similar queries find this case
  ✓ System learns what legal issues matter
  ✓ Improves recommendations over time
  ✓ Enables analytics

═══════════════════════════════════════════════════════════════════

STEP 10: RETURN COMPLETE ANSWER TO USER

JSON Response Sent to Frontend:
```
{
  "status": "success",
  "case_id": "case_20260120_00847",
  
  "query": "What are my rights as a tenant being illegally evicted?",
  
  "domains": ["property_law", "tenant_rights"],
  "primary_domain": "property_law",
  
  "explanation": "Based on the retrieved documents: [full text]...",
  
  "statutes": [
    {
      "id": 1,
      "title": "Rent Control Act",
      "section": "Section 21",
      "content": "Full statute text...",
      "act_name": "Rent Control Act 2024",
      "jurisdiction": "India",
      "year": 2024,
      "score": 0.78
    },
    [4 more statutes...]
  ],
  
  "similar_cases": [
    {
      "case_name": "State v. Landlord",
      "court": "High Court",
      "year": 2023,
      "summary": "Illegal eviction case...",
      "key_points": ["Court order required", "Due process must be followed"],
      "citation": "2023 (5) SCC 123",
      "outcome": "In favor of tenant",
      "score": 0.76
    },
    [4 more cases...]
  ],
  
  "recommendations": [
    {
      "action": "File complaint with District Magistrate",
      "description": "Lodge formal complaint of illegal eviction",
      "steps": [
        "Gather proof of tenancy",
        "Get eviction notice",
        "Visit magistrate office",
        "File complaint",
        "Attend hearings"
      ],
      "authority": "District Magistrate Office",
      "required_documents": ["ID", "Lease", "Notice", "Rent receipts"],
      "timeline": "30 days",
      "cost": "Free",
      "score": 0.81
    },
    [4 more recommendations...]
  ],
  
  "disclaimers": [
    "This is legal information only, not professional legal advice.",
    "Every case is unique - consult a qualified lawyer.",
    "This system does not provide litigation strategy."
  ],
  
  "confidence": 0.76,
  "processing_time_ms": 2847,
  
  "agent_outputs": {
    "intake": {"confidence": 1.0},
    "classification": {"confidence": 0.82},
    "knowledge": {"confidence": 0.78},
    "case_similarity": {"confidence": 0.76},
    "reasoning": {"confidence": 0.76},
    "recommendation": {"confidence": 0.81},
    "ethics": {"approved": true},
    "memory": {"stored": true}
  }
}
```

Frontend Display (Streamlit):
  
  ⚖️ NyayaAI - Your Legal Information Assistant
  ═════════════════════════════════════════════════════════════
  
  📋 YOUR QUERY:
  "What are my rights as a tenant being illegally evicted?"
  
  🔍 LEGAL DOMAIN:
  Property Law, Tenant Rights
  
  📜 APPLICABLE LAWS:
  • Rent Control Act, Section 21 - Landlords must follow due process
  • Protection of Tenancy Act, Section 15 - 30 days notice required
  [3 more laws...]
  
  ⚖️ SIMILAR PAST CASES:
  • State v. Landlord (2023) - "Eviction without court order is illegal"
  • Tenant Union v. Owner (2022) - "Due process must be followed"
  [3 more cases...]
  
  ✅ WHAT YOU CAN DO:
  1. File complaint with District Magistrate
     - Steps: [1. Gather documents, 2. Get notice, ...]
     - Timeline: 30 days
     - Cost: Free
  
  2. File case in District Court
     - Steps: [1. Hire lawyer, 2. Prepare case, ...]
     - Timeline: 3-6 months
     - Cost: Court fees + lawyer fees
  
  [3 more recommendations...]
  
  ⚠️ IMPORTANT DISCLAIMERS:
  This is legal information only, not professional legal advice.
  Every case is unique. Consult with a qualified lawyer.
  This system does not provide litigation strategy.
  
  📊 CONFIDENCE: 76%
  ⏱️ PROCESSED IN: 2.8 seconds
  📌 CASE ID: case_20260120_00847 (saved for reference)

═══════════════════════════════════════════════════════════════════
```

---

## 🧩 How Each Agent Works Independently

```
┌─────────────────────────────────────────────────────────┐
│           AGENT INDEPENDENCE & MODULARITY               │
└─────────────────────────────────────────────────────────┘

AGENT 1: INTAKE
  Inputs from: User
  Outputs to: Classification Agent
  Qdrant: None
  LLM: None
  Can fail? Unlikely (preprocessing only)
  Replaces? Replace if you want different normalization
  ┌─────────────────────────────────────────┐
  │ Raw Query ─────────────────────────────▶│
  │  "What are my    ┌─────────────────┐   │
  │   rights?"  ───▶│  NORMALIZE      │   │
  │              │  • Lowercase     │   │
  │              │  • Clean spaces  │   │
  │              │  • Generate      │   │
  │              │    embedding     │   │
  │              └────────┬─────────┘   │
  │                       │              │
  │         Normalized + Embedding       │
  │                       │              │
  │         "what are my rights?" +      │
  │         [0.234, -0.156, ...]        │
  │                       │              │
  │                       ▼              │
  │                  To Agent 2          │
  └─────────────────────────────────────────┘

AGENT 2: CLASSIFICATION
  Inputs from: Agent 1
  Outputs to: Agents 3, 4, 6
  Qdrant: legal_taxonomy_vectors
  LLM: None
  Can fail? Yes (no matching domain found)
  Fallback: Keyword matching
  Replaces? Replace if you want different domain list
  ┌─────────────────────────────────────────┐
  │  Embedding ───────────────────────────▶│
  │  From Agent 1  ┌──────────────────┐   │
  │         ─────▶│ SEARCH QDRANT   │   │
  │         │     │ legal_taxonomy_ │   │
  │         │     │ vectors         │   │
  │         │     │                  │   │
  │         │     │ Returns:        │   │
  │         │     │ • property_law  │   │
  │         │     │   (0.82)        │   │
  │         │     │ • tenant_rights │   │
  │         │     │   (0.78)        │   │
  │         │     │ • civil_law     │   │
  │         │     │   (0.65)        │   │
  │         │     └────────┬─────────┘   │
  │         │              │              │
  │ Domains & Primary Domain             │
  │                       │              │
  │ ["property_law",      │              │
  │  "tenant_rights"]     │              │
  │ primary: "property"   │              │
  │                       ▼              │
  │              To Agents 3, 4, 6       │
  └─────────────────────────────────────────┘

AGENT 3: KNOWLEDGE RETRIEVAL
  Inputs from: Agent 1 (embedding), Agent 2 (domain)
  Outputs to: Agent 5
  Qdrant: statutes_vectors
  LLM: None
  Can fail? No (will return empty if no matches)
  Replaces? Replace if you want different statute source
  ┌─────────────────────────────────────────┐
  │  Embedding + Domain ──────────────────▶│
  │  From A1 + A2  ┌──────────────────┐   │
  │         ─────▶│ SEARCH QDRANT   │   │
  │         │     │ statutes_       │   │
  │         │     │ vectors         │   │
  │         │     │ Filter:         │   │
  │         │     │ domain=property │   │
  │         │     │                  │   │
  │         │     │ Returns 5       │   │
  │         │     │ statutes        │   │
  │         │     └────────┬─────────┘   │
  │         │              │              │
  │ 5 Statutes with Scores                │
  │                       │              │
  │ 1. Rent Control      │              │
  │    (0.78)            │              │
  │ 2. Tenancy Protect   │              │
  │    (0.74)            │              │
  │ [3 more...]          │              │
  │                       ▼              │
  │               To Agent 5              │
  └─────────────────────────────────────────┘

AGENT 4: CASE SIMILARITY
  Inputs from: Agent 1 (embedding), Agent 2 (domain)
  Outputs to: Agent 5
  Qdrant: case_law_vectors
  LLM: None
  Can fail? No (will return empty if no matches)
  Replaces? Replace if you want different case source
  ┌─────────────────────────────────────────┐
  │  Embedding + Domain ──────────────────▶│
  │  From A1 + A2  ┌──────────────────┐   │
  │         ─────▶│ SEARCH QDRANT   │   │
  │         │     │ case_law_       │   │
  │         │     │ vectors         │   │
  │         │     │ Filter:         │   │
  │         │     │ domain=property │   │
  │         │     │                  │   │
  │         │     │ Returns 5       │   │
  │         │     │ cases           │   │
  │         │     └────────┬─────────┘   │
  │         │              │              │
  │ 5 Cases with Scores                   │
  │                       │              │
  │ 1. State v. Landlord │              │
  │    (0.76)            │              │
  │ 2. Tenant Union v.   │              │
  │    Owner (0.72)      │              │
  │ [3 more...]          │              │
  │                       ▼              │
  │               To Agent 5              │
  └─────────────────────────────────────────┘

AGENT 5: REASONING
  Inputs from: Agent 1 (query), A3 (statutes), A4 (cases)
  Outputs to: Agent 6
  Qdrant: None
  LLM: Ollama (Llama 3 / Mistral)
  Can fail? Yes (LLM error, no docs to reason on)
  Fallback: Return "insufficient information"
  Replaces? Replace if you want different LLM provider
  ┌──────────────────────────────────────────┐
  │  Query + Statutes + Cases ──────────────▶│
  │  From A1, A3, A4   ┌─────────────────┐  │
  │         ────────▶│ SEND TO LLM     │  │
  │         │        │ Ollama          │  │
  │         │        │                  │  │
  │         │        │ System Prompt:  │  │
  │         │        │ "Only use these │  │
  │         │        │  docs, cite     │  │
  │         │        │  specific laws" │  │
  │         │        │                  │  │
  │         │        │ User Prompt:    │  │
  │         │        │ "Explain user's │  │
  │         │        │  rights using   │  │
  │         │        │  these docs"    │  │
  │         │        │                  │  │
  │         │        │ LLM generates   │  │
  │         │        │ explanation     │  │
  │         │        └────────┬────────┘  │
  │         │                 │            │
  │ Plain-Language Explanation             │
  │                       │               │
  │ "Based on Rent       │               │
  │  Control Act...      │               │
  │  You have rights:    │               │
  │  1. Notice must be   │               │
  │  2. Court order...   │               │
  │  Cited: [cases]"     │               │
  │                       ▼               │
  │                To Agent 6              │
  └──────────────────────────────────────────┘

AGENT 6: RECOMMENDATION
  Inputs from: Agent 1 (embedding), A5 (explanation)
  Outputs to: Agent 7
  Qdrant: civic_process_vectors
  LLM: None
  Can fail? No (will return empty if no matches)
  Replaces? Replace if you want different civic actions
  ┌──────────────────────────────────────────┐
  │  Embedding + Explanation ──────────────▶│
  │  From A1 + A5   ┌──────────────────┐   │
  │         ──────▶│ SEARCH QDRANT   │   │
  │         │      │ civic_process_ │   │
  │         │      │ vectors         │   │
  │         │      │                  │   │
  │         │      │ Returns 5       │   │
  │         │      │ civic actions   │   │
  │         │      └────────┬────────┘   │
  │         │               │             │
  │ 5 Recommendations                      │
  │                       │              │
  │ 1. File with         │              │
  │    Magistrate        │              │
  │    (0.81)            │              │
  │ 2. File in Court     │              │
  │    (0.78)            │              │
  │ [3 more...]          │              │
  │                       ▼              │
  │               To Agent 7              │
  └──────────────────────────────────────────┘

AGENT 7: ETHICS
  Inputs from: Agent 5 (explanation), A6 (recommendations)
  Outputs to: Agent 8
  Qdrant: None
  LLM: None
  Can fail? No (always validates)
  Replaces? Replace if you want different safety rules
  ┌──────────────────────────────────────────┐
  │  Explanation + Recommendations ────────▶│
  │  From A5 + A6    ┌─────────────────┐   │
  │         ───────▶│ VALIDATE       │   │
  │         │       │ • No "sue"?    │   │
  │         │       │ • No advice?   │   │
  │         │       │ • Safe recs?   │   │
  │         │       │ • Add disclam? │   │
  │         │       └────────┬───────┘   │
  │         │                │            │
  │ Safety Validation Result               │
  │                       │              │
  │ approved: true        │              │
  │ issues: []            │              │
  │ disclaimers: [...]    │              │
  │                       ▼              │
  │                To Agent 8             │
  └──────────────────────────────────────────┘

AGENT 8: MEMORY
  Inputs from: Complete context
  Outputs to: User + Qdrant storage
  Qdrant: Write to case_memory_vectors + user_interaction_memory
  LLM: None
  Can fail? No (graceful degradation)
  Replaces? Replace if you want different storage strategy
  ┌──────────────────────────────────────────┐
  │  All Context ──────────────────────────▶│
  │  Statutes, Cases, Recs   ┌────────────┐ │
  │         ──────────────▶│ STORE IN  │ │
  │         │             │ QDRANT    │ │
  │         │             │           │ │
  │         │             │ Save to:  │ │
  │         │             │ case_     │ │
  │         │             │ memory_   │ │
  │         │             │ vectors   │ │
  │         │             │           │ │
  │         │             │ + user_   │ │
  │         │             │ interact  │ │
  │         │             │ _memory   │ │
  │         │             └────┬──────┘ │
  │         │                  │        │
  │ Case Stored + ID Generated         │
  │                       │           │
  │ case_20260120_00847   │           │
  │ stored: true          │           │
  │ retrieval_enabled     │           │
  │                       ▼           │
  │        To User + Future Queries    │
  └──────────────────────────────────────────┘

```

---

## 🗺️ Data Flow Map

```
USER INPUT
    │
    ▼
┌─────────────────────┐
│  INTAKE AGENT       │  ← Normalizes query
│                     │  ← Generates embedding
└──────────┬──────────┘
           │
           ▼ [embedding]
┌─────────────────────┐
│ CLASSIFICATION      │  ← Searches legal_taxonomy_vectors
│ AGENT               │  ← Identifies domain
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼ [embedding + domain]
┌──────────┐   ┌──────────────┐
│KNOWLEDGE │   │ CASE         │  ← Search statutes_vectors
│RETRIEVAL │   │ SIMILARITY   │  ← Search case_law_vectors
│AGENT     │   │ AGENT        │
└────┬─────┘   └──────┬───────┘
     │                │
     ▼ [statutes]     ▼ [cases]
     │                │
     └────────┬───────┘
              │
              ▼ [query + statutes + cases]
        ┌──────────────┐
        │ REASONING    │  ← LLM generates explanation
        │ AGENT        │  ← Grounded in retrieval
        └──────┬───────┘
               │
               ▼ [explanation]
        ┌─────────────────────────┐
        │ RECOMMENDATION AGENT    │  ← Search civic_process_vectors
        │                         │  ← Suggests civic actions
        └──────┬──────────────────┘
               │
               ▼ [recommendations]
        ┌─────────────────────────┐
        │ ETHICS AGENT            │  ← Validates safety
        │                         │  ← Adds disclaimers
        └──────┬──────────────────┘
               │
               ▼ [approved output]
        ┌─────────────────────────┐
        │ MEMORY AGENT            │  ← Stores in case_memory_vectors
        │                         │  ← Stores in user_interaction_memory
        └──────┬──────────────────┘
               │
               ▼
        USER RECEIVES ANSWER
               │
               ├─ Legal information
               ├─ Relevant statutes
               ├─ Similar cases
               ├─ Civic actions to take
               ├─ Disclaimers
               └─ Case ID for reference
```

---

## 💾 Data Storage Architecture

```
QDRANT DATABASE
├── Collection 1: legal_taxonomy_vectors
│   ├── Stores: Legal domain taxonomy
│   ├── Used by: Classification Agent
│   ├── Vector Size: 384 dimensions
│   └── Typical Size: ~100-200 entries
│
├── Collection 2: statutes_vectors
│   ├── Stores: Legal statutes and acts
│   ├── Used by: Knowledge Retrieval Agent
│   ├── Vector Size: 384 dimensions
│   ├── Metadata: title, section, content, domain, jurisdiction
│   └── Typical Size: 1000-10000+ entries
│
├── Collection 3: case_law_vectors
│   ├── Stores: Court cases and judgments
│   ├── Used by: Case Similarity Agent
│   ├── Vector Size: 384 dimensions
│   ├── Metadata: case_name, court, year, summary, citation
│   └── Typical Size: 1000-5000+ entries
│
├── Collection 4: civic_process_vectors
│   ├── Stores: Civic procedures and actions
│   ├── Used by: Recommendation Agent
│   ├── Vector Size: 384 dimensions
│   ├── Metadata: action, steps, authority, documents, timeline
│   └── Typical Size: 200-500+ entries
│
├── Collection 5: case_memory_vectors
│   ├── Stores: Long-term case memory
│   ├── Used by: Memory Agent + Future queries
│   ├── Vector Size: 384 dimensions
│   ├── Metadata: query, domains, statutes, cases, explanation
│   └── Typical Size: Grows over time (unlimited)
│
└── Collection 6: user_interaction_memory
    ├── Stores: User interaction history
    ├── Used by: Analytics + personalization
    ├── Vector Size: 384 dimensions
    ├── Metadata: user_id, session_id, query, domains, timestamp
    └── Typical Size: Grows over time (unlimited)
```

---

## 🎓 What You've Built - The Complete Picture

```
╔════════════════════════════════════════════════════════════════╗
║                 NYAYAAI SYSTEM CAPABILITIES                    ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ INPUT:                                                         ║
║ • Any legal question from a citizen                            ║
║ • Natural language (English)                                   ║
║ • No legal expertise required                                  ║
║                                                                ║
║ PROCESSING:                                                    ║
║ • 8 specialized agents orchestrated via LangGraph              ║
║ • Semantic search using Qdrant vector database                 ║
║ • Evidence-based reasoning (no hallucination)                  ║
║ • Safety validation on all outputs                             ║
║                                                                ║
║ OUTPUT:                                                        ║
║ ✓ Relevant laws (statutes/acts)                                ║
║ ✓ Similar past cases (precedents)                              ║
║ ✓ Plain-language explanation                                   ║
║ ✓ Specific civic actions to take                               ║
║ ✓ Step-by-step instructions                                    ║
║ ✓ Legal authority information                                  ║
║ ✓ Required documents                                           ║
║ ✓ Timelines and costs                                          ║
║ ✓ Appropriate disclaimers                                      ║
║ ✓ Confidence scores                                            ║
║ ✓ Case reference ID                                            ║
║                                                                ║
║ GUARANTEE:                                                     ║
║ • NO made-up laws or cases                                     ║
║ • NO legal advice given                                        ║
║ • NO litigation strategies                                     ║
║ • 100% TRACEABLE (all claims cited)                            ║
║                                                                ║
║ SCALABILITY:                                                   ║
║ • Can handle thousands of queries                              ║
║ • Learns from every query                                      ║
║ • Supports ~3 second response time                             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 📊 Complexity Summary

```
ARCHITECTURE COMPLEXITY: 8 Agents

Agent 1 (Intake)        - SIMPLE        (text normalization)
Agent 2 (Classification) - SIMPLE        (semantic search)
Agent 3 (Knowledge)     - SIMPLE        (semantic search)
Agent 4 (Cases)         - SIMPLE        (semantic search)
Agent 5 (Reasoning)     - COMPLEX       (LLM with constraints)
Agent 6 (Recommend)     - SIMPLE        (semantic search)
Agent 7 (Ethics)        - MEDIUM        (validation logic)
Agent 8 (Memory)        - SIMPLE        (storage operation)
────────────────────────────────────────
OVERALL:                - MODERATE      (well-orchestrated)

DATABASE COMPLEXITY: 6 Collections

legal_taxonomy_vectors      - Moderate (domain index)
statutes_vectors            - High (large corpus)
case_law_vectors            - High (large corpus)
civic_process_vectors       - Moderate (action index)
case_memory_vectors         - Growing (learning system)
user_interaction_memory     - Growing (analytics)
────────────────────────────────────────
OVERALL:                    - High (comprehensive)

INTEGRATION POINTS: 3 Main Components

FastAPI Backend             - REST API
Qdrant Vector DB            - Vector search
Ollama LLM                  - Local inference
────────────────────────────────────────
OVERALL:                    - Elegant (minimal dependencies)
```

