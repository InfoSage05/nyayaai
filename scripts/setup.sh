#!/bin/bash
# Setup script for NyayaAI

echo "NyayaAI Setup Script"
echo "==================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [ -z "$python_version" ]; then
    echo "ERROR: Python 3.11+ is required"
    exit 1
fi
echo "✓ Python $python_version found"

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is required"
    exit 1
fi
echo "✓ Docker found"

# Check Ollama
echo "Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "WARNING: Ollama not found. Please install from https://ollama.ai"
else
    echo "✓ Ollama found"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Start Qdrant
echo "Starting Qdrant..."
docker-compose up -d qdrant
sleep 5
echo "✓ Qdrant started"

# Setup collections
echo "Setting up Qdrant collections..."
python -m nyayaai.database.setup_collections
echo "✓ Collections created"

# Ingest sample data
echo "Ingesting sample data..."
python -m nyayaai.database.ingest_sample_data
echo "✓ Sample data ingested"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start Ollama: ollama serve"
echo "2. Pull model: ollama pull llama3"
echo "3. Start API: uvicorn nyayaai.api.main:app --reload"
echo "4. (Optional) Start frontend: streamlit run nyayaai/frontend/app.py"
