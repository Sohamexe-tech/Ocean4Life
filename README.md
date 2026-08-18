# 🌊 OceanShield AI

**AI-Powered Crowdsourced Ocean Hazard Monitoring & Response**

---

## Problem Statement

Ocean and coastal hazards—including flooding, storm surge, high waves, erosion, and pollution—can be detected from citizen reports, social media, news, and other data sources. However, information is often:

- **Fragmented** across multiple platforms and sources
- **Duplicated** with similar reports appearing multiple times
- **Unverified** with unclear credibility or accuracy
- **Unstructured** making it difficult to extract actionable intelligence

**OceanShield AI** aims to aggregate, verify, and prioritize ocean hazard information in real-time to support coastal authorities, emergency responders, and citizens.

---

## Current Status: Phase 1

This is **Phase 1** of the OceanShield AI project. The foundation is built from an existing Disaster Relief Agent system, which has proven AI-powered extraction and deduplication capabilities. We are adapting this for ocean and coastal hazards while maintaining backward compatibility and existing functionality.

### ✅ Phase 1 Objectives (Current)

1. ✅ Understand and preserve existing system architecture
2. ✅ Remove hardcoded secrets and establish secure credential handling
3. ✅ Rebrand application to OceanShield AI (user-facing)
4. ✅ Introduce ocean hazard taxonomy
5. ✅ Prepare data model for ocean hazards
6. ✅ Create demo ocean hazard dataset
7. ✅ Document system architecture
8. ⏳ Test and verify functionality

### 📋 Current Foundation

OceanShield AI currently contains proven functionality from the Disaster Relief Agent:

- **LLM-based Information Extraction** - Uses Groq's Llama 3.3 70B to extract structured data from unstructured text
- **Semantic Deduplication** - DBSCAN clustering removes duplicate reports automatically
- **Cross-Source Verification** - Combines evidence from multiple sources for confidence scoring
- **Confidence Scoring** - Rates incidents based on corroboration and source diversity
- **News Integration** - Aggregates real-time news from Google News RSS
- **Geocoding** - Maps incidents to geographic coordinates using Nominatim
- **Leaflet Map Dashboard** - Interactive web-based visualization
- **Flask API** - REST backend for dashboard
- **JSON Storage** - Persistent incident storage

---

## Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to repository
cd ocean4life

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
# Get API key from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Generate Demo Data

```bash
# Create sample posts for testing
python data_collectors/realtime_simulator.py
```

### 4. Run System

**Option A: Command-line processing**
```bash
python main.py
```

**Option B: Web dashboard**
```bash
python app.py
# Open http://127.0.0.1:5000 in browser
```

---

## Project Structure

```
ocean4life/
├── app.py                          # Flask web dashboard
├── main.py                         # CLI main runner
├── real_news_disaster_search.py    # News aggregation + AI enhancement
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template (safe)
├── .env                            # Local config (ignored by git)
├── .gitignore                      # Git ignore rules
│
├── config/                         # Configuration & taxonomy
│   ├── __init__.py
│   └── hazard_taxonomy.py         # Ocean hazard type definitions
│
├── agents/                         # AI processing agents
│   ├── extract_agent.py           # LLM extraction (Groq)
│   └── dedupe_agent.py            # Deduplication + cross-reference
│
├── models/                         # Data models
│   └── schema.py                  # Pydantic models for Need, UniqueIncident
│
├── data_collectors/               # Data generation & collection
│   ├── __init__.py
│   └── realtime_simulator.py      # Demo data generator
│
├── data/                          # Input data
│   ├── sample_posts.txt           # Sample disaster reports
│   └── demo_ocean_incidents.json  # DEMO: Sample ocean hazards
│
├── outputs/                       # Results
│   ├── verified_incidents.json    # Deduplicated + verified incidents
│   ├── mumbai_realtime.json       # City-specific results
│   └── delhi_realtime.json        # City-specific results
│
├── templates/                     # Web interface
│   └── index.html                 # Dashboard (Leaflet map, dark/light theme)
│
└── README.md                      # This file
```

