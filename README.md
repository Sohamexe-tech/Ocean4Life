# Disaster Relief Resource Scout

## Feature 2: Identify Unique Incidents

An agentic AI system that eliminates duplicates and cross-references disaster reports for accuracy using real-time LLM extraction and semantic clustering.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Sample Data
```bash
python data_collectors/realtime_simulator.py
```

### 3. Run System
```bash
python main.py
```

## Features

### ✅ Real-Time LLM Extraction
- Uses Groq's Llama 3.3 70B for text extraction
- Converts chaotic posts into structured JSON
- Falls back to keyword extraction if needed

### ✅ Semantic Deduplication
- DBSCAN clustering on embeddings
- Groups similar reports with different wording
- Configurable similarity threshold (default: 0.75)

### ✅ Cross-Reference Scoring
- Confidence based on:
  - Number of corroborating reports
  - Source diversity
  - Urgency consensus

### ✅ Priority Ranking
- Incidents ranked by confidence score
- Visual indicators for quick assessment

## Project Structure
```
disaster-relief-agent/
├── data/
│   └── sample_posts.txt       # Disaster reports
├── data_collectors/
│   ├── __init__.py
│   └── realtime_simulator.py  # Data generator
├── agents/
│   ├── extract_agent.py       # LLM extraction (Groq)
│   └── dedupe_agent.py        # Deduplication + cross-reference
├── models/
│   └── schema.py              # Data models
├── outputs/
│   └── verified_incidents.json # Results
├── main.py                     # Main runner
├── requirements.txt
└── README.md
```

## Output Example
```
🚨 DISASTER RELIEF RESOURCE SCOUT - FEATURE 2
======================================================================

✅ Identified 3 unique incidents
📊 Eliminated 7 duplicates (70.0%)

🟢 #1 [INC_A7B3C2D1]
   Type: FOOD
   Location: Andheri East, Mumbai
   Urgency: 🔴🔴🔴🔴🔴 (5/5)
   📊 Corroboration: 4 reports from 4 sources
   🎯 Confidence: 100.0%
   📱 Sources: twitter, whatsapp, reddit, facebook
```

## Technologies

- **LLM**: Groq (Llama 3.3 70B)
- **Embeddings**: sentence-transformers
- **Clustering**: DBSCAN
- **Validation**: Pydantic

## Hackathon Demo

**"Our system processes chaotic social media reports and converts them into verified, actionable intelligence through semantic deduplication and multi-source cross-referencing."**

## Authors

Built for Disaster Relief Hackathon 2026