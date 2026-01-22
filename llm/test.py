"""
Quick test script for GroqLLM synthesis agent.
Run this AFTER setting GROQ_API_KEY in environment.
"""

from groq_client import GroqLLM


def main():
    print("Initializing GroqLLM...")
    
    try:
        llm = GroqLLM()
    except Exception as e:
        print(f"❌ Failed to initialize GroqLLM: {e}")
        return

    print("✅ GroqLLM initialized successfully\n")

    # Sample legal query
    query = "How do I file an RTI application in India?"

    # Mock retrieved statutes (simulate Qdrant output)
    retrieved_statutes = [
        {
            "title": "Right to Information Act, 2005",
            "summary": (
                "The Right to Information Act, 2005 empowers citizens to "
                "request information from public authorities. It mandates "
                "timely response to citizen requests and promotes transparency."
            ),
        }
    ]

    # Mock similar cases (simulate case similarity agent output)
    similar_cases = [
        {
            "case_name": "CBSE v. Aditya Bandopadhyay",
            "outcome": (
                "The Supreme Court held that citizens have the right to access "
                "information held by public authorities, subject to reasonable "
                "restrictions under the RTI Act."
            ),
        }
    ]

    print("Sending synthesis request to Groq...\n")

    # response = llm.synthesize_legal_answer(
    #     query=query,
    #     retrieved_statutes=retrieved_statutes,
    #     similar_cases=similar_cases,
    #     temperature=0.3,
    # )
    response = llm.generate_response("hello")
    print("\nRAW RESPONSE:\n", response)    

    print(response)

    print("===== SYNTHESIS RESPONSE =====\n")
    print("SUMMARY:")
    print(response.get("summary", "N/A"), "\n")

    print("REASONING STEPS:")
    for step in response.get("reasoning_steps", []):
        print("-", step)
    print()

    print("CONFIDENCE LEVEL:")
    print(response.get("confidence_level", "N/A"), "\n")

    print("DISCLAIMERS:")
    for disclaimer in response.get("disclaimers", []):
        print("-", disclaimer)

    print("\n✅ Test completed successfully.")


if __name__ == "__main__":
    main()