---

## Technologies

### Core

- **Flask** - Web framework
- **Python 3.8+** - Language

### AI & NLP

- **Groq API** - LLM inference (Llama 3.3 70B)
- **sentence-transformers** - Text embeddings
- **scikit-learn** - Clustering (DBSCAN)

### Data & Geocoding

- **BeautifulSoup4** - Web scraping
- **requests** - HTTP library
- **geopy** - Geocoding (Nominatim)
- **pydantic** - Data validation

### Frontend

- **Leaflet.js** - Interactive maps
- **HTML5/CSS3/JavaScript** - UI

---

## Key Features

### 🔍 Real-Time Extraction

```
Raw Report → LLM Analysis → Structured JSON
```

Example:
```
Input: "URGENT: Coastal flooding in Mumbai due to heavy rains!"
Output: {
  "hazard_type": "COASTAL_FLOODING",
  "location": "Mumbai",
  "urgency": 5,
  "severity": "HIGH"
}
```

### 🧲 Semantic Deduplication

Eliminates duplicate reports using DBSCAN clustering on TF-IDF embeddings.

```
Raw Reports: 10
Unique Incidents: 3
Deduplication Rate: 70%
```

### 🔗 Cross-Reference Verification

Combines evidence from multiple sources:

```
Confidence = (Report Count Score) + (Source Diversity) + (Urgency Consensus)
```

### 🗺️ Interactive Dashboard

- Dark/light theme toggle
- Real-time map visualization
- Incident details panel
- Source attribution
- Confidence score display

---

## Ocean Hazard Types (Taxonomy)

The system now recognizes:

| Hazard Type | Description |
|---|---|
| `COASTAL_FLOODING` | Temporary inundation of coastal areas |
| `STORM_SURGE` | Rapid water level rise during cyclones |
| `CYCLONE` | Tropical cyclonic systems with strong winds |
| `TSUNAMI` | Large waves from underwater earthquakes |
| `HIGH_WAVES` | Unusually high ocean waves |
| `COASTAL_EROSION` | Loss of land mass along coast |
| `OIL_SPILL` | Petroleum release into marine environment |
| `MARINE_POLLUTION` | Chemical/waste contamination of waters |
| `DANGEROUS_CURRENT` | Strong ocean currents (rip tides, undertows) |
| `COASTAL_LANDSLIDE` | Slope failure along coastal areas |
| `STORM` | Severe coastal weather events |
| `OTHER` | Other ocean hazards |
| `NOT_RELEVANT` | Non-hazard content |

See `config/hazard_taxonomy.py` for detailed definitions.

---

## Data Model

### Need (Report)

```python
{
  "need_type": "rescue",
  "location": "Mumbai",
  "urgency": 5,
  "summary": "Coastal flooding affecting residents",
  "source": "twitter",
  "timestamp": "2026-01-15T10:30:00Z",
  "hazard_type": "COASTAL_FLOODING",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "source_type": "social_media"
}
```

### UniqueIncident (Verified)

```python
{
  "incident_id": "INC_ABC123",
  "hazard_type": "COASTAL_FLOODING",
  "severity": "HIGH",
  "location": "Mumbai",
  "urgency": 5,
  "summary": "Coastal flooding in Worli area",
  "report_count": 4,
  "sources": ["twitter", "news", "citizen_report", "news"],
  "confidence_score": 0.87,
  "ai_confidence": 0.89,
  "status": "PENDING",
  "evidence": ["flooding", "water level", "coastal"]
}
```

---

## Security

### Credentials Management

- ✅ **No hardcoded secrets** in source code
- ✅ **Environment variables only** - Uses `.env` file (not committed)
- ✅ `.env.example` provided with safe placeholder values
- ✅ All API keys configured via environment at runtime

### Best Practices

```python
# ✅ CORRECT
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ❌ NEVER DO THIS
GROQ_API_KEY = "gsk_ABC123xyz..."  # Don't hardcode!
```

