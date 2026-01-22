"""Demo examples for NyayaAI."""
from core.orchestrator import _init_orchestrator

# Sample queries for demonstration
DEMO_QUERIES = [
    "How do I file an RTI application?",
    "What are my rights if I receive a defective product?",
    "How can I file a consumer complaint?",
    "What is the procedure to file an FIR?",
    "What are my fundamental rights under the Constitution?",
    "How do I get a divorce under Hindu Marriage Act?",
    "What are my rights as a worker regarding wages?",
    "How can I access government information?",
]


def run_demo(query: str):
    """Run a demo query."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    orchestrator = _init_orchestrator()
    result = orchestrator.process_query(query)
    
    print(f"Domains: {result.get('domains', [])}")
    print(f"\nExplanation:\n{result.get('explanation', 'N/A')}")
    
    statutes = result.get('statutes', [])
    if statutes:
        print(f"\nRetrieved {len(statutes)} statute(s):")
        for i, statute in enumerate(statutes[:3], 1):
            print(f"  {i}. {statute.get('title', 'N/A')}")
    
    cases = result.get('cases', [])
    if cases:
        print(f"\nRetrieved {len(cases)} case(s):")
        for i, case in enumerate(cases[:3], 1):
            print(f"  {i}. {case.get('case_name', 'N/A')} ({case.get('year', 'N/A')})")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\nRetrieved {len(recommendations)} recommendation(s):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec.get('action', 'N/A')}")
    
    print(f"\nCase ID: {result.get('case_id', 'N/A')}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    print("NyayaAI Demo - Sample Queries")
    print("="*80)
    
    for query in DEMO_QUERIES[:3]:  # Run first 3 queries
        try:
            run_demo(query)
        except Exception as e:
            print(f"Error processing query: {e}\n")
