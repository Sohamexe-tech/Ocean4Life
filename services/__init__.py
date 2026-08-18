# OceanShield AI - Services Package
# Core processing services for hazard analysis

from .classifier import classify_hazard, safe_classify, keyword_based_classification
from .severity_assessor import assess_severity, assess_incident_severity
from .credibility_scorer import CredibilityScorer, score_report, score_incident

__all__ = [
    "classify_hazard",
    "safe_classify",
    "keyword_based_classification",
    "assess_severity",
    "assess_incident_severity",
    "CredibilityScorer",
    "score_report",
    "score_incident",
]
