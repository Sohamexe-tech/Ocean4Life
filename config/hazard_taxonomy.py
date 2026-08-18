# OceanShield AI - Ocean Hazard Taxonomy
# Defines supported ocean and coastal hazard types

OCEAN_HAZARD_TYPES = {
    "COASTAL_FLOODING": {
        "label": "Coastal Flooding",
        "description": "Temporary inundation of normally dry areas due to high tides, storm surge, or heavy rainfall",
        "severity_indicators": ["water level", "flood", "inundated", "submerged"],
    },
    "STORM_SURGE": {
        "label": "Storm Surge",
        "description": "Rapid rise in water level during cyclones or severe storms",
        "severity_indicators": ["surge", "cyclone", "storm", "hurricane", "typhoon"],
    },
    "CYCLONE": {
        "label": "Cyclone/Hurricane/Typhoon",
        "description": "Intense tropical cyclonic systems with strong winds and heavy rainfall",
        "severity_indicators": ["cyclone", "hurricane", "typhoon", "winds"],
    },
    "TSUNAMI": {
        "label": "Tsunami",
        "description": "Large ocean waves caused by underwater earthquakes or subsea landslides",
        "severity_indicators": ["tsunami", "earthquake", "wave", "ocean waves"],
    },
    "HIGH_WAVES": {
        "label": "High Waves/Rough Seas",
        "description": "Unusually high ocean waves due to strong winds or storms",
        "severity_indicators": ["high waves", "rough seas", "strong waves", "dangerous waves"],
    },
    "COASTAL_EROSION": {
        "label": "Coastal Erosion",
        "description": "Loss of land mass along coastal areas due to wave action and weathering",
        "severity_indicators": ["erosion", "landslide", "land loss", "cliff collapse"],
    },
    "OIL_SPILL": {
        "label": "Oil Spill",
        "description": "Release of petroleum into marine environment causing ecological damage",
        "severity_indicators": ["oil spill", "petroleum", "slick", "contamination"],
    },
    "MARINE_POLLUTION": {
        "label": "Marine Pollution",
        "description": "Contamination of marine waters from industrial waste, plastic, or chemical spills",
        "severity_indicators": ["pollution", "contamination", "waste", "toxic", "chemical spill"],
    },
    "DANGEROUS_CURRENT": {
        "label": "Dangerous Current/Rip Tide",
        "description": "Strong ocean currents that pose risk to swimmers and vessels",
        "severity_indicators": ["current", "rip tide", "undertow", "strong current"],
    },
    "COASTAL_LANDSLIDE": {
        "label": "Coastal Landslide",
        "description": "Sudden movement of earth/rock material on coastal slopes",
        "severity_indicators": ["landslide", "mudslide", "collapse", "slip"],
    },
    "STORM": {
        "label": "Coastal Storm",
        "description": "Severe weather event with strong winds and heavy precipitation affecting coastal areas",
        "severity_indicators": ["storm", "winds", "severe weather", "heavy rain"],
    },
    "OTHER": {
        "label": "Other Ocean Hazard",
        "description": "Other ocean or coastal hazards not covered by specific categories",
        "severity_indicators": [],
    },
    "NOT_RELEVANT": {
        "label": "Not Relevant",
        "description": "Content not related to ocean or coastal hazards",
        "severity_indicators": [],
    },
}

# Severity levels
SEVERITY_LEVELS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MODERATE": 3,
    "LOW": 2,
    "MINIMAL": 1,
}

def get_hazard_type(hazard_key):
    """Get hazard type details by key"""
    return OCEAN_HAZARD_TYPES.get(hazard_key, OCEAN_HAZARD_TYPES["NOT_RELEVANT"])

def get_all_hazard_types():
    """Get list of all hazard types"""
    return list(OCEAN_HAZARD_TYPES.keys())

def get_hazard_label(hazard_key):
    """Get human-readable label for a hazard type"""
    return OCEAN_HAZARD_TYPES.get(hazard_key, {}).get("label", hazard_key)
