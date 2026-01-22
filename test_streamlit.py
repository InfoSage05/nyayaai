#!/usr/bin/env python3
"""
Test script to verify Streamlit app can be imported and basic functionality works.
Run this before starting the Streamlit server.
"""
import sys
import os

print("Testing Streamlit Frontend...")
print("=" * 50)

try:
    # Test if streamlit is installed
    import streamlit as st
    print("✓ Streamlit is installed")
    
    # Test if requests is installed
    import requests
    print("✓ Requests library is installed")
    
    # Test importing the app
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from frontend.app import process_query, display_results, main
    print("✓ Streamlit app module imported successfully")
    
    # Test the process_query function structure
    print("\nTesting function signatures...")
    import inspect
    
    sig = inspect.signature(process_query)
    print(f"✓ process_query signature: {sig}")
    
    sig = inspect.signature(display_results)
    print(f"✓ display_results signature: {sig}")
    
    print("\n" + "=" * 50)
    print("✅ Streamlit frontend code is ready!")
    print("\nTo start the Streamlit app:")
    print("  1. Make sure API is running: uvicorn api.main:app --reload")
    print("  2. Run: streamlit run frontend/app.py")
    print("  3. Open browser to: http://localhost:8501")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nPlease install missing dependencies:")
    print("  pip install streamlit requests")
    sys.exit(1)
except Exception as e:
    print(f"\n⚠ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