### .gitignore Rules

```
.env
*.env
key.env
__pycache__/
*.pyc
venv/
.venv/
```

---

## Demo Data

The file `data/demo_ocean_incidents.json` contains **DEMO DATA ONLY** for testing purposes.

**⚠️ WARNING**: This data is synthetic and should never be treated as real-time hazard information. It demonstrates:

- Coastal Flooding incident
- Storm Surge incident  
- High Waves incident
- Coastal Erosion incident
- Marine Pollution incident

All locations, timestamps, and details are examples for system testing.

---

## Planned Features (Phase 2+)

The following features are planned for future phases:

### Phase 2: Enhanced Hazard Detection

- ⏳ Citizen hazard reporting (web form + mobile-friendly)
- ⏳ Ocean-specific classification model
- ⏳ Satellite image analysis for coastal features
- ⏳ Real-time social media monitoring (Twitter, Reddit, etc.)
- ⏳ Advanced AI confidence scoring

### Phase 3: Response & Alerts

- ⏳ Automated alert generation
- ⏳ Authority dashboard for responders
- ⏳ Email/SMS notifications
- ⏳ Real-time map hotspots
- ⏳ Integration with emergency services APIs

### Phase 4: Intelligence & Prediction

- ⏳ Offline synchronization
- ⏳ Satellite integration (NOAA, Sentinel-2)
- ⏳ IoT sensor integration (buoys, weather stations)
- ⏳ Predictive models (forecasting)
- ⏳ Mobile application (iOS/Android)

### Not Planned for This Phase

- Computer vision/image classification
- Video analysis
- Complex ML model training
- IoT integration
- Mobile apps
- Email/SMS system
- Authentication/user management

---

## System Architecture

### Data Flow

```
Citizen / Social Media / News
         ↓
    Report Collection (scraping, APIs, user input)
         ↓
     LLM Extraction (Groq - structured JSON)
         ↓
   Semantic Deduplication (DBSCAN clustering)
         ↓
     Cross-Reference Verification (multi-source)
         ↓
    Confidence Scoring (evidence-based)
         ↓
        Geocoding (Nominatim)
         ↓
      JSON Storage
         ↓
     Dashboard / Map (Leaflet)
```

### Component Interaction

```
[Flask App] ←→ [RealNewsDisasterSearch]
                 ├→ [extract_agent.py] ←→ Groq API
                 ├→ [dedupe_agent.py]
                 └→ [geopy.geocoders]

[CLI main.py] ←→ Same agent pipeline

[Templates/index.html] ←→ Leaflet map + JSON data
```

---

## Configuration

Edit `.env` to configure:

```bash
# Groq LLM API key (required for AI extraction)
GROQ_API_KEY=your_key_here
```

### Similarity Threshold

In `agents/dedupe_agent.py`:

```python
dedupe_agent = DeduplicationAgent(similarity_threshold=0.75)
# 0.75 = 75% text similarity required to be considered duplicate
# Lower = more aggressive deduplication
# Higher = fewer false positives but more duplicate incidents
```

---

## Testing

### Manual Testing

1. Start web dashboard:
   ```bash
   python app.py
   ```

2. Open http://127.0.0.1:5000

3. Try these cities (coastal for ocean testing):
   - Mumbai
   - Chennai
   - Goa

4. Try analyzing a news URL

---

## Troubleshooting

### "No module named 'groq'"

```bash
pip install groq
```

### "GROQ_API_KEY not set"

Ensure `.env` file has valid API key:

```bash
cat .env
# Should show: GROQ_API_KEY=gsk_...
```

---

## License

[To be added]

---

## Acknowledgments

- Built on Disaster Relief Agent framework
- Powered by Groq API (Llama 3.3 70B)
- Maps by Leaflet.js
- Geocoding by Nominatim/OpenStreetMap

---

**Last Updated**: January 15, 2026  
**Phase**: 1 (Foundation)  
**Status**: Active Development