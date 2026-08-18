"""
OceanShield AI - Severity Assessment Service

Estimates the severity of ocean hazards based on available evidence.
Severity levels: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
"""

from models.ocean_models import OceanReport, OceanIncident
from typing import List, Tuple


def assess_severity(
    hazard_type: str,
    description: str,
    evidence: List[str],
    report_count: int = 1
) -> Tuple[str, List[str]]:
    """
    Assess severity of an ocean hazard based on available evidence.
    
    Returns:
        (severity_level, reasoning)
        severity_level: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
        reasoning: List of factors that influenced the assessment
    """
    
    reasoning = []
    score = 0  # Start with base score
    
    # 1. Hazard type inherent severity
    inherent_severity = {
        "TSUNAMI": 5,
        "CYCLONE": 4.5,
        "STORM_SURGE": 4.5,
        "STORM": 3.5,
        "HIGH_WAVES": 3,
        "COASTAL_FLOODING": 3.5,
        "OIL_SPILL": 4,
        "MARINE_POLLUTION": 3,
        "COASTAL_EROSION": 2.5,
        "COASTAL_LANDSLIDE": 3.5,
        "DANGEROUS_CURRENT": 2.5,
        "OTHER": 2,
        "NOT_RELEVANT": 0,
    }
    
    score = inherent_severity.get(hazard_type, 2)
    reasoning.append(f"Hazard type '{hazard_type}' base severity: {score}/5")
    
    # 2. Evidence severity indicators
    critical_words = ["urgent", "emergency", "critical", "life-threatening", "danger", 
                      "immediate", "evacuate", "severe", "major", "deaths", "injured"]
    high_words = ["serious", "significant", "major", "affecting", "impact", "damage", 
                  "affected", "injured", "rescue"]
    
    evidence_text = " ".join(evidence).lower() + " " + description.lower()
    
    if any(word in evidence_text for word in critical_words):
        score = max(score, 4.5)
        reasoning.append("Critical severity keywords detected")
    elif any(word in evidence_text for word in high_words):
        score = max(score, 3.5)
        reasoning.append("High severity keywords detected")
    
    # 3. Infrastructure/people indicators
    infra_words = ["road", "bridge", "building", "structure", "infrastructure", "port"]
    people_words = ["people", "residents", "citizens", "families", "children", "injured", "death"]
    
    if any(word in evidence_text for word in infra_words):
        score += 0.5
        reasoning.append("Infrastructure affected")
    
    if any(word in evidence_text for word in people_words):
        score += 0.7
        reasoning.append("People/casualties mentioned")
    
    # 4. Multiple reports increase severity
    if report_count > 1:
        score += (report_count - 1) * 0.3
        reasoning.append(f"Multiple reports corroborate ({report_count} reports)")
    
    # 5. Location specificity
    if "," in description or any(city in description for city in 
                                   ["Mumbai", "Chennai", "Goa", "Delhi", "Kolkata"]):
        score += 0.2
        reasoning.append("Specific location mentioned")
    
    # Normalize score to 0-5 range
    score = max(0, min(5, score))
    
    # Map score to severity level
    if score < 1:
        severity = "MINIMAL"
    elif score < 2:
        severity = "LOW"
    elif score < 3:
        severity = "MODERATE"
    elif score < 4:
        severity = "HIGH"
    else:
        severity = "CRITICAL"
    
    reasoning.append(f"Final severity assessment: {severity} (score: {score:.1f}/5)")
    
    return severity, reasoning


def assess_incident_severity(incident: OceanIncident) -> Tuple[str, List[str]]:
    """
    Assess severity for a clustered incident.
    Takes into account all reports in the incident.
    """
    
    # Aggregate evidence from all reports
    all_evidence = []
    combined_description = ""
    
    for report in incident.reports:
        all_evidence.extend(report.description.split())
        combined_description += " " + report.description
    
    return assess_severity(
        incident.hazard_type,
        combined_description,
        all_evidence,
        len(incident.reports)
    )
