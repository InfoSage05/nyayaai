"""Enhanced Streamlit frontend for NyayaAI - Modern UI Design."""
import streamlit as st
import requests
import json
from typing import Dict, Any
import time

# Page config with dark theme
st.set_page_config(
    page_title="NyayaAI - Your Personal Legal & Civic Guide",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and modern design
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Title styling */
    h1 {
        color: #ff6b6b;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Query input styling */
    .stTextArea textarea {
        background-color: #2d2d44;
        color: #ffffff;
        border: 2px solid #4a4a6a;
        border-radius: 10px;
        padding: 15px;
        font-size: 16px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #ff6b6b;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #ff5252;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
    }
    
    /* Common query cards */
    .query-card {
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5a 100%);
        border: 1px solid #4a4a6a;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .query-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        border-color: #ff6b6b;
    }
    
    .query-card h3 {
        color: #ff6b6b;
        margin-bottom: 0.5rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d44;
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff6b6b;
        color: white;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #2d2d44;
        border-left: 4px solid #4dabf7;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #2d2d44;
        border-left: 4px solid #ffd43b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Status indicator */
    .status-ready {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #51cf66;
        color: white;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    /* Response section */
    .response-section {
        background-color: #2d2d44;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 2rem;
        border: 1px solid #4a4a6a;
    }
</style>
""", unsafe_allow_html=True)

# API URL
API_URL = "http://localhost:8000"

# Common queries
COMMON_QUERIES = [
    {
        "title": "Tenant Rights",
        "description": "Understand your rights as a tenant regarding rent, eviction, and maintenance",
        "query": "What are my rights as a tenant regarding rent increases and eviction?"
    },
    {
        "title": "Filing an RTI",
        "description": "Learn how to file a Right to Information application",
        "query": "How do I file an RTI application? What is the procedure and fees?"
    },
    {
        "title": "Consumer Complaints",
        "description": "File complaints for defective products or poor service",
        "query": "How do I file a consumer complaint for a defective product?"
    },
    {
        "title": "Traffic Violations",
        "description": "Understand traffic rules, fines, and how to contest violations",
        "query": "What are the penalties for traffic violations and how can I contest them?"
    }
]


def process_query(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Call the API to process a query."""
    try:
        # Try structured endpoint first
        response = requests.post(
            f"{API_URL}/api/v1/query/structured",
            json={"query": query, "user_id": user_id},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Fallback to legacy endpoint
        try:
            response = requests.post(
                f"{API_URL}/api/v1/query",
                json={"query": query, "user_id": user_id},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e2:
            return {"error": str(e2)}


def main():
    """Main Streamlit app."""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📚 About")
        st.markdown("""
        **NyayaAI helps you:**
        - 🔍 Discover applicable laws
        - 📖 Understand legal provisions
        - 🚀 Navigate civic processes
        - ✅ Get evidence-based information
        """)
        
        st.markdown("---")
        st.markdown("**Help & Resources**")
        st.markdown("[Documentation](https://github.com/your-repo) | [Support](mailto:support@nyayaai.com)")
        
        st.markdown("---")
        st.markdown("**⚠️ Disclaimer**")
        st.markdown("""
        This system provides legal information only, 
        not legal advice. Consult a qualified lawyer 
        for specific legal matters.
        """)
    
    # Main content
    st.markdown("# ⚖️ NyayaAI: Your Personal Legal & Civic Guide")
    st.markdown("---")
    
    # Query input section
    st.markdown("### Ask Your Legal or Civic Question:")
    
    # Query input with placeholder examples
    query = st.text_area(
        "",
        height=120,
        placeholder="e.g., How do I file an RTI application?\nWhat are my rights as a tenant?\nHow do I file a consumer complaint?",
        label_visibility="collapsed"
    )
    
    # Action buttons row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        voice_query = st.button("🎤 Voice Query", use_container_width=True)
    
    with col2:
        upload_doc = st.button("☁️ Upload Document (Optional)", use_container_width=True)
    
    with col3:
        select_region = st.button("📍 Select Your Region/State", use_container_width=True)
    
    with col4:
        status_ready = st.markdown('<span class="status-ready">Ready</span>', unsafe_allow_html=True)
    
    # Common queries section
    st.markdown("---")
    st.markdown("### Common Queries & Examples")
    
    # Display common queries as cards
    cols = st.columns(2)
    for idx, common_query in enumerate(COMMON_QUERIES):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                <div class="query-card">
                    <h3>{common_query['title']}</h3>
                    <p>{common_query['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Learn more →", key=f"query_{idx}", use_container_width=True):
                    st.session_state['selected_query'] = common_query['query']
                    st.rerun()
    
    # Handle selected query from common queries
    if 'selected_query' in st.session_state:
        query = st.session_state['selected_query']
        del st.session_state['selected_query']
    
    # Submit button
    st.markdown("---")
    col_submit, col_status = st.columns([3, 1])
    
    with col_submit:
        submit_button = st.button("🔍 Submit Query", type="primary", use_container_width=True)
    
    # Process query
    if submit_button or query:
        if not query.strip():
            st.error("⚠️ Please enter a query")
        else:
            with st.spinner("🔄 Processing your query through multi-agent system..."):
                result = process_query(query)
            
            # Check for errors
            if not result or not isinstance(result, dict):
                st.error("❌ Invalid response from server. Please try again.")
            elif result.get('error'):
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            else:
                display_results(result)


def display_results(result: Dict[str, Any]):
    """Display query results with tabs."""
    st.markdown("---")
    st.markdown("## Your Response:")
    
    # Determine if structured or legacy response
    is_structured = 'llm_reasoned_answer' in result
    
    if is_structured:
        # Structured response with tabs
        tab1, tab2, tab3 = st.tabs(["📖 Legal Explanation", "🎯 Action Steps", "⚠️ Safety Disclaimer"])
        
        with tab1:
            st.markdown("### Legal Explanation")
            llm_answer = result.get('llm_reasoned_answer', {})
            st.markdown(llm_answer.get('summary', 'No explanation available.'))
            
            # Reasoning steps
            reasoning_steps = llm_answer.get('reasoning_steps', [])
            if reasoning_steps:
                st.markdown("#### Reasoning Steps:")
                for i, step in enumerate(reasoning_steps, 1):
                    st.markdown(f"{i}. {step}")
            
            # Evidence
            evidence = result.get('retrieved_evidence', {})
            if evidence:
                st.markdown("---")
                st.markdown("#### 📚 Retrieved Evidence")
                
                statutes = evidence.get('statutes', [])
                if statutes:
                    st.markdown("**Relevant Statutes:**")
                    for statute in statutes[:3]:
                        with st.expander(f"📜 {statute.get('title', 'Unknown')}"):
                            st.markdown(f"**Summary:** {statute.get('summary', 'N/A')}")
                            st.markdown(f"**Source:** {statute.get('source', 'N/A')}")
                            if statute.get('relevance_score'):
                                st.markdown(f"**Relevance:** {statute['relevance_score']:.2f}")
                
                cases = evidence.get('cases', [])
                if cases:
                    st.markdown("**Similar Cases:**")
                    for case in cases[:3]:
                        with st.expander(f"⚖️ {case.get('case_name', 'Unknown')}"):
                            st.markdown(f"**Summary:** {case.get('summary', 'N/A')}")
                            st.markdown(f"**Source:** {case.get('source', 'N/A')}")
                            if case.get('relevance_score'):
                                st.markdown(f"**Relevance:** {case['relevance_score']:.2f}")
            
            # Similar case analysis
            similar_cases = result.get('similar_case_analysis', [])
            if similar_cases:
                st.markdown("---")
                st.markdown("#### 📊 Similar Case Analysis")
                for case_analysis in similar_cases[:2]:
                    with st.expander(f"Case: {case_analysis.get('source', 'Unknown')}"):
                        st.markdown(f"**Context:** {case_analysis.get('case_context', 'N/A')}")
                        st.markdown(f"**What Happened:** {case_analysis.get('what_happened', 'N/A')}")
                        st.markdown(f"**Outcome:** {case_analysis.get('outcome', 'N/A')}")
                        st.markdown(f"**Relevance:** {case_analysis.get('relevance_to_query', 'N/A')}")
        
        with tab2:
            st.markdown("### Action Steps")
            recommendations = result.get('civic_action_recommendations', [])
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"#### {i}. {rec.get('action', 'Unnamed Action')}")
                    st.markdown(f"**Responsible Authority:** {rec.get('responsible_authority', 'N/A')}")
                    st.markdown(f"**Why This Matters:** {rec.get('why_this_matters', 'N/A')}")
                    st.markdown(f"**Next Step:** {rec.get('next_step', 'N/A')}")
                    if rec.get('estimated_timeline'):
                        st.markdown(f"**Estimated Timeline:** {rec['estimated_timeline']}")
                    st.markdown("---")
            else:
                st.info("No specific action steps identified. Please review the legal explanation for guidance.")
        
        with tab3:
            st.markdown("### Safety Disclaimer")
            llm_answer = result.get('llm_reasoned_answer', {})
            disclaimers = llm_answer.get('disclaimers', [])
            
            if disclaimers:
                for disclaimer in disclaimers:
                    st.warning(disclaimer)
            
            st.markdown("""
            **⚠️ Important:**
            - This system provides legal information only, not legal advice
            - Consult a qualified lawyer for specific legal matters
            - Information is based on retrieved documents and may not be complete
            - Laws may vary by jurisdiction and change over time
            """)
            
            # Agent trace
            agent_trace = result.get('agent_trace', {})
            if agent_trace:
                st.markdown("---")
                st.markdown("#### 🔍 Agent Trace (Transparency)")
                st.markdown(f"**Legal Domain:** {agent_trace.get('classification_domain', 'N/A')}")
                st.markdown(f"**Retrieval Summary:** {agent_trace.get('retrieval_summary', 'N/A')}")
                st.markdown(f"**Case Analysis:** {agent_trace.get('case_analysis_summary', 'N/A')}")
                st.markdown(f"**Recommendations:** {agent_trace.get('recommendation_count', 0)}")
    
    else:
        # Legacy response format
        st.markdown("### 📖 Legal Explanation")
        explanation = result.get('explanation', '')
        if explanation:
            st.markdown(explanation)
        else:
            st.warning("No explanation generated.")
        
        # Statutes
        statutes = result.get('statutes', [])
        if statutes:
            st.markdown("### 📜 Relevant Statutes")
            for i, statute in enumerate(statutes[:3], 1):
                with st.expander(f"{i}. {statute.get('title', 'N/A')}"):
                    st.markdown(f"**Act:** {statute.get('act_name', 'N/A')}")
                    st.markdown(f"**Section:** {statute.get('section', 'N/A')}")
                    st.markdown(f"**Content:** {statute.get('content', 'N/A')}")
        
        # Cases
        cases = result.get('cases', [])
        if cases:
            st.markdown("### ⚖️ Similar Cases")
            for i, case in enumerate(cases[:3], 1):
                with st.expander(f"{i}. {case.get('case_name', 'N/A')}"):
                    st.markdown(f"**Court:** {case.get('court', 'N/A')}")
                    st.markdown(f"**Summary:** {case.get('summary', 'N/A')}")
        
        # Recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            st.markdown("### 🎯 Civic Action Recommendations")
            for i, rec in enumerate(recommendations[:3], 1):
                with st.expander(f"{i}. {rec.get('action', 'N/A')}"):
                    st.markdown(f"**Description:** {rec.get('description', 'N/A')}")
                    if rec.get('steps'):
                        st.markdown("**Steps:**")
                        for step in rec['steps']:
                            st.markdown(f"- {step}")
    
    # Case ID footer
    if result.get('case_id'):
        st.markdown("---")
        st.caption(f"Case ID: `{result['case_id']}` | Generated at: {result.get('generated_at', 'N/A')}")


if __name__ == "__main__":
    main()
