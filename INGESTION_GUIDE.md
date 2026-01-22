# NyayaAI Unified Data Ingestion Guide

## Overview

The unified ingestion script (`ingest_all_sources.py`) sets up all Qdrant collections and ingests legal data from multiple sources in a single run.

## Quick Start

### Run Complete Ingestion

```bash
python ingest_all_sources.py
```

This single command will:
1. ✅ Set up all Qdrant collections
2. ✅ Ingest from Data.gov.in (government datasets)
3. ✅ Ingest from IndiaCode (acts and statutes)
4. ✅ Ingest from Supreme Court of India (judgments)
5. ✅ Ingest from WorldLII/IndianLII (case law)
6. ✅ Ingest from Law Commission of India (reports)
7. ✅ Ingest sample data (fallback)
8. ✅ Verify ingestion and report statistics

## What Gets Ingested

### Data Sources

1. **Data.gov.in**
   - Government legal datasets
   - Constitutional framework data
   - Court portal information
   - Justice sector statistics

2. **IndiaCode**
   - Right to Information Act
   - Consumer Protection Act
   - Constitution of India
   - Other acts and statutes

3. **Supreme Court of India**
   - Landmark judgments
   - Recent case law
   - Legal precedents

4. **WorldLII/IndianLII**
   - International case law
   - Indian case law database
   - Cross-jurisdictional cases

5. **Law Commission of India**
   - Legal reports
   - Reform recommendations
   - Policy documents

6. **Sample Data**
   - Reference legal documents
   - Common legal procedures
   - Fallback data for testing

### Collections Created

- `legal_taxonomy_vectors` - Legal domain classification
- `statutes_vectors` - Acts, statutes, regulations
- `case_law_vectors` - Court judgments and cases
- `civic_process_vectors` - Civic procedures and processes
- `case_memory_vectors` - Long-term case memory
- `user_interaction_memory` - User interaction history
- `case_similarity_vectors` - Case similarity data

## Prerequisites

1. **Qdrant Running**
   ```bash
   docker compose up -d qdrant
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables** (Optional)
   - `GROQ_API_KEY` - For LLM synthesis (optional, has fallback)

## Usage Examples

### Basic Usage

```bash
# Run complete ingestion
python ingest_all_sources.py
```

### Individual Stages

You can also run individual ingestion scripts:

```bash
# Setup collections only
python -m database.setup_collections

# Ingest sample data only
python -m database.ingest_sample_data

# Ingest from specific connector
python -m connectors.data_gov_connector
```

## Output

The script provides detailed logging:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NYAYAAI UNIFIED DATA INGESTION                           ║
║                    Complete Vector Database Setup                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

STAGE 1: SETTING UP COLLECTIONS
================================================================================
  ✓ legal_taxonomy_vectors: 0 vectors
  ✓ statutes_vectors: 0 vectors
  ...

STAGE 2: INGESTING FROM DATA.GOV.IN
================================================================================
Dataset 1/3: https://data.gov.in/api/...
  ✓ Ingested dataset

...

FINAL INGESTION SUMMARY
================================================================================
📋 SOURCES PROCESSED:
  • Data.gov.in:        3 datasets
  • IndiaCode:          3 acts
  • Supreme Court:      1 cases
  • WorldLII/IndianLII: 3 cases
  • Law Commission:     2 reports
  • Sample Data:        4 collections

📦 COLLECTIONS STATUS:
  ✓ legal_taxonomy_vectors: 150 vectors
  ✓ statutes_vectors: 500 vectors
  ✓ case_law_vectors: 200 vectors
  ...

⏱️  PERFORMANCE:
  • Total Time: 120.45 seconds (2.01 minutes)
  • Vectors/sec: 7.1

✅ UNIFIED INGESTION COMPLETE!
```

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**
   - Ensure Qdrant is running: `docker compose ps`
   - Check connection: `curl http://localhost:6333/collections`

2. **Import Errors**
   - Ensure you're in the project root directory
   - Install dependencies: `pip install -r requirements.txt`

3. **Rate Limiting**
   - The script includes delays between requests
   - If you encounter rate limits, increase delays in the script

4. **Empty Collections**
   - Some sources may fail due to network issues
   - Sample data will always be ingested as fallback
   - Check logs for specific error messages

### Verification

After ingestion, verify data:

```python
from database.qdrant_client import qdrant_manager

# Check collection info
info = qdrant_manager.get_collection_info("statutes_vectors")
print(f"Statutes: {info.get('points_count', 0)} vectors")
```

## Next Steps

After successful ingestion:

1. **Start the API Server**
   ```bash
   python main.py
   ```

2. **Start the Streamlit Frontend**
   ```bash
   streamlit run frontend/app.py
   ```

3. **Test a Query**
   - Open http://localhost:8501
   - Enter a legal query
   - View results with retrieved evidence

## Adding More Data Sources

To add more data sources:

1. **Add URLs to Configuration**
   Edit `ingest_all_sources.py`:
   ```python
   NEW_SOURCE_URLS = [
       "https://example.com/legal-data",
       ...
   ]
   ```

2. **Create Connector Function**
   ```python
   def stage_X_new_source() -> Tuple[int, List[str]]:
       # Implementation
   ```

3. **Add to Main Pipeline**
   ```python
   new_count, new_errors = stage_X_new_source()
   ```

## Notes

- The script is idempotent - safe to run multiple times
- Existing collections are not deleted, only new data is added
- Sample data ensures minimum viable data even if external sources fail
- All ingestion is logged for debugging
