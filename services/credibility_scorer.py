"""
OceanShield AI - Credibility Scoring Service

Computes AI credibility score (0-100) for ocean hazard reports and incidents.

Credibility Formula (0-100 scale):
- Source reliability: 20%
- Cross-source agreement: 20%
- Evidence strength: 20%
- Location consistency: 15%
- Temporal consistency: 10%
- Semantic similarity/corroboration: 10%
- AI extraction confidence: 5%
"""

from models.ocean_models import OceanReport, OceanIncident
from typing import List, Dict, Tuple


class CredibilityScorer:
    """Compute credibility scores with transparent reasoning."""
    
    # Source reliability weights (0-100)
    SOURCE_RELIABILITY = {
        "official_alert": 95,
        "news": 80,
        "social_media": 60,
        "citizen_report": 65,
        "google_news": 85,
        "twitter": 55,
        "facebook": 58,
        "whatsapp": 50,
        "reddit": 65,
        "instagram": 45,
        "unknown": 50,
    }
    
    def __init__(self):
        self.weights = {
            "source_reliability": 0.20,
            "cross_source_agreement": 0.20,
            "evidence_strength": 0.20,
            "location_consistency": 0.15,
            "temporal_consistency": 0.10,
            "semantic_similarity": 0.10,
            "extraction_confidence": 0.05,
        }
    
    def score_report(self, report: OceanReport) -> Tuple[int, Dict]:
        """
        Score a single report's credibility (0-100).
        
        Returns:
            (score, factors_dict)
            score: 0-100 credibility score
            factors_dict: breakdown of how score was computed
        """
        
        factors = {}
        
        # 1. Source Reliability (0-100)
        source_rel = self.SOURCE_RELIABILITY.get(report.source, 50)
        factors["source_reliability"] = source_rel
        
        # 2. Evidence Strength
        # Based on description length, detail, and specificity
        evidence_strength = self._compute_evidence_strength(report)
        factors["evidence_strength"] = evidence_strength
        
        # 3. Extraction Confidence (from LLM)
        extraction_conf = int((report.hazard_confidence or 0.5) * 100)
        factors["extraction_confidence"] = extraction_conf
        
        # 4. Location Consistency (how well location was specified)
        location_consistency = self._compute_location_consistency(report)
        factors["location_consistency"] = location_consistency
        
        # 5. Temporal Consistency (report timing)
        # For single reports, assume recent = more credible
        temporal = 80  # Assume reports are recent
        factors["temporal_consistency"] = temporal
        
        # For now, these are unavailable for single reports:
        factors["cross_source_agreement"] = 50  # Will use in incident-level scoring
        factors["semantic_similarity"] = 50  # Will use in incident-level scoring
        
        # Compute weighted score
        score = (
            source_rel * self.weights["source_reliability"] +
            evidence_strength * self.weights["evidence_strength"] +
            extraction_conf * self.weights["extraction_confidence"] +
            location_consistency * self.weights["location_consistency"] +
            temporal * self.weights["temporal_consistency"]
        ) / (
            self.weights["source_reliability"] +
            self.weights["evidence_strength"] +
            self.weights["extraction_confidence"] +
            self.weights["location_consistency"] +
            self.weights["temporal_consistency"]
        )
        
        score = int(max(0, min(100, score)))
        
        return score, factors
    
    def score_incident(self, incident: OceanIncident) -> Tuple[int, Dict, str]:
        """
        Score an incident's credibility (0-100).
        Takes into account all reports and corroboration.
        
        Returns:
            (score, factors_dict, level)
            level: LOW (0-39), MODERATE (40-59), HIGH (60-79), VERY_HIGH (80-100)
        """
        
        factors = {}
        
        if not incident.reports:
            return 50, {"error": "No reports"}, "MODERATE"
        
        # 1. Source Reliability (average of all reports)
        source_scores = [
            self.SOURCE_RELIABILITY.get(r.source, 50)
            for r in incident.reports
        ]
        avg_source_rel = sum(source_scores) / len(source_scores)
        factors["source_reliability"] = int(avg_source_rel)
        
        # 2. Cross-source Agreement
        # More sources = higher agreement score
        unique_sources = len(set(r.source for r in incident.reports))
        cross_source = min(100, 40 + (unique_sources * 15))  # 40-100 based on sources
        factors["cross_source_agreement"] = int(cross_source)
        
        # 3. Report Count (corroboration)
        report_count_score = min(100, 50 + (incident.report_count * 10))
        factors["report_count_corroboration"] = int(report_count_score)
        
        # 4. Evidence Strength (aggregate)
        evidence_scores = [
            self._compute_evidence_strength(r)
            for r in incident.reports
        ]
        avg_evidence = sum(evidence_scores) / len(evidence_scores)
        factors["evidence_strength"] = int(avg_evidence)
        
        # 5. Location Consistency (all reports have similar location?)
        location_consistency = self._compute_location_cluster_consistency(incident)
        factors["location_consistency"] = int(location_consistency)
        
        # 6. Extraction Confidence (average)
        conf_scores = [
            int((r.hazard_confidence or 0.5) * 100)
            for r in incident.reports
        ]
        avg_extraction = sum(conf_scores) / len(conf_scores)
        factors["extraction_confidence"] = int(avg_extraction)
        
        # 7. Temporal Consistency
        temporal = 80
        factors["temporal_consistency"] = temporal
        
        # 8. Semantic Similarity
        # If many reports clustered together, similarity is high
        semantic_sim = min(100, 60 + (incident.report_count * 5))
        factors["semantic_similarity"] = int(semantic_sim)
        
        # Compute weighted score
        score = (
            avg_source_rel * self.weights["source_reliability"] +
            cross_source * self.weights["cross_source_agreement"] +
            avg_evidence * self.weights["evidence_strength"] +
            location_consistency * self.weights["location_consistency"] +
            temporal * self.weights["temporal_consistency"] +
            semantic_sim * self.weights["semantic_similarity"] +
            avg_extraction * self.weights["extraction_confidence"]
        )
        
        score = int(max(0, min(100, score)))
        
        # Determine confidence level
        if score < 40:
            level = "LOW"
        elif score < 60:
            level = "MODERATE"
        elif score < 80:
            level = "HIGH"
        else:
            level = "VERY_HIGH"
        
        return score, factors, level
    
    def _compute_evidence_strength(self, report: OceanReport) -> int:
        """
        Compute evidence strength based on description quality and detail.
        Returns 0-100.
        """
        
        if not report.description:
            return 10
        
        score = 50  # Base
        desc = report.description.lower()
        
        # Length of description (more detail = stronger)
        if len(report.description) > 200:
            score += 25
        elif len(report.description) > 100:
            score += 15
        elif len(report.description) > 50:
            score += 5
        
        # Specific details increase strength
        detail_words = ["water", "damage", "affected", "location", "area", "time",
                       "people", "structure", "road", "flooded", "wave", "current"]
        detail_count = sum(1 for word in detail_words if word in desc)
        score += min(25, detail_count * 2)
        
        return min(100, score)
    
    def _compute_location_consistency(self, report: OceanReport) -> int:
        """
        Compute how well location was specified.
        Returns 0-100.
        """
        
        if not report.location:
            return 30
        
        score = 50
        
        # User-provided coordinates = high consistency
        if report.latitude and report.longitude:
            if report.location_type == "USER_PROVIDED":
                score = 95
            elif report.location_type == "GEOCODED":
                score = 85
            else:
                score = 70
        
        # Specific named location
        if "," in report.location or len(report.location.split()) >= 2:
            score = max(score, 75)
        
        return min(100, score)
    
    def _compute_location_cluster_consistency(self, incident: OceanIncident) -> int:
        """
        Compute how consistent locations are across all reports in an incident.
        Returns 0-100.
        """
        
        if not incident.reports or not incident.latitude or not incident.longitude:
            return 60
        
        # If all reports have coordinates and are clustered together
        # (same incident), assume high consistency
        # This is verified by the deduplication process
        
        has_coords = sum(1 for r in incident.reports if r.latitude and r.longitude)
        if has_coords == len(incident.reports):
            return 90  # All have coordinates
        elif has_coords > 0:
            return 75  # Some have coordinates
        else:
            return 60  # No coordinates


def score_report(report: OceanReport) -> int:
    """Quick function to score a single report."""
    scorer = CredibilityScorer()
    score, _ = scorer.score_report(report)
    return score


def score_incident(incident: OceanIncident) -> Tuple[int, str]:
    """Quick function to score an incident."""
    scorer = CredibilityScorer()
    score, _, level = scorer.score_incident(incident)
    return score, level
