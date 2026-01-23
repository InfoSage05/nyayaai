"""Streamlit frontend for NyayaAI - SIMPLIFIED."""
import streamlit as st
import requests
from typing import Dict, Any

# Page config
st.set_page_config(
    page_title="NyayaAI - Legal & Civic Information",
    page_icon="⚖️",
    layout="wide"
)

# API URL
API_URL = "http://localhost:8000"


def process_query_simple(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Call the SIMPLE API endpoint (ONE LLM call)."""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/query/simple",
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
    st.markdown("### Legal & Civic Information Assistant")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        NyayaAI helps you:
        - Understand laws and rights
        - Navigate civic processes
        - Get helpful information
        
        **Powered by:**
        - 📚 Qdrant (Legal Database)
        - 🌐 Tavily (Web Search)
        - 🤖 Groq LLM
        """)
        
        st.markdown("---")
        st.warning("""
        **⚠️ Disclaimer**
        
        This provides legal **information** only, 
        NOT legal advice. Consult a qualified 
        lawyer for specific legal matters.
        """)
    
    # Query input
    query = st.text_area(
        "Ask your question:",
        height=100,
        placeholder="e.g., How do I file a PIL? What are my rights under RTI?"
    )
    
    if st.button("🔍 Get Answer", type="primary"):
        if not query.strip():
            st.error("Please enter a question")
        else:
            with st.spinner("Finding information..."):
                result = process_query_simple(query)
            
            if result.get('error'):
                st.error(f"Error: {result['error']}")
            elif result.get('response'):
                display_simple_result(result)
            else:
                st.warning("No response received. Please try again.")


def display_simple_result(result: Dict[str, Any]):
    """Display simple pipeline result."""
    st.markdown("---")
    
    # Main response (the LLM output)
    response = result.get('response', '')
    if response:
        st.markdown(response)
    
    # Sources summary
    sources = result.get('sources', {})
    if sources:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Database Docs", sources.get('database_docs', 0))
        with col2:
            st.metric("🌐 Web Results", sources.get('web_results', 0))
        with col3:
            status = sources.get('retrieval_status', 'unknown')
            status_icon = "✅" if status == "hit" else "⚠️"
            st.metric("Status", f"{status_icon} {status}")
    
    # Show retrieved sources if available
    retrieved_docs = result.get('retrieved_docs', [])
    web_results = result.get('web_results', [])
    
    if retrieved_docs or web_results:
        with st.expander("📖 View Sources", expanded=False):
            if retrieved_docs:
                st.markdown("**From Database:**")
                for doc in retrieved_docs[:3]:
                    doc_type = doc.get('type', 'doc').upper()
                    title = doc.get('title', 'Document')
                    source = doc.get('source', '')
                    st.markdown(f"- **[{doc_type}]** {title} _{source}_")
            
            if web_results:
                st.markdown("**From Web:**")
                for web in web_results[:3]:
                    title = web.get('title', 'Web Source')
                    url = web.get('url', '')
                    if url:
                        st.markdown(f"- [{title}]({url})")
                    else:
                        st.markdown(f"- {title}")
    
    # Case ID footer
    if result.get('case_id'):
        st.caption(f"Case ID: {result['case_id']}")


if __name__ == "__main__":
    main()