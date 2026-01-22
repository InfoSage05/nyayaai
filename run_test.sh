#!/bin/bash
# Test script to verify the system is ready to run

echo "=========================================="
echo "NyayaAI System Test"
echo "=========================================="
echo ""

# Check Python
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ Python found: $PYTHON_VERSION"
else
    echo "   ✗ Python3 not found"
    exit 1
fi

# Check if virtual environment exists
echo ""
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "   ✓ Virtual environment found"
    echo "   Activate with: source venv/bin/activate"
else
    echo "   ⚠ Virtual environment not found"
    echo "   Create with: python3 -m venv venv"
fi

# Check dependencies
echo ""
echo "3. Checking key dependencies..."
python3 -c "import streamlit" 2>/dev/null && echo "   ✓ streamlit" || echo "   ✗ streamlit (install: pip install streamlit)"
python3 -c "import fastapi" 2>/dev/null && echo "   ✓ fastapi" || echo "   ✗ fastapi (install: pip install fastapi uvicorn)"
python3 -c "import qdrant_client" 2>/dev/null && echo "   ✓ qdrant_client" || echo "   ✗ qdrant_client (install: pip install qdrant-client)"
python3 -c "import groq" 2>/dev/null && echo "   ✓ groq" || echo "   ⚠ groq (optional, install: pip install groq)"

# Check Docker
echo ""
echo "4. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✓ Docker found"
    if docker ps &> /dev/null; then
        echo "   ✓ Docker is running"
        # Check if Qdrant container is running
        if docker ps | grep -q qdrant; then
            echo "   ✓ Qdrant container is running"
        else
            echo "   ⚠ Qdrant container not running"
            echo "   Start with: docker compose up -d qdrant"
        fi
    else
        echo "   ⚠ Docker is not running"
    fi
else
    echo "   ⚠ Docker not found (needed for Qdrant)"
fi

# Check .env file
echo ""
echo "5. Checking configuration..."
if [ -f ".env" ]; then
    echo "   ✓ .env file found"
    if grep -q "GROQ_API_KEY" .env; then
        echo "   ✓ GROQ_API_KEY configured"
    else
        echo "   ⚠ GROQ_API_KEY not found in .env"
    fi
else
    echo "   ⚠ .env file not found"
    echo "   Create .env file with: GROQ_API_KEY=your_key_here"
fi

# Test imports
echo ""
echo "6. Testing Python imports..."
python3 test_streamlit.py 2>&1 | tail -5

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "To start the system:"
echo "  1. Start Qdrant: docker compose up -d qdrant"
echo "  2. Start API server: uvicorn api.main:app --reload"
echo "  3. Start Streamlit: streamlit run frontend/app.py"
