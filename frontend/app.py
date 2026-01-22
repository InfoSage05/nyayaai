"""Streamlit frontend for NyayaAI."""
import streamlit as st
import requests
import json
from typing import Dict, Any

# Page config
st.set_page_config(
    page_title="NyayaAI - Legal Rights & Civic Access",
    page_icon="⚖️",
    layout="wide"
)

# API URL
API_URL = "http://localhost:8000"


def process_query(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Call the API to process a query."""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/query",
            json={"query": query, "user_id": user_id},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main Streamlit app."""
    st.title("⚖️ NyayaAI")
    st.markdown("### Multi-Agent Legal Rights & Civic Access System")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        NyayaAI helps you:
        - Discover applicable laws
        - Understand legal provisions
        - Navigate civic processes
        - Get evidence-based information
        """)
        
        st.markdown("---")
        st.markdown("**⚠️ Disclaimer**")
        st.markdown("""
        This system provides legal information only, 
        not legal advice. Consult a qualified lawyer 
        for specific legal matters.
        """)
    
    # Query input
    query = st.text_area(
        "Enter your legal query:",
        height=100,
        placeholder="e.g., How do I file an RTI application? What are my rights if I receive a defective product?"
    )
    
    if st.button("Submit Query", type="primary"):
        if not query.strip():
            st.error("Please enter a query")
        else:
            with st.spinner("Processing your query through multi-agent system..."):
                result = process_query(query)
            
            # Check for errors in response
            if not result or not isinstance(result, dict):
                st.error("Invalid response from server. Please try again.")
            elif result.get('error'):
                st.error(f"Error: {result.get('error', 'Unknown error')}")
            elif not result.get('explanation') or result.get('explanation').strip() == "":
                st.warning("No explanation generated. The system may still be processing.")
            else:
                display_results(result)


def display_results(result: Dict[str, Any]):
    """Display query results."""
    st.markdown("---")
    
    # Query info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Query:** {result.get('query', 'N/A')}")
    with col2:
        if result.get('case_id'):
            st.markdown(f"**Case ID:** `{result['case_id']}`")
    
    # Domains
    domains = result.get('domains', [])
    if domains:
        st.markdown(f"**Legal Domains:** {', '.join(domains)}")
    
    st.markdown("---")
    
    # Explanation
    explanation = result.get('explanation', '')
    if explanation:
        st.markdown("### 📖 Legal Explanation")
        st.markdown(explanation)
    
    # Statutes
    statutes = result.get('statutes', [])
    if statutes:
        st.markdown("### 📜 Relevant Statutes")
        for i, statute in enumerate(statutes[:3], 1):
            with st.expander(f"{i}. {statute.get('title', 'N/A')}"):
                st.markdown(f"**Act:** {statute.get('act_name', 'N/A')}")
                st.markdown(f"**Section:** {statute.get('section', 'N/A')}")
                st.markdown(f"**Content:** {statute.get('content', 'N/A')}")
                st.markdown(f"**Similarity Score:** {statute.get('score', 0):.3f}")
    
    # Cases
    cases = result.get('cases', [])
    if cases:
        st.markdown("### ⚖️ Similar Cases")
        for i, case in enumerate(cases[:3], 1):
            with st.expander(f"{i}. {case.get('case_name', 'N/A')} ({case.get('year', 'N/A')})"):
                st.markdown(f"**Court:** {case.get('court', 'N/A')}")
                st.markdown(f"**Citation:** {case.get('citation', 'N/A')}")
                st.markdown(f"**Summary:** {case.get('summary', 'N/A')}")
                if case.get('key_points'):
                    st.markdown(f"**Key Points:** {', '.join(case['key_points'])}")
                st.markdown(f"**Similarity Score:** {case.get('score', 0):.3f}")
    
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
                st.markdown(f"**Authority:** {rec.get('authority', 'N/A')}")
                st.markdown(f"**Timeline:** {rec.get('timeline', 'N/A')}")
                st.markdown(f"**Cost:** {rec.get('cost', 'N/A')}")
    
    # Retrieval Evidence
    evidence = result.get('retrieval_evidence', {})
    if evidence:
        st.markdown("---")
        st.markdown("### 🔍 Retrieval Evidence")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Statutes", evidence.get('statutes_count', 0))
        with col2:
            st.metric("Cases", evidence.get('cases_count', 0))
        with col3:
            st.metric("Recommendations", evidence.get('recommendations_count', 0))
    
    # Disclaimers
    disclaimers = result.get('disclaimers', {})
    if disclaimers.get('safety') or disclaimers.get('standard'):
        st.markdown("---")
        if disclaimers.get('safety'):
            st.warning(disclaimers['safety'])
        if disclaimers.get('standard'):
            st.info(disclaimers['standard'])


if __name__ == "__main__":
    main()
