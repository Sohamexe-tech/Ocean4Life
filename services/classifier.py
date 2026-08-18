"""
OceanShield AI - Hazard Classification Service

Uses Groq LLM to classify ocean hazard reports into structured categories.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from config import OCEAN_HAZARD_TYPES

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

OCEAN_HAZARD_CLASSIFICATION_PROMPT = """You are an AI system that classifies ocean and coastal hazard reports.

Analyze the report and classify it into ONE of these hazard types:

COASTAL_FLOODING - Temporary inundation of coastal areas
STORM_SURGE - Rapid water level rise during cyclones
CYCLONE - Tropical cyclonic systems with strong winds
TSUNAMI - Large waves from earthquakes
HIGH_WAVES - Unusually high ocean waves
COASTAL_EROSION - Loss of land mass along coast
OIL_SPILL - Petroleum release
MARINE_POLLUTION - Chemical/waste contamination
DANGEROUS_CURRENT - Rip tides, undertows
COASTAL_LANDSLIDE - Slope failure
STORM - Severe coastal weather
OTHER - Other ocean hazards
NOT_RELEVANT - Not about ocean hazards

Return ONLY valid JSON. No extra text.

{
  "hazard_type": "COASTAL_FLOODING",
  "confidence": 0.95,
  "severity": "HIGH",
  "location": "extracted location or null",
  "evidence": ["keyword1", "keyword2"]
}

Severity should be one of: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
"""


def classify_hazard(description: str, location: str = None) -> dict:
    """
    Classify an ocean hazard report using Groq LLM.
    
    Returns:
        dict with keys: hazard_type, confidence, severity, location, evidence
        or empty dict on failure
    """
    if not client:
        return {"error": "GROQ_API_KEY not configured"}
    
    try:
        user_message = f"Report: {description}"
        if location:
            user_message += f"\nLocation: {location}"
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": OCEAN_HAZARD_CLASSIFICATION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,  # Deterministic
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start == -1 or end == 0:
            return {"error": "No valid JSON in response"}
        
        data = json.loads(content[start:end])
        
        # Validate hazard type
        hazard_type = data.get("hazard_type", "OTHER")
        if hazard_type not in OCEAN_HAZARD_TYPES:
            hazard_type = "OTHER"
        
        # Validate confidence (0-1)
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        
        # Validate severity
        severity = data.get("severity", "MODERATE")
        if severity not in ["MINIMAL", "LOW", "MODERATE", "HIGH", "CRITICAL"]:
            severity = "MODERATE"
        
        return {
            "hazard_type": hazard_type,
            "confidence": confidence,
            "severity": severity,
            "location": data.get("location"),
            "evidence": data.get("evidence", [])
        }
    
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from LLM"}
    except Exception as e:
        return {"error": f"Classification failed: {str(e)}"}


def safe_classify(description: str, location: str = None) -> dict:
    """
    Safely classify a hazard with fallback to keyword-based classification.
    
    Always returns a valid classification dict.
    """
    result = classify_hazard(description, location)
    
    if "error" in result:
        # Fallback to keyword-based classification
        return keyword_based_classification(description, location)
    
    return result


def keyword_based_classification(description: str, location: str = None) -> dict:
    """
    Fallback keyword-based classification when LLM is unavailable.
    """
    text = description.lower()
    
    # Keyword mapping to hazard types
    keywords = {
        "COASTAL_FLOODING": ["flood", "water", "inundated", "submerged", "water level", "high tide"],
        "STORM_SURGE": ["surge", "cyclone", "hurricane", "typhoon", "tropical storm"],
        "CYCLONE": ["cyclone", "hurricane", "typhoon", "wind", "storm system"],
        "TSUNAMI": ["tsunami", "earthquake", "seismic", "wave", "tidal"],
        "HIGH_WAVES": ["waves", "rough sea", "swell", "dangerous waves", "wave action"],
        "COASTAL_EROSION": ["erosion", "landslide", "cliff", "land loss", "collapse"],
        "OIL_SPILL": ["oil spill", "petroleum", "slick", "crude"],
        "MARINE_POLLUTION": ["pollution", "contamination", "waste", "toxic", "chemical"],
        "DANGEROUS_CURRENT": ["current", "rip tide", "undertow", "water current"],
        "COASTAL_LANDSLIDE": ["landslide", "mudslide", "slide", "slip"],
        "STORM": ["storm", "weather", "severe", "heavy rain", "wind"],
    }
    
    # Find matching hazard type
    for hazard_type, keywords_list in keywords.items():
        if any(kw in text for kw in keywords_list):
            # Determine severity from keywords
            severity_keywords = {
                "CRITICAL": ["urgent", "emergency", "critical", "danger", "life-threatening"],
                "HIGH": ["serious", "major", "severe", "emergency"],
                "MODERATE": ["significant", "notable", "affecting"],
                "LOW": ["minor", "small", "slight"],
            }
            
            severity = "MODERATE"
            for sev, sev_kws in severity_keywords.items():
                if any(kw in text for kw in sev_kws):
                    severity = sev
                    break
            
            return {
                "hazard_type": hazard_type,
                "confidence": 0.6,  # Lower confidence for keyword-based
                "severity": severity,
                "location": location,
                "evidence": [kw for kw in keywords_list if kw in text]
            }
    
    # Default to OTHER
    return {
        "hazard_type": "OTHER",
        "confidence": 0.3,
        "severity": "MODERATE",
        "location": location,
        "evidence": []
    }
