#!/usr/bin/env python
"""Quick test of the None error fix."""
import time
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 70)
print("🧪 TESTING GROQ INTEGRATION - NONE ERROR FIX")
print("=" * 70)
print()

# Wait for API to be ready
print("⏳ Waiting for API to be ready...")
max_retries = 10
for i in range(max_retries):
    try:
        response = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is ready!")
            break
    except:
        if i < max_retries - 1:
            time.sleep(2)
            print(f"   Retry {i+1}/{max_retries-1}...")
        else:
            print("❌ API not responding. Start it first:")
            print("   python -m uvicorn api.main:app --reload")
            exit(1)

print()
print("Testing query: 'What is RTI?'")
print("-" * 70)

try:
    response = requests.post(
        f"{API_URL}/api/v1/query",
        json={"query": "What is RTI?"},
        timeout=60
    )
    
    result = response.json()
    
    print()
    print("Response Status:", response.status_code)
    print()
    
    # Check for errors
    if result.get('error'):
        print(f"❌ ERROR: {result.get('error')}")
    else:
        explanation = result.get('explanation', '')
        
        if not explanation or explanation.strip() == "":
            print("❌ EMPTY/NONE EXPLANATION - Still broken!")
        else:
            print("✅ SUCCESS - Got valid explanation!")
            print()
            print("Explanation (first 200 chars):")
            print(explanation[:200] + "..." if len(explanation) > 200 else explanation)
            print()
            print(f"✅ Query: {result.get('query')}")
            print(f"✅ Statutes: {len(result.get('statutes', []))} found")
            print(f"✅ Cases: {len(result.get('cases', []))} found")
            print(f"✅ Recommendations: {len(result.get('recommendations', []))} found")
    
    print()
    print("=" * 70)
    print("Full Response (pretty printed):")
    print("=" * 70)
    print(json.dumps(result, indent=2)[:500] + "...")
    
except requests.exceptions.Timeout:
    print("❌ TIMEOUT - Query took too long (>60s)")
    print("   Check if Groq API is responding")
    
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR - Can't reach API")
    print("   Start API: python -m uvicorn api.main:app --reload")
    
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 70)
