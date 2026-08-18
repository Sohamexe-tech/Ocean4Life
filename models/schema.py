from pydantic import BaseModel
from typing import List, Optional


class Need(BaseModel):
    """Represents a single report/need from any source (news, social media, etc.)"""
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    source: str
    timestamp: str
    # Ocean-hazard specific fields (optional, for future enhancement)
    hazard_type: Optional[str] = None  # e.g., COASTAL_FLOODING, STORM_SURGE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_type: Optional[str] = None  # e.g., news, social_media, citizen_report


class UniqueIncident(BaseModel):
    """Represents a deduplicated, cross-referenced incident"""
    incident_id: str
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    report_count: int = 1
    sources: List[str] = []
    original_reports: List[Need] = []
    confidence_score: float = 0.0
    # Ocean-hazard specific fields (optional, for future enhancement)
    hazard_type: Optional[str] = None  # e.g., COASTAL_FLOODING
    severity: Optional[str] = None  # e.g., CRITICAL, HIGH, MODERATE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ai_confidence: Optional[float] = None  # AI-generated confidence score
    evidence: List[str] = []  # Supporting evidence/keywords from reports
    status: Optional[str] = "PENDING"  # e.g., PENDING, VERIFIED, RESOLVED