#!/bin/bash
# QUICK FIX COMMANDS - Copy and paste these

echo "================================"
echo "NYAYAAI ERROR NONE FIX"
echo "================================"
echo ""

# STEP 1: Pull recommended model
echo "[STEP 1] Pulling MISTRAL model..."
ollama pull mistral
echo "✓ Done"
echo ""

# STEP 2: Check available models
echo "[STEP 2] Checking available models..."
ollama list
echo ""

# STEP 3: Instructions for config change
echo "[STEP 3] Update config/settings.py"
echo "Change: ollama_model = \"llama3\""
echo "To:     ollama_model = \"mistral\""
echo ""

# STEP 4: Restart services
echo "[STEP 4] Restarting services..."
echo "In separate terminals, run:"
echo ""
echo "Terminal 1:"
echo "  ollama serve"
echo ""
echo "Terminal 2:"
echo "  python -m uvicorn api.main:app --reload"
echo ""
echo "Terminal 3:"
echo "  streamlit run frontend/app.py"
echo ""

# STEP 5: Test
echo "[STEP 5] Testing..."
echo "Visit: http://localhost:8501"
echo "Try query: How do I file an RTI application?"
echo ""
echo "================================"
echo "✓ All steps complete!"
echo "================================"
